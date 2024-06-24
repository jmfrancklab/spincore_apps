def get_integer_sampling_intervals(SW=None, acq_time_ms=None):
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
    if SW is None:
        print("You need to tell me what the SW is in units of kHz!")
    if acq_time_ms is None:
        print("You need to define the acquisition time in units of ms!")
    actual_SW = 75e6 / round(75e6 / SW / 1e3) / 1e3
    nPoints = int(acq_time_ms * actual_SW + 0.5)
    return actual_SW, nPoints
