def get_integer_sampling_intervals(config_dict, use_echo_acq=False):
    """
    calculate the actual SW the SpinCore uses based on the digitization
    rate and use that value to calculate the number of points
    Parameters
    ==========
    config_dict:     dict
                    configuration file containing all parameters for the experiment
                    and sample.
    use_echo_acq:   bool
                    if true will use the echo_acq_ms in calculating the nPoints (per echo)
    Returns
    =======
    config_dict:    dict
                    edited configuration file containing the actual SW the SpinCore will
                    use as well as the calculated number of points (per echo when applicable)
                    as well as the proper acquisition time based on the number of points and
                    spectral width
    """
    assert config_dict is not None, "You need to feed me the configuration file!"
    config_dict["SW_kHz"] = 75e6 / round(75e6 / config_dict["SW_kHz"] / 1e3) / 1e3
    if use_echo_acq:
        nPoints = int(config_dict["echo_acq_ms"] * config_dict["SW_kHz"] + 0.5)
        config_dict["echo_acq_ms"] = nPoints / config_dict["SW_kHz"]
    else:
        nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
        config_dict["acq_time_ms"] = nPoints / config_dict["SW_kHz"]
    config_dict.write()
    return config_dict, nPoints
