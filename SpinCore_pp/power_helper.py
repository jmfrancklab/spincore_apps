from numpy import *

"Helper functions for dealing with powers"


def gen_powerlist(max_power, steps, min_dBm_step=0.5, three_down=False):
    """generate a list of (roughly) evenly spaced powers up
    to max_power

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
