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
        retval[thisname] = float(acq_params[thisname.lower()])
    for thisname in [
        "Field",
        "uw_dip_center_GHz",
        "uw_dip_width_GHz",
        "FIR_rep",
        "max_power"
    ]:
        if thisname in odnp_params:
            retval[thisname] = float(odnp_params[thisname.lower()])
        else:
            print("You need to add this parameter to the active.ini file then try again")
        # here, we want errors
    # }}}
    # {{{ int, by section
    for thisname in [
        "nScans",
        "adc_offset",
        "nEchoes",
    ]:
        retval[thisname] = int(acq_params[thisname.lower()])
    for thisname in [
        "power_steps",
        "num_T1s",
    ]:
        retval[thisname] = int(odnp_params[thisname.lower()])
        # if these are not set, we actually want an error!
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
        retval[thisname] = file_names[thisname.lower()]
        # do the same thing here -- use "unknown"
    # }}}
    for thisname in [
        "date"
    ]:
        retval[thisname] = int(file_names[thisname.lower()])
        # make sure this doesn't error out
    return retval, config  # return dictionary and also the config file itself
