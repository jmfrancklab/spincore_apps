import numpy as np
from numpy import r_
import sympy as sp
from scipy.integrate import quad
import pyspecdata as psp

"Helper functions for dealing with powers"
# {{{ For even spacing based on phalf estimation
def integral_as_quad(expr, lims):
    var, a, b = lims
    return quad(sp.lambdify(var, expr, modules="numpy"), a, b)[0]


Emax, p, phalf, pmax = sp.symbols("E_max p p_half p_max", real=True, positive=True)


def Ep_spacing_from_phalf(
    est_phalf=0.2,
    sim_Emax=30,
    max_power=3.16,
    aspect_ratio=1.618,
    p_steps=20,
    min_dBm_step=1.0,
    three_down=True,
    fl=None,
):
    """
        Parameters
        ==========
        est_phalf:      float
                        estimated power for half saturation
        sim_Emax:       float
                        ONLY FOR PLOTTING PURPOSES. when fl is not None, this will generate an E(p) curve using this Emax but it is not used in the actual function.
        max_power:      float
                        maximum power that you will send to the sample (W)
        aspect_ratio:   float
                        width of figure size/ height of figure size. Most likely you will not need to change this but if you want to make a different figure size aspect ratio this ensures the E(p) spacing is even within that figure
        p_steps:        float
                        number of power steps in the enhancement experiment
        min_dBm_step:   float
                        minimum stepsize that is allowed, in dBm
        three_down:     boolean
                        Do you want three evenly spaced powers on the way
                        back down?
    Return
        ======
        List of evenly spaced powers (dBm) for generated a nicely spaced Ep curve for a specific sample based on the estimated p_half.
    """
    p_array = r_[0:max_power:200j]
    f = 1 - Emax * (p / (p + phalf))
    f_fn = sp.lambdify((Emax, phalf, p), f)
    dline = sp.simplify(
        sp.sqrt(1 + (sp.diff(f / Emax, p) * (max_power / aspect_ratio)) ** 2)
    )
    if fl is not None:
        psp.figure(figsize=(12, 12 / aspect_ratio))
    length_vs_p = sp.Integral(dline, (p, 0, pmax))
    length_vs_p_fn = np.vectorize(
        sp.lambdify(
            (phalf, pmax),  # no longer depends on Emax!
            length_vs_p,
            modules=[{"Integral": integral_as_quad}, "sympy"],
        ),
        excluded=[0],
    )
    length_data = psp.nddata(length_vs_p_fn(est_phalf, p_array), [-1], ["p"]).setaxis(
        "p", p_array
    )
    length_data.invinterp("p", np.linspace(0, length_data["p", -1].item(), p_steps))
    if fl is not None:
        fl.plot(
            f_fn(sim_Emax, est_phalf, length_data.fromaxis("p")), "o", human_units=False
        )
        psp.text(
            0.5,
            0.5,
            "Just showing the E(p) to show JF the spacing is what we want - \nwe can delete this figure after we are good with everything else",
        )
    W_settings = length_data.fromaxis("p").data
    rdB_settings = np.ones_like(W_settings)
    for x in range(len(W_settings)):
        if x == 0:
            rdB_settings[x] = 0.0
        else:
            rdB_settings[x] = (
                round(10 * (np.log10(W_settings[x]) + 3.0) / min_dBm_step)
                * min_dBm_step
            )
    dB_settings = np.unique(rdB_settings)
    if three_down:
        append_dB = [
            rdB_settings[
                abs(10 ** (rdB_settings / 10.0 - 3) - max_power * frac).argmin()
            ]
            for frac in [0.75, 0.5, 0.25]
        ]
        dB_settings = np.append(rdB_settings, append_dB)
    return dB_settings.real


# }}}
# {{{ Older method of just generating a power list - works for concentrated samples but not great for dilute
def gen_powerlist(max_power, steps, min_dBm_step=0.5, three_down=False):
    """Generate a list of (roughly) evenly spaced powers up
    to max_power.
    With `three_down` set to False, generate steps-1 steps, as is appropriate
    for an enhancement curve with `steps` indirect points.
    With `three_down` set to True, adds three points going down in power at the end.

    Parameters
    ==========
    min_dBm_step: float
        minimum stepsize that is allowed, in dBm
    three_down: boolean
        Do you want three evenly spaced powers on the way
        back down?
    """
    lin_steps = steps

    def det_allowed(lin_steps):
        powers = r_[0 : max_power : 1j * lin_steps][1:]
        vectorize(powers)
        rdB_settings = ones_like(powers)
        for x in range(len(powers)):
            rdB_settings[x] = (
                round(10 * (log10(powers[x]) + 3.0) / min_dBm_step) * min_dBm_step
            )  # round to nearest min_dBm_step
        return unique(rdB_settings)

    dB_settings = det_allowed(lin_steps)
    while len(dB_settings) < steps - 1:
        lin_steps += 1
        dB_settings = det_allowed(lin_steps)
        if lin_steps >= 200:
            raise ValueError(
                "I think I'm in an infinite loop -- maybe you"
                "can't request %d steps between 0 and %f W without going"
                "below %f a step?"
            ) % (steps, max_power, min_dBm_step)
    if three_down:
        append_dB = [
            dB_settings[abs(10 ** (dB_settings / 10.0 - 3) - max_power * frac).argmin()]
            for frac in [0.75, 0.5, 0.25]
        ]
        dB_settings = append(dB_settings, append_dB)
    return dB_settings


# }}}
