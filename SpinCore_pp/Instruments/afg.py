from pylab import *
from pyspecdata import nddata,strm
from .serial_instrument import SerialInstrument

import logging
logger = logging.getLogger('AFG Scope Class')

class AFG_Channel_Properties (object):
    """This class controls the channel properties (burst, output, etc.).
    
    By setting these up as properties, we allow tab completion, and for sensible manipulation of parameters.
    """
    def __init__(self,ch,afg):
        """initialize a new `AFG_Channel_Properties` class
        
        Properties
        ----------

        ch : int

            the AFG channel you are manipulating or learning about

        afg : AFG

            the AFG instance that initialized this
        """
        self.ch = ch
        self.afg = afg
        return
    def digital_ndarray(self, data, rate=50e6):
        """Take a numpy ndarray `data`, and set it up for AWG output
        Default rate set to 50 MHz
        """
        print("About to output the ndarray...")
        cmd = ['SOUR%d:DATA:DAC VOLATILE,'%self.ch]
        cmd += [self.afg.binary_block(data)]
        self.afg.write(*cmd)
        print("Initial ndArray frequency set to",rate/len(data))
        self.afg.write('SOUR%d:APPL:USER %+0.7E'%(self.ch, rate/len(data)))
        self.afg.check_idn()
        self.afg.write('SOUR%d:ARB:OUTP'%self.ch)
        self.afg.check_idn()
        #self.afg.write('SOUR%d:FUNC USER'%self.ch)
        self.freq = rate/len(data)
        self.afg.check_idn()
        return
    @property
    def freq(self):
        r"""The frequency (what this means depends on the current mode)

        For AWG, this corresponds to :math:`R/N` where :math:`R` is
        the rate at which samples are played out and :math:`N` is the
        number of points.
        """
        cmd = 'SOUR%d:FREQ?'%self.ch
        return float(self.afg.respond(cmd))
    @freq.setter
    def freq(self,f):
        cmd = 'SOUR%d:FREQ %+0.7E'%(self.ch, f)
        print("About to call:",cmd)
        self.afg.write(cmd)
        self.afg.demand('SOUR%d:FREQ?'%(self.ch), f)
        return
    @property
    def ampl(self):
        """The amplitude setting in VPP by default. 
        """
        cmd = 'SOUR%d:AMP?'%self.ch
        return float(self.afg.demand(cmd))
    @ampl.setter
    def ampl(self,amp):
        cmd = 'SOUR%d:AMP %+0.7E'%(self.ch, amp)
        print("About to call:",cmd)
        self.afg.write(cmd)
        self.afg.demand('SOUR%d:AMP?'%(self.ch), amp)
        return
    @property
    def burst(self):
        cmd = 'SOUR%d:BURS:STAT?'%self.ch
        return bool(int(self.afg.respond(cmd)))
    @burst.setter
    def burst(self,onoff):
        if onoff:
            self.afg.write('SOUR%d:BURS:STAT ON'%self.ch)
            self.afg.demand("SOUR%d:BURS:STAT?"%self.ch,1)
            cmd = 'SOUR%d:BURS:STAT?'%self.ch
            #print "burst is",bool(int(self.afg.respond(cmd)))
        else:
            self.afg.write('SOUR%d:BURS:STAT OFF'%self.ch)
            self.afg.demand("SOUR%d:BURS:STAT?"%self.ch,0)
        return
    @property
    def output(self):
        cmd = 'OUTP%d?'%self.ch
        return bool(int(self.afg.respond(cmd)))
    @output.setter
    def output(self,onoff):
        if onoff:
            self.afg.write('OUTP%d ON'%self.ch)
            self.afg.demand('OUTP%d?'%self.ch,1)
        else:
            self.afg.write('OUTP%d OFF'%self.ch)
            self.afg.demand('OUTP%d?'%self.ch,0)
        return
    @property
    def sweep(self):
        cmd = 'SOUR%d:SWE:STAT?'%self.ch
        return bool(int(self.afg.respond(cmd)))
    @sweep.setter
    def sweep(self,onoff):
        if onoff:
            self.afg.write('SOUR%d:SWE:STAT ON'%self.ch)
        else:
            self.afg.write('SOUR%d:SWE:STAT OFF'%self.ch)
        self.afg.check_idn()
        return
    
class AFG (SerialInstrument):
    """Class for the AFG-2225

    The CH1 and CH2 attribute allow access to channel-specific functions.
    
    `self[0]` will return self.CH1 and `self[1]` will return self.CH2
    """
    def __init__(self,model='2225'):
        super().__init__('AFG-'+model)
        logger.debug(strm("identify from within AFG",super(self.__class__,self).respond('*idn?')))
        logger.debug("I should have just opened the serial connection")
        return
    def __getitem__(self,arg):
        if arg == 0:
            return self.CH1
        if arg == 1:
            return self.CH2
        else:
            raise ValueError("There is no channel "+str(arg))
    def sin(self,ch=1,V=1,f=1e6):
        """Outputs a sine wave of a particular frequency

        Parameters
        ==========

        
        ch : int
            
            On which channel do you want to ouput the sine wave?

        f : double

            frequency of the sine wave in SI units
        """
        # {{{ loop through units, and find the right one
        # Note that it interprets mhz in any case as mHz
        unit_list = ['mHZ','HZ','KHZ']
        f_list = [1e-3,1.0,1e3]
        for j,thisunit in enumerate(unit_list):
            thisf = f_list[j]
            if f < thisf: break
            unit_chosen = thisunit
            f_chosen = thisf
        # }}}
        cmd = 'SOUR%d:APPL:SIN %0.3f%s,1,0'%(ch,f/f_chosen,unit_chosen)
        print(cmd)
        self.write(cmd)
        
        ###ALEC 2017-10-06
    def appl_squ(self,ch=1,f='15000KHZ'):
        """Outputs a square wave at specified frequency
        
        Parameters
        ==========
        
        ch : int
            Number to indicate channel that outputs square wave
            
        f : str
            Frequency of square wave as string including units in HZ
            with no spaces all caps. To specify MHz must enter as
            equivalent numebr in KHZ (15MHZ=15000KHZ).
        """
        self.write('SOUR%d:APPL:SQU %s'%(ch,f))
        levels = self.respond('SOUR%d:APPL:SQU?'%(ch))
        return levels
    
    def set_burst(self,per,ncyc=1,ch=1):
        """Outputs a burst of a previously identified waveform
            at time interval specified by per in seconds.
        
        Parameters
        ==========
        
        ncyc : int
            Burst cycle or burst count; the number of repeated cycles
            of the waveform per burst. range 1 to 65535.
            Condition: ncyc < (per*f)
            where f is frequenecy of previously identified waveform.
        per : int
            Time between start of one burst and start of the next burst.
            Units of seconds. Only for internal triggering. Range of 1ms
            to 500 s. per will adjust if ncyc is too large such that
            ncyc < (per*f) condition is met.
        """
        self.write('SOUR%d:BURS:NCYC %+0.4E'%(ch,ncyc))
        self.demand('SOUR%d:BURS:NCYC?'%ch, ncyc)
        self.write('SOUR%d:BURS:INT:PER %+0.4E'%(ch,per))
        self.demand('SOUR%d:BURS:INT:PER?'%ch, per)
        self.respond('SOUR%d:BURS:TRIG:SOUR?'%ch)
        self.respond('OUTP%d:TRIG?'%ch)
        return      
        ###ALEC 2017-10-06
        
    def binary_block(self,data):
        """Converts array `data` into a binary string of IEE488.2 format
        
        (data is sent as a 16 bit integer)"""
        assert all(abs(data)<1.1), "all data must have absolute value less than 1"
        data = int16(data*511).tostring()
        data_len = len(data)
        data_len = str(data_len)
        assert (len(data_len) < 10), "the number describing the data length must be less than ten digits long, but your data length is "+data_len
        initialization = b'#'+str(len(data_len)).encode('ascii')+data_len.encode('ascii')
        return initialization+data
    def set_sweep(self, start=3e3, stop=5e3, time=1, ch=1):
        assert time>=1e-3, "It seems like the AFG will only allow time values set to 1ms or higher"
        f_str = '%+0.4E'%start
        self.write('SOUR%d:FREQ:STAR %+0.4E'%(ch,start))
        self.demand('SOUR%d:FREQ:STAR?'%ch, start)
        self.write('SOUR%d:FREQ:STOP %+0.4E'%(ch,stop))
        self.demand('SOUR%d:FREQ:STOP?'%ch, stop)
        self.write('SOUR%d:SWE:TIME %+0.4E'%(ch,time))
        self.demand('SOUR%d:SWE:TIME?'%ch, time)
        return
    @property
    def CH1(self):
        "Properties of channel 1 (on, burst, etc.) -- given as a :class:`AFG_Channel_Properties` object"
        if hasattr(self,'_ch1_class'):
            return self._ch1_class
        else:
            self._ch1_class = AFG_Channel_Properties(1,self)
        return self._ch1_class
    @CH1.deleter
    def CH1(self):
        del self._ch1_class
    @property
    def CH2(self):
        "Properties of channel 2 (on, burst, etc.) -- given as a :class:`AFG_Channel_Properties` object"
        if hasattr(self,'_ch2_class'):
            return self._ch2_class
        else:
            self._ch2_class = AFG_Channel_Properties(2,self)
        return self._ch2_class
    @CH2.deleter
    def CH2(self):
        del self._ch2_class

