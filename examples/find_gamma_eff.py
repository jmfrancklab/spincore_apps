from pylab import *
import sys
from pyspecdata import *
import SpinCore_pp

config_dict = SpinCore_pp.configuration('active.ini')
print("Your original gamma effective was:", config_dict['gamma_eff_MHz_G'])
Delta_nu = float(sys.argv[1])/1e6
new_gamma = config_dict['gamma_eff_MHz_G'] * (1 - (Delta_nu/config_dict['carrierFreq_MHz'])) 
print("based on your offset of %d"%Delta_nu)
print("your new gamma_eff should be %.8f"%new_gamma)
config_dict['gamma_eff_MHz_G'] = new_gamma
config_dict.write()

