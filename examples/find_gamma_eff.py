from pylab import *
import sys

config_dict = SpinCore_pp.configuration('active.ini')
print("Your original gamma effective was:". config_dict['gamma_eff_MHz_G'])
Delta_nu = float(sys.argv[1])/1e6
new_gamma = config_dict['carrierFreq_MHz']/config_dict['Field'] - (
        Delta_nu/config_dict['Field'])
print("based on your offset of %d, your new gamma_eff should be %d"%(Delta_nu,new_gamma))
config_dict['gamma_eff_MHz_G'] = new_gamma
config_dict.write()

