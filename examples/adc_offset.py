import SpinCore_pp
myconfig = SpinCore_pp.configuration("active.ini")
myconfig['adc_offset'] = SpinCore_pp.adc_offset()
print("You're ADC offset is:",myconfig['adc_offset'])
myconfig.write()
