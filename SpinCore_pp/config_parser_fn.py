from pyspecdata import *
import configparser


def parser_function(parser_filename):
    # open parser
    config = configparser.ConfigParser()
    config.sections()
    config.read("active.ini")
    try:
        acq_params = config["acq_params"]
    except KeyError:
        config.add_section("acq_params")
        acq_params = config["acq_params"]
    try:    
        file_names = config["file_names"]
    except KeyError:
        config.add_section("file_names")
        file_names = config["file_names"]
    try:    
        odnp_params = config["odnp_params"]
    except KeyError:
        config.add_section("odnp_params")
        odnp_params = config["odnp_params"]
    retval = {}
    # {{{ floats, by section
    for thisname in [
        "p90_us",
        "deadtime_us",
        "amplitude",
        "deblank_us",
        "tau_us",
        "repetition_us",
        "SW_kHz",
        "acq_time_ms",
        "carrierFreq_MHz",
    ]:
        try:
            retval[thisname] = float(file_names[thisname.lower()])
        except KeyError:
            print(thisname, f"it doesn't make sense for you to have a .ini file where the {thisname} parameter is not set!")
    for thisname in [
        "Field",
        "uw_dip_center_GHz",
        "uw_dip_width_GHz",
        "FIR_rep",
        "max_power"
    ]:
        try:
            retval[thisname] = float(file_names[thisname.lower()])
        except KeyError:
            print(thisname, f"it doesn't make sense for you to have a .ini file where the {thisname} parameter is not set!")
    # }}}
    # {{{ int, by section
    for thisname in [
        "nScans",
        "adc_offset",
        "nEchoes",
    ]:
        retval[thisname] = int(acq_params[thisname.lower()])
        try:
            retval[thisname] = int(file_names[thisname.lower()])
        except KeyError:
            print(thisname, f"it doesn't make sense for you to have a .ini file where the {thisname} parameter is not set!")
    for thisname in [
        "power_steps",
        "num_T1s",
    ]:
        retval[thisname] = int(odnp_params[thisname.lower()])
        # if these are not set, we actually want an error!
        try:
            retval[thisname] = int(file_names[thisname.lower()])
        except KeyError:
            print(thisname, f"it doesn't make sense for you to have a .ini file where the {thisname} parameter is not set!")
    for thisname in [
        "odnp_counter",
        "echo_counter",
        "cpmg_counter",
        "IR_counter",
    ]:
        try:
            retval[thisname] = int(file_names[thisname.lower()])
        except KeyError:
            print(thisname, "doesn't exist yet so we are setting it to 0")
            retval[thisname] = 0
        # what happens if thisname is not already in the ini file?
        # does it return none? or does it fail with a key error?
        # in either case, we should add code here, so that if it doesn't
        # exist, just go ahead and set it to 0
        # this can be accomplished by either testing for None or with a
        # try/except
    # }}}
    # {{{ all the rest of the file name parameters are just strings
    for thisname in [
        "chemical",
        "type",
    ]:
        try:
            retval[thisname] = file_names[thisname.lower()]
        except KeyError:
            print(thisname, f"it doesn't make sense for you to have a .ini file where the {thisname} parameter is not set!")
    # }}}
    for thisname in [
        "date"
    ]:
        try:
            retval[thisname] = int(file_names[thisname.lower()])
        except KeyError:
            print(thisname, f"it doesn't make sense for you to have a .ini file where the {thisname} parameter is not set!")
    return retval, config  # return dictionary and also the config file itself
