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
myconfig["field"] = 3600.99
print(
    myconfig.asdict()
)  # so we can, e.g. put in an HDF5 file -- this should have the nice case that was registered
print("echo counter was", myconfig["echo_counter"], "and I'm going to increment it")
myconfig["echo_counter"] += 1
myconfig.write()  # this should write the field and whatever else we've changed
