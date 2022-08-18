import SpinCore_pp
myconfig = SpinCore_pp.configuration("active.ini")
myconfig['adc_offset'] = SpinCore_pp.adc_offset()
print(myconfig['adc_offset'])
myconfig.write()
