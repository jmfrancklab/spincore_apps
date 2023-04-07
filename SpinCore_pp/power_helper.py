from numpy import *
import sympy as sp
from scipy.integrate import quad
from pyspecdata import *
"Helper functions for dealing with powers"
#{{{ For even spacing based on phalf estimation
def integral_as_quad(expr, lims):
    var, a, b = lims
    return quad(sp.lambdify(var, expr, modules='numpy'), a, b)[0]
Emax, p, phalf, pmax = sp.symbols('E_max p p_half p_max',real=True,positive=True)
def thisfn(sim_phalf = 0.2,sim_Emax = 30, sim_pmax = 3.16,
           aspect_ratio = 1.618, p_steps = 20, fl = None):
    p_array = r_[0:sim_pmax:200j]
    f = 1 - Emax*(p/(p+phalf))
    f_fn = sp.lambdify((Emax,phalf,p),f)
    dline = sp.simplify(sp.sqrt(1+(sp.diff(f/Emax,p)*(sim_pmax/aspect_ratio))**2))
    if fl is not None:
        figure(figsize=(12,12/aspect_ratio))
    length_vs_p = sp.Integral(dline,(p,0,pmax))
    length_vs_p_fn = vectorize(
        sp.lambdify((phalf, pmax), # no longer depends on Emax!
                          length_vs_p,
                          modules=[{"Integral": integral_as_quad},'sympy']),
        excluded=[0])
    length_data = nddata(length_vs_p_fn(sim_phalf,p_array),[-1],['p']).setaxis('p',p_array)
    length_data.invinterp('p', linspace(0,length_data['p',-1].item(),p_steps))
    if fl is not None:
        fl.plot(f_fn(sim_Emax,sim_phalf,length_data.fromaxis('p')),'o',human_units = False)
    return length_data.fromaxis('p')
#}}}
#{{{ Older method of just generating a power list - works for concentrated samples but not great for dilute
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
        powers = r_[0 : max_power : 1j*lin_steps][1:]
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
            dB_settings[abs(10**(dB_settings / 10.0 - 3) - max_power * frac).argmin()]
            for frac in [0.75, 0.5, 0.25]
        ]
        dB_settings = append(dB_settings, append_dB)
    return dB_settings
#}}}
