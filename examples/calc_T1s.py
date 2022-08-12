from pyspecdata import *
import SpinCore_pp
config_dict = SpinCore_pp.configuration("active.ini")
vd_kwargs = {
    j: config_dict[j]
    for j in ["krho_cold", "krho_hot", "T1water_cold", "T1water_hot"]
    if j in config_dict.keys()
}
print((
    SpinCore_pp.vdlist_from_relaxivities(config_dict["concentration"], **vd_kwargs)
    * 1e6
))
quit()
