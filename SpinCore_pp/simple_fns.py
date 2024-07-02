def get_integer_sampling_intervals(SW_kHz, time_per_segment_ms):
    """Calculate the actual SW the SpinCore uses based on the digitization rate
    and use that value to calculate the number of points

    Parameters
    ==========
    SW_kHz: float
        Desired SW in kHz
    time_per_segment_ms: float
        Time per transient in ms

    Returns
    =======
    nPoints: float
        Number of points per transient
    actual_SW_kHz: float
        The rounded integral decimation the the SpinCore will use for the SW.
    new_time_per_segment_ms: float
        Calculated time per transient based on the integral number
        of samples from the rounded integral decimation.
    """
    actual_SW_kHz = 75e6 / round(75e6 / SW_kHz / 1e3) / 1e3
    nPoints = int(time_per_segment_ms * actual_SW_kHz + 0.5)
    new_time_per_segment_ms = nPoints / actual_SW_kHz
    return nPoints, actual_SW_kHz, new_time_per_segment_ms
