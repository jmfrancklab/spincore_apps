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
                    The actual SW SpinCore will use based on the maximum
                    digitization rate.
    acq_time_ms:    float
                    calculated acquisition time per transient based on the 
                    calculated nPoints and actual SW that the SpinCore will use
    """
    actual_SW_kHz = 75e6 / round(75e6 / SW / 1e3) / 1e3
    nPoints = int(acq_time_ms * actual_SW_kHz + 0.5)
    new_acq_time_ms = nPoints / actual_SW_kHz
    return nPoints, actual_SW_kHz, acq_time_ms
