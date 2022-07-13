from pyspecdata import *
import configparser


def parser_function(parser_filename):
    # open parser
    config = configparser.ConfigParser()
    config.sections()
    config.read("active.ini")
    acq_params = config["acq_params"]
    file_names = config["file_names"]
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
        retval[thisname] = float(odnp_params[thisname.lower()])
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
    for thisname in [
        "odnp_counter",
        "echo_counter",
        "IR_counter",
    ]:
        retval[thisname] = int(file_names[thisname.lower()])
    # }}}
    # {{{ all the rest of the file name parameters are just strings
    for thisname in [
        "chemical",
        "type",
    ]:
        retval[thisname] = file_names[thisname.lower()]
    # }}}
    for thisname in [
        "date"
    ]:
        retval[thisname] = int(file_names[thisname.lower()])
    return retval, config  # return dictionary and also the config file itself
