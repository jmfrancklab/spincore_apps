def get_integer_sampling_intervals(config_dict, use_echo_acq=False):
    """
    calculate the actual SW the SpinCore uses based on the digitization
    rate and use that value to calculate the number of points
    Parameters
    ==========
    SW:     float
            desired spectral width in kHz
    acq_time_ms:    float
                    acquisition time for pulse sequence in ms
    Returns
    =======
    actual_SW:  float
                The calculated spectral width (in kHz) that the SpinCore
                will use based on a digitization rate of 75 MHz
    nPoints:    float
                calculated number of points per transient based on the
                acquisition time and spectral width
    """
    assert config_dict is not None, "You need to feed me the configuration file!"
    config_dict["SW_kHz"] = 75e6 / round(75e6 / config_dict["SW_kHz"] / 1e3) / 1e3
    if use_echo_acq:
        nPoints = int(config_dict["echo_acq_ms"] * config_dict["SW_kHz"] + 0.5)
        config_dict["echo_acq_ms"] = nPoints / config_dict["SW_kHz"]
    else:
        nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
        config_dict["acq_time_ms"] = nPoints / config_dict["SW_kHz"]
    return config_dict
    config_dict

    return actual_SW, nPoints
