""" Ninety pulse length conversion
==================================
The programmed SpinCore pulse length does not
match the actual output pulse length. This example
finds what pulse length should be fed to SpinCore
in order to get a pulse length with the actual
desired pulse length.
"""
import matplotlib.pyplot as plt
from pyspecdata import *
from SpinCore_pp.pulse_length_conv import prog_plen

desired_plen = r_[0:25:25j]
prog_plen = prog_plen(desired_plen)
with figlist_var() as fl:
    fl.next("Actual vs programmed plen")
    plt.plot(prog_plen, desired_plen, "o")
    plt.ylabel(r"actual plen / $\mu$s")
    plt.xlabel(r"programmed plen / $\mu$s")
