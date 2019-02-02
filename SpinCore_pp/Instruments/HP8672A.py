from pylab import *
from .gpib_eth import gpib_eth

class HP8672A (gpib_eth):
    def __init__(self, gpibaddress=51):
        super(self.__class__,self).__init__()
        self.gpibaddress = gpibaddress
        self.stepsize = 0.5e6 # this is a lie, but it's used as a default by wobbandmin
    def set_frequency(self,frequency):
        self.write(self.gpibaddress,'P%08dZ0'%int(round(frequency*1e-3)))# just use the 10 GHz setting, and fill out all the other decimal places with zeros
        return
    def set_power(self,dBm):
        assert dBm <= 3 and dBm >= -120, "dBm value must be between -120 and 3 dBm"
        # {{{ all of the following is based off fig 15-6 from the programming manual
        ascii_set = list('013456789:;<=')
        coarse_values = r_[0:-120:-10]
        vernier = r_[3:-11:-1]
        # }}}
        coarse_idx = argmin(abs(dBm - coarse_values))
        residual = dBm - coarse_values[coarse_idx]
        vernier_idx = argmin(abs(residual - vernier))
        print "I'm going to set the coarse value to",coarse_values[coarse_idx],"and the vernier to",vernier[vernier_idx]
        cmd = 'K' + ascii_set[coarse_idx] + ascii_set[vernier_idx]
        print "command for this is",cmd
        self.write(self.gpibaddress,cmd)
        return
