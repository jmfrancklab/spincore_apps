from pyspecdata import *
from SpinCore_pp.power_helper import Ep_spacing_from_phalf
from SpinCore_pp.config_parser_fn import configuration
import matplotlib.pyplot as plt

config_dict = configuration("active.ini")
with figlist_var() as fl:
    Ep_powers = Ep_spacing_from_phalf(
        est_phalf=config_dict["guessed_phalf"] / 4,
        max_power=config_dict["max_power"],
        p_steps=config_dict["power_steps"],
        min_dBm_step=config_dict["min_dBm_step"],
        fl=fl,
    )
    plt.title("Evenly spaced Ep curve")
    plt.ylabel("Signal")
    plt.xlabel("Power / W")
    print("The list with the optimal powers for this E(p) experiment is", Ep_powers)
