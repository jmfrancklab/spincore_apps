import serial
from serial.tools.list_ports import comports
from serial import SerialException
from pyspecdata import strm
import re

import logging
logger = logging.getLogger('Base Serial Class')

port_dict = {}

class SerialInstrument (object):
    """Class to describe an instrument connected using pyserial.
    Provides initialization (:func:`__init__`) to start the connection,
    as well as :func:`write` :func:`read` and :func:`respond` functions.
    Can be used inside a with block.
    """
    def __init__(self,textidn, **kwargs):
        """Initialize a serial connection based on the identifier string
        `textidn`, and assign it to the `connection` attribute

        Parameters
        ==========

        textidn : str
            
            A string used to identify the instrument.
            Specifically, the instrument responds to the ``*idn?`` command
            with a string that includes ``textidn``.
            If textidn is set to None, just show the available instruments.
        """
        self._textidn = textidn
        if textidn is None:
            self.show_instruments()
        else:
            self.connection = serial.Serial(self.id_instrument(textidn), **kwargs)
            assert self.connection.isOpen(), "For some reason, I couldn't open the connection!"
            logger.debug('opened serial connection, and set to connection attribute')
        return
    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.connection.close()
        return
    def write(self,*args):
        """Send info to the instrument.  Take a comma-separated list of
        arguments, which are converted to strings and separated by a space.
        (Similar to a print command, but directed at the instrument)"""
        text = ' '.join([str(j) for j in args])
        logger.debug(strm("when trying to write, port looks like this:",self.connection))
        self.connection.write(text+'\n')
        return
    def read(self, *args, **kwargs):
        return self.connection.read(*args, **kwargs)
    def flush(self, timeout=1):
        """Flush the input (say we didn't read all of it, *etc.*)
        
        Note that there are routines called "flush" in serial, but these
        seem to not be useful.
        """
        old_timeout = self.connection.timeout
        self.connection.timeout = timeout
        result = 'blah'
        while len(result)>0:
            result = self.connection.read(2000)
        self.connection.timeout = old_timeout
        return
    def respond(self,*args, **kwargs):
        """Same a write, but also sets the timeout to infinite and returns the result.
        
        Parameters
        ----------
        message_len : int

            If present, read a message of a specified number of bytes.
            if not present, return a text line (readline).
        """
        message_len = None
        if 'message_len' in kwargs:
            message_len = kwargs.pop('message_len')
        self.write(*args)
        old_timeout = self.connection.timeout
        if message_len is None:
            self.connection.timeout = 5
            retval = self.connection.readline()
        else:
            retval = self.connection.read(message_len)
        self.connection.timeout = old_timeout
        return retval
    def show_instruments(self):
        """For testing.  Same as :func:`id_instrument`, except that it just prints the idn result from all com ports.
        """
        for j in comports():
            port_id = j[0] # based on the previous, this is the port number
            try:
                with serial.Serial(port_id) as s:
                    s.timeout = 0.1
                    assert s.isOpen(), "For some reason, I couldn't open the connection for %s!"%str(port_id)
                    s.write('*idn?\n')
                    result = s.readline()
                    print result
            except SerialException:
                pass
    # {{{ common commands
    def demand(self, cmd, value, tries=200, error=1e-2):
        """Demand that the result of cmd contains `value`.
        Keep trying until the instrument is ready to respond, and then flush
        the buffer.
        (Set to a relatively short timeout, and keep sending the command over
        and over.)

        Parameters
        ----------
        cmd : str
            The command to issue.
        value : str or float or int
            :if str:
                A regular expression that should match to the command
            :if a number:
                When I convert the response to a number, the number matches to
                within `error` (relative error).
        """
        old_timeout = self.connection.timeout
        self.connection.timeout = 0.1
        response = None
        j = 0
        while response is None or len(response) == 0 and j<tries:
            j += 1
            self.write(cmd) # to make sure it's done resetting
            response = self.connection.readline()
        if type(value) is str:
            m = re.match(value,response)
            if not m:
                raise RuntimeError(strm("I got a reponse (",response,") from", cmd,
                    "but it doesn't match the regular expression'"+value+
                    "'"))
            self.flush(timeout=0.1)
            self.connection.timeout = old_timeout
            self.flush()
            return response
        else:
            try:
                response = float(response)
            except ValueError:
                raise ValueError("I got a response that I couln't convert to a floating point number:\n\t"+response)
            if abs((value - response)/response) < error:
                self.flush()
                return response
            else:
                raise RuntimeError(strm("I got a reponse (",response,") from", cmd,
                    "but it doesn't match the the value of",value))
    def check_idn(self, tries=200):
        """Check IDN and wait a while for a reponse.  This is a bit of a hack,
        used to make sure the instrument is ready, and can be called at the end
        of any commands that take a while to execute.  It also executes a flush
        at the end, to make sure that there's nothing stuck in the buffer."""
        old_timeout = self.connection.timeout
        self.connection.timeout = 0.1
        response = None
        j = 0
        while response is None or len(response) == 0 and j<tries:
            j += 1
            self.write('*IDN?') # to make sure it's done resetting
            response = self.connection.readline()
        assert self._textidn in response
        self.flush(timeout=0.1)
        self.connection.timeout = old_timeout
        return response
    def reset(self):
        self.write('*RST')
        self.check_idn() # wait until it's done
        return
    def save(self,fileno=1):
        """Save current setup to setup file number ``fileno``
        
        Parameters
        ----------

        fileno : int

            A number of the file -- typically between 1 and 20.
        """
        self.write('*SAV %d'%fileno)
    def recall(self,fileno=1):
        """Recall a set of panel settings that were previously saved:
            
        see :func:`save`
        """
        self.write('*RCL %d'%fileno)
        return
    def learn(self):
        "Returns the settings as a data string."
        return self.respond('*LRN?')
    # }}}
    def id_instrument(self,textidn):
        """A helper function for :func:`init` Identify the instrument that returns an ID string containing ``textidn``

            Here, I search through the comports in order to identify the
            instrument that I'm interested in.  This (or something like this)
            should work on either Windows or Mac/Linux.
        """
        if len(port_dict) == 0:
            print "port dict has no results, so searching for instruments"
            for j in comports():
                port_id = j[0] # based on the previous, this is the port number
                try:
                    with serial.Serial(port_id) as s:
                        s.timeout = 0.1
                        assert s.isOpen(), "For some reason, I couldn't open the connection for %s!"%str(port_id)
                        s.write('*idn?\n')
                        result = s.readline()
                        port_dict[port_id] = result
                except SerialException:
                    pass # on windows this is triggered if the port is already open
        for port_id, result in port_dict.iteritems():
            if textidn in result:
                return port_id
        print "I looped through all the com ports and didn't find ",textidn,"resetting port_dict, and trying again"
        for j in port_dict.keys():
            port_dict.pop(j)
        return self.id_instrument(textidn)
