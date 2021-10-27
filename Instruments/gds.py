from pylab import *
from pyspecdata import nddata,strm
from .serial_instrument import SerialInstrument

import logging
logger = logging.getLogger('GDS Scope Class')

class GDS_Channel_Properties (object):
    """This class controls the channel properties (display (or output), voltage level (volts/div), etc.).
    
    By setting these up as properties, we allow tab completion, and for sensible manipulation of parameters.
    """
    def __init__(self,ch,gds):
        """initialize a new `GDS_Channel_Properties` class
        
        Properties
        ----------

        ch : int

            the GDS channel you are manipulating or learning about

        gds : GDS_scope 

            the GDS instance that initialized this
        """
        self.ch = ch
        self.gds = gds 
        return
    @property
    def disp(self):
        """The display, whether or not the channel is on or off
        """
        cmd = ':CHAN%d:DISP?'%self.ch
        return str(self.gds.respond(cmd))
    @disp.setter
    def disp(self,onoff):
        if onoff:
            self.gds.write(':CHAN%d:DISP ON'%self.ch)
            self.gds.demand(":CHAN%d:DISP?"%self.ch,'ON')
            cmd = ':CHAN%d:DISP?'%self.ch
            print("CH",self.ch," display is",bool(str(self.gds.respond(cmd))))
        else:
            self.gds.write(':CHAN%d:DISP OFF'%self.ch)
            self.gds.demand("CHAN%d:DISP?"%self.ch,'OFF')
        return    
    @property
    def voltscal(self):
        """The Channel Scale or volts/div displayed on the GDS for each channel.
        
        Set this by sending a number in scientific notation, such as 1E0 for 1V/div or 1E-3 for 1mV/div
        Careful with formatting to use a capital E
        Settable values are restricted to what the GDS accepts.
        """
        cmd = ':CHAN%d:SCAL?'%self.ch
        return float(self.gds.respond(cmd))
    @voltscal.setter
    def voltscal(self,vs):
        vs_str = '%0.3E'%vs
        cmd = ':CHAN%d:SCAL %f'%(self.ch,vs)
        #self.demand(':CHAN1:SCAL 100e-9',vs_str)
        print("Setting CH",self.ch," volt scale to %s volt/div"%vs_str)
        self.gds.write(cmd)
        return
#        @property
#     def output(self):
#         cmd = 'OUTP%d?'%self.ch
#         return bool(int(self.afg.respond(cmd)))
#     @output.setter
#     def output(self,onoff):
#         if onoff:
#             self.afg.write('OUTP%d ON'%self.ch)
#             self.afg.demand('OUTP%d?'%self.ch,1)
#         else:
#             self.afg.write('OUTP%d OFF'%self.ch)
#             self.afg.demand('OUTP%d?'%self.ch,0)
#         return
#     @property

class GDS_scope (SerialInstrument):
    """Next, we can define a class for the scope, based on `pyspecdata`"""
    def __init__(self,model='3254'):
        super().__init__('GDS-'+model)
        print(strm("debugging -- identify from within GDS",super().respond('*idn?')))
        logger.debug(strm("identify from within GDS",super().respond('*idn?')))
        logger.debug("I should have just opened the serial connection")
        self.CH1 = GDS_Channel_Properties(1,self)
        self.CH2 = GDS_Channel_Properties(2,self)
        return
    def __getitem__(self,arg):
        if arg == 0:
            return self.CH1
        if arg == 1:
            return self.CH2
        else:
            raise ValueError("There is no channel "+str(arg))

    def timscal(self,ts,pos=None):
        print("Query time scale in sec/div")
        print(self.respond(':TIM:SCAL?'))
        ts_str = ' %0.6e'%ts
        self.write(':TIM:SCAL ',ts)
        self.demand(':TIM:SCAL?',ts)
        if pos is not None:
            self.write(':TIM:POS ',pos)
            self.demand(':TIM:POS?',pos)
        #Running into matching error here, but command does work
        print("Time scale (sec/div) is set to",self.respond(':TIM:SCAL?'))
        return
    
    def acquire_mode(self,mode,num_avg=1):
        """"Set the acquisition mode on the scope. Prints the current mode setting.

        Parameters
        ==========

        mode : string

            Possible options: 
                'sample' (or 'SAMP') = Sample mode sampling
                'pdetect' (or 'PDET') = Peak detection sampling
                'average' (or 'AVER') = Average mode sampling. Must also set number of averages 
                desired per sample, `num_avg`.

        num_avg : int
            
            By default set equal to 1. Only needs to be set when in average mode sampling. Only
            possible values are powers of 2 up to 2**8: 2, 4, 8, 16, 64, 128, 256.
            
        Returns
        =======

        None
        
        """
        possible_avg = [2**1, 2**2, 2**3, 2**4, 2**5, 2**6, 2**7, 2**8]
        self.write(':ACQ:MOD %s'%mode)
        print("Acquire mode is:",self.respond(':ACQ:MOD?'))
        if num_avg in possible_avg:
            self.write(':ACQ:AVER %d'%num_avg)
            print("Number of averages set to:",self.respond(':ACQ:AVER?'))
    
    def autoset(self):
        self.write(':AUTOS')
    def waveform(self,ch=1):
        """Retrieve waveform and associated parameters form the scope.

        Comprises the following steps:

        * opens the port to the scope
        * acquires what is saved in memory as string
        * Divides this string at hashtag which separates settings from waveform

        Parameters
        ==========

        ch : int
            
            Which channel do you want?

        Returns
        =======

        data : nddata

            The scope data, as a pyspecdata nddata, with the
            extra information stored as nddata properties
        """
        self.write(':ACQ%d:MEM?'%ch)
        def upto_hashtag():
            this_char = self.read(1)
            this_line = ''
            while this_char != '#':          
                this_line += this_char
                this_char = self.read(1)
            return this_line
        #Further divides settings
        preamble = upto_hashtag().split(';')
        
        #Retrieves 'memory' of 25000 from settings
        #Waveform data is 50,000 bytes of binary data (2*mem)
        mem = int(preamble[0].split(',')[1])
        
        #Generates list of parameters in the preamble
        param = dict([tuple(x.split(',')) for x in preamble if len(x.split(',')) == 2])

        #Reads waveform data of 50,000 bytes
        self.read_binary(6) # length of 550000
        data = self.read_binary(50001)
        assert data[-1] == 10, "data is not followed by newline!, rather it's %d"%data[-1]
        data = data[:-1]

        # convert the binary string
        data_array = fromstring(data,dtype='i2')
        data_array =  double(data_array)/double(2**(2*8-1))
        # I could do the following
        #x_axis = r_[0:len(data_array)] * float(param['Sampling Period'])
        # but since I'm "using up" the sampling period, do this:
        x_axis = r_[0:len(data_array)] * float(param.pop('Sampling Period'))
        # r_[... is used by numpy to construct arrays on the fly


        # Similarly, use V/div scale to scale the y values of the data
        data_array *= float(param.pop('Vertical Scale'))/0.2 # we saw
        #              empirically that 0.2 corresponds to about 1 division
        if not all(isfinite(x_axis)):
            raise ValueError("your x axis is not finite!! len(data_array) is %s and 'Sampling Period' is %s"%(str(len(data_array)),str(param.pop('Sampling Period'))))
        data = nddata(data_array,['t']).setaxis('t',x_axis)
        data.set_units('t',param.pop('Horizontal Units').replace('S','s'))
        data.set_units(param.pop('Vertical Units'))
        name = param.pop('Source')
        # the last part is not actually related to the nddata object -- for convenience,
        # I'm just converting the data type of the remaining parameters
        def autoconvert_number(inpstr):
            try:
                retval = float(inpstr)
                isnumber = True
            except:
                retval = inpstr
                isnumber = False
            if isnumber:
                try:
                    intval = int(inpstr)
                    if str(intval) == inpstr:
                        retval = intval
                except:
                    pass
            return retval
        for j in list(param.keys()):
            param[j] = autoconvert_number(param[j])
        data.other_info.update(param)
        data.name(name)
        return data
