from pyspecdata import *
def gen_powerlist(max_power, steps, min_dBm_step=0.5):
    "generate a list of (roughly) evenly spaced powers up to max_power"
    lin_steps = steps
    def det_allowed(lin_steps):
        powers = r_[0:max_power:1j*lin_steps][1:]
        vectorize(powers)
        rdB_settings = ones_like(powers)
        for x in range(len(powers)):
            rdB_settings[x] = round(10*(log10(powers[x])+3.0)/min_dBm_step)*min_dBm_step # round to nearest min_dBm_step
        return unique(rdB_settings)
    dB_settings = det_allowed(lin_steps)
    while len(dB_settings) < steps-1:
        lin_steps += 1
        dB_settings = det_allowed(lin_steps)
        if lin_steps >= 200:
            raise ValueError("I think I'm in an infinite loop -- maybe you"
                    "can't request %d steps between 0 and %f W without going"
                    "below %f a step?")%(steps,max_power,min_dBm_step)
    return dB_settings
max_power = 0.5
power_steps = 15
dB_settings = gen_powerlist(max_power,power_steps)
append_dB = [dB_settings[abs(10**(dB_settings/10.-3)-max_power*frac).argmin()]
#        #for frac in [0.75,0.5,0.25]]
        for frac in [0.25]]
dB_settings = append(dB_settings,append_dB)
dB_settings = [2.,3.,5.,7.,9.,11.,13.,15.,18.,21.,23.,25.,26.,27.]
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)

