from pylab import array
from numpy import zeros, polyval
from pyspecdata import r_, nddata


def prog_plen(desired_actual):
    """
    Takes the desired pulse length and tells the
    user what pulse length should be programmed in order to get the actual desired
    pulse length
    Parameters
    ==========
    desired_actual: float
                    the actual pulse length you wish the spincore to output,
                    in us
    Returns
    =======
    retval: float
            The pulse length you tell spincore in order to get the desired actual.
    """
    # {{{ list of programmed p90, actual p90 and actual 180 - used in
    # generating the calibrated fit
    # list of the programmed pulse length, the actual p90 length 
    # and the actual p180 length based on the programmed p90
    datapoints = [
        (1, 2.25869, 5.75412),
        (2, 5.78065, 16.6168),
        (3, 10.4132, 36.0229),
        (3.5, 13.2053, 49.4104),
        (4, 16.9808, 63.7255),
        (4.5, 20.4275, 77.5474),
        (5, 24.8538, 91.5177),
        (5.5, 30.0159, 106.302),
        (6, 35.6903, 119.849),
        (6.5, 42.2129, 134.328),
        (7, 48.9577, 149.029),
        (7.5, 55.977, 162.774),
        (8, 63.0445, 176.917),
        (8.5, 69.881, 190.167),
        (9, 76.9727, 203.486),
        (9.5, 84.5149, 217.965),
        (10, 91.7002, 232.042),
        (10.5, 98.6599, 245.213),
        (11, 105.327, 258.004),
        (11.5, 112.985, 272.776),
        (12, 120.264, 286.884),
        (12.5, 126.251, 299.009),
    ]
    # neat JF trick for organizing these data points
    prog90, act90, act180 = map(array, zip(*datapoints))
    # }}}
    # {{{ prepare data into arrays for interpolation
    # gather programmed pulse lengths in array
    plen_prog = r_[0, prog90, 2 * prog90] 
    # assume the longest pulse is about the correct length
    # and again gather into an array
    plen_actual = r_[0, act90, act180] * 2 * prog90[-1] / act180[-1] 
    # }}}
    calibration_data = nddata(plen_prog, [-1], ["plen"]).setaxis("plen", plen_actual)
    calibration_data.sort("plen")
    # fit the programmed vs actual lengths to a polynomial
    c = calibration_data.polyfit("plen", order=10)
    # {{{ Make an array out of the fitting coefficients from the polyfit
    coeffs = zeros(len(c))
    for j in range(len(c)):
        coeffs[j] = c[j]
    # }}}
    return polyval(coeffs[::-1],desired_actual)
