"just testing/illustrating the basic function of configfiles -- really for devel purposes"

import configparser
import os
import SpinCore_pp
retval_dict, config = SpinCore_pp.parser_function("active.ini")
file_names=config["file_names"]
acq_params = config["acq_params"]
print("initially our repetition delay is", retval_dict["repetition_us"])
repetition_us = 5.3e6
config.set("acq_params","repetition_us",f"{repetition_us:0.4f}")
with open("active.ini","w") as fp:
    config.write(fp)
retval_dict, config = SpinCore_pp.parser_function("active.ini")
print(retval_dict)
print(retval_dict["cpmg_counter"])
