def get_integer_sampling_intervals(SW_kHz, acq_time_ms):
    """
    calculate the actual SW the SpinCore uses based on the digitization
    rate and use that value to calculate the number of points
    Parameters
    ==========
    SW_kHz:         float
                    desired SW in kHz
    acq_time_ms:    float
                    acquisition time per transient in ms
    Returns
    =======
    nPoints:        float
                    number of points per transient
    actual_SW_kHz:  float   
                    The rounded integral decimation the the SpinCore will use for
                    the SW.
    acq_time_ms:    float
                    calculated acquisition time per transient based on the 
                    integral number of samples from the rounded integral decimation.
    """
    actual_SW_kHz = 75e6 / round(75e6 / SW_kHz / 1e3) / 1e3
    nPoints = int(acq_time_ms * actual_SW_kHz + 0.5)
    new_acq_time_ms = nPoints / actual_SW_kHz
    return nPoints, actual_SW_kHz, new_acq_time_ms
