"just testing/illustrating the basic function of configfiles -- really for devel purposes"

import configparser
import os

config = configparser.ConfigParser()
config.optionxform = str # preserves case?
config.read('active.ini')
print(config.items('acq_params'))
amplitude = config.get('acq_params','amplitude')
print("amplitude is set to",amplitude)
p90_time = config.get('acq_params','p90_us')
print("90 time is set to", p90_time)
p90_time = 4.464
config.set('acq_params','p90_us',f'{p90_time:0.4f}')
new_p90 = config.get('acq_params','p90_us')
print("90 time is now",new_p90)
with open('active.ini','w') as fp:
    config.write(fp)
