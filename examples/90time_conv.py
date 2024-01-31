""" Ninety pulse length conversion
==================================
The programmed SpinCore pulse length does not match the actual output pulse length. This example finds what pulse length should be fed to SpinCore in order to get a pulse length with the actual desired pulse length.
"""
from pylab import *
from pyspecdata import *
from SpinCore_pp.pulse_length_conv import prog_plen
desired_plen = r_[1,12.5,0.5]
prog_plen = prog_plen(desired_plen)
print(prog_plen)
show()
