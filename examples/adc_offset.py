"""Calculate ADC offset
=======================

Calculates the ADC offset of the SpinCore transceiver board and automatically appends the value to the configuration file used for experiments.
"""
import SpinCore_pp
myconfig = SpinCore_pp.configuration("active.ini")
myconfig['adc_offset'] = SpinCore_pp.adc_offset()
print("Your ADC offset is:",myconfig['adc_offset'])
myconfig.write()
