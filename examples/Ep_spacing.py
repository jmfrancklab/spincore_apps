from pyspecdata import *
import SpinCore_pp
#config_dict = SpinCore_pp.configuration("active.ini")
with figlist_var() as fl:
    Ep_powers = gen_Ep_powers(sim_phalf = 0.2, sim_Emax = 10.0, sim_pmax = 3.16,
            aspect_ratio = 1.618, p_steps = 15,fl=fl)
    fl.show()
