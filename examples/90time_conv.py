""" Ninety pulse length conversion
==================================
The programmed SpinCore pulse length does not match the actual output pulse length. This example finds what pulse length should be fed to SpinCore in order to get a pulse length with the actual desired pulse length.
"""
from pylab import *
from pyspecdata import *
#from SpinCore_pp.pulse_length_conv import prog_plen
fl = figlist_var()
def prog_plen(desired_actual):
    """
    Parameters
    ==========
    desired_actual: float
                    the actual pulse length you wish the spincore to output, in us
    Returns
    =======
    retval: float
            The pulse length you tell spincore in order to get the desired actual.
    """
    # {{{ list of programmed p90, actual p90 and actual 180
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
    # neat JF trick for storing these data points
    prog90, act90, act180 = map(array, zip(*datapoints))
    # }}}
    plen_prog = r_[0, prog90, 2 * prog90]  # array of programmed pulse lengths
    plen_actual = (
        r_[0, act90, act180] * 2 * prog90[-1] / act180[-1]
    )  # assume the longest pulse is about the correct length
    calibration_data = nddata(plen_prog, [-1], ["plen"]).setaxis(
        "plen", plen_actual
    )  # programmed pulse lengths with the actual pulse
    calibration_data.sort("plen")
    c = calibration_data.polyfit(
        "plen", order=10
    )  # fit the programmed vs actual lengths to a polynomial
    # {{{ Make an array out of the fitting coefficients from the polyfit
    coeffs = np.zeros(len(c))
    for j in range(len(c)):
        coeffs[j] = c[j]
    # }}}
    retval = polyval(coeffs[::-1], desired_actual)
    # {{{ Plot the calibration data with the users datapoint plotted on top
    #print(
    #    "In order to get an actual pulse length of %d, you must tell SC to send a pulse length of %d"
    #    % (desired_actual, retval)
    #)
    return retval
desired_plen = r_[1,12.5,0.5]
prog = r_[1,2,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10,10.5,11,11.5,12,12.5]
act_p90 = r_[2.259,5.781,10.413,13.2053,16.981,20.428,24.853,30.0159,35.6903,42.2129,48.9577,55.977,63.045,69.881,76.973,84.515,91.7,98.66,105.327,112.985,120.264,126.251]
act_p180 = r_[5.754,16.617,36.023,49.41,63.726,77.547,91.518,106.302,119.849,134.328,149.029,162.774,176.917,190.167,203.486,217.965,232.042,245.213,258.004,272.776,286.884,299.009]
plen_prog = r_[0,prog,2*prog]
plen_actual = (
        r_[0,act_p90, act_p180]*2*prog[-1]/act_p180[-1]
        )
calib_data = nddata(plen_actual, [-1],['plen_prog']).setaxis(
        "plen_prog",plen_prog)
calib_data.sort('plen_prog')
fl.next('calibration data')
fl.plot(calib_data,'o')
#plen_fine = nddata(r_[0:max(plen_actual):200j],'plen')
plt.ylabel('actual pulse time')
plt.xlabel('programmed pulse time')
#calib_fine = prog_plen(plen_fine.getaxis("plen"))
#print(calib_fine)
#fl.plot(calib_fine)
test = r_[0:25:25j]
prog_plen = prog_plen(test)
plt.plot(prog_plen,test,'o')
print(prog_plen)
show()
