from pylab import *
from pyspecdata import *
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
prog, act90, act180 = map(array, zip(*datapoints))
#plot(prog,act90)
#plot(2*prog,act180)
plen_prog = r_[0, prog, 2 * prog]
plen_actual = (
    r_[0, act90, act180] * 2 * prog[-1] / act180[-1]
)  # assume the longest pulse is about the correct length
# ordering = argsort(plen_actual)
#figure()
calibration_data = nddata(plen_prog, [-1], ["plen"]).setaxis(
    "plen", plen_actual
)
calibration_data.sort("plen")
plen_fine = nddata(r_[0 : max(plen_actual) : 200j], "plen")
plen_fine = nddata(r_[0 : 30: 200j], "plen")
c = calibration_data.polyfit("plen", order=10)
#plot(calibration_data,'o')
#plot(plen_fine.eval_poly(c,'plen'))
# rather than saving, let's just hardcode these
for j in range(len(c)):
    print(f"c[{j}] = {c[j]:0.8e}")
print("r_[" + ",".join([f"{v:0.8e}" for v in c]) + "]")
# let's see that we know how to use this with polyval
def prog_plen(desired_actual):
    "returns the pulse length that you need to program given a particular actual pulse length"
    # finally, let's generate the calibration curve from these hard-coded coeff
    # (copied and pasted from previous)
    c = r_[
        1.16388244e-01,
        4.53149832e00,
        -1.76826907e00,
        4.84434996e-01,
        -8.25811850e-02,
        9.09890119e-03,
        -6.56683149e-04,
        3.07625484e-05,
        -8.99083655e-07,
        1.48684691e-08,
        -1.06082445e-10,
    ]
    return polyval(c[::-1], desired_actual)
#plot(plen_fine.getaxis('plen'),prog_plen(plen_fine.getaxis('plen')),":")
show()
