"just testing/illustrating the basic function of configfiles -- really for devel purposes"

import configparser
import os
import SpinCore_pp

# initialize
myconfig = SpinCore_pp.configuration("active.ini")
# set a parameter that's not registered:
try:
    myconfig["new_thing"] = 300
    failure = False
except:
    failure = True
if failure:
    print("I tried to set an unregistered parameter, and it failed ... good!")
else:
    raise ValueError("Didn't fail on unregistered parameter!")
# look for a parameter that's not registered:
try:
    retval = myconfig["another_thing"]
    failure = False
except:
    failure = True
if failure:
    print("I tried to get an unregistered parameter, and it failed ... good!")
else:
    raise ValueError("Didn't fail on unregistered parameter!")
# look for a parameter that isn't in the ini file, but is registered with a default
print("odnp_counter", myconfig["odnp_counter"])  # look for something that doesn't exist
# look for a parameter that isn't in the ini file and does not have a default
try:
    print("p90_us", myconfig["p90_us"])  # look for something that doesn't exist
except Exception as e:
    print("looking for p90_us failed with:\n\n", e)
# set a parameter that is registered, and see that it will change
myconfig["adc_offset"] = 30
print(
    myconfig.asdict()
)  # so we can, e.g. put in an HDF5 file -- this should have the nice case that was registered
print("echo counter was", myconfig["echo_counter"], "and I'm going to increment it")
myconfig["echo_counter"] += 1
myconfig.write()  # this should write the adc offset and whatever else we've changed

# {{{ pull only the subset of info we want to actually pass to our
#     function
relevant_kwargs = {
    j: myconfig[j]
    for j in ["krho_cold", "krho_hot", "T1water_cold", "T1water_hot"]
    if j in myconfig.keys()
}
print(
    "for calculating a IR or FIR vdlist, the relevant parameters that I find in your ini file are",
    relevant_kwargs,
)
print(
    "this gives me the vdlist:",
    SpinCore_pp.vdlist_from_relaxivities(myconfig["concentration"], **relevant_kwargs),
)
# }}}
