"just testing/illustrating the basic function of configfiles -- really for devel purposes"

import configparser
import os
import SpinCore_pp
retval_dict, config = SpinCore_pp.parser_function("active.ini")
retval_dict['new_thing'] = 300
print(retval_dict)
retval_dict, config = SpinCore_pp.parser_function("active.ini")
print(retval_dict)

