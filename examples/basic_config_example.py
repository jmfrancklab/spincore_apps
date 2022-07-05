"just testing/illustrating the basic function of configfiles -- really for devel purposes"

import configparser
import os

config = configparser.ConfigParser()
config.sections()
config.read('active.ini')
acq_params = config['acq_params']
amplitude = float(acq_params['amplitude'])
print(type(amplitude))
print("amplitude is set to",amplitude)
p90_time = float(acq_params['p90_us'])
print("90 time is set to", p90_time)
p90_time = 4.464
config.set('acq_params','p90_us',f'{p90_time:0.4f}')
new_p90 = float(acq_params['p90_us'])
print("90 time is now",new_p90)
with open('active.ini','w') as fp:
    config.write(fp)
