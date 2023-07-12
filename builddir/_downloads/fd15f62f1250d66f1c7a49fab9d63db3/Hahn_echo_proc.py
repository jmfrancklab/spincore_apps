"This example was a precursor to the GUI function.  Once GUI part of the master branch, probably delete this."
from pylab import *
from pyspecdata import *
import SpinCore_pp
from datetime import datetime

with figlist_var() as fl:
    config_dict = SpinCore_pp.configuration("active.ini")
    config_dict["type"] = "echo"
    # we do not load the date here, because this is designed to be run
    # immediately after an echo program, which would have written the date --
    # also, if we wnat to look at a different date, we just change it in the
    # config file
    filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
    d = find_file(
        filename,
        exp_type="ODNP_NMR_comp/Echoes",
        expno=config_dict["type"] + "_" + str(config_dict["echo_counter"]),
    )
    assert (
        d.get_units("t2") is not None
    ), "bad data file!  units of s for t2 should be stored in nddata!"
    d.ft("ph1", unitary=True)
    if "nScans" in d.dimlabels:
        d.mean("nScans")
    d.ft("t2", shift=True)
    # {{{ show raw data with peak pick
    fl.next("raw ft")
    for j in d.getaxis("ph1"):
        fl.plot(abs(d["ph1":j]), label=f"Δp={j}", alpha=0.5)
    centerfrq = abs(d["ph1", +1]).argmax("t2").item()
    axvline(x=centerfrq / 1e3, ls=":", color="r", alpha=0.25)
    # }}}
    d_fullsw = d.C
    fl.next("zoomed")
    for j in d.getaxis("ph1"):
        fl.plot(
            abs(d["ph1":j]["t2" : tuple(r_[-3e3, 3e3] + centerfrq)]),
            label=f"Δp={j}",
            alpha=0.5,
        )
    noise = d["ph1", r_[0, 2, 3]]["t2":centerfrq].run(std, "ph1")
    signal = abs(d["ph1", r_[0, 2, 3]]["t2":centerfrq])
    assert signal > 3 * noise
    d = d["t2" : tuple(r_[-3e3, 3e3] + centerfrq)]
    d.ift("t2")
    fl.next("time domain, filtered")
    filter_timeconst = 10e-3
    myfilter = exp(
        -abs((d.fromaxis("t2") - config_dict["tau_us"] * 1e-6)) / filter_timeconst
    )
    for j in d.getaxis("ph1"):
        fl.plot(abs(d["ph1":j]), label=f"Δp={j}", alpha=0.5)
    fl.plot(myfilter * abs(d["ph1", 1]["t2" : config_dict["tau_us"] * 1e-6]))
    # {{{ show filtered data with peak pick
    d = d_fullsw
    d.ift("t2")
    d *= exp(-abs((d.fromaxis("t2") - config_dict["tau_us"] * 1e-6)) / filter_timeconst)
    d.ft("t2")
    fl.next("apodized ft")
    for j in d.getaxis("ph1"):
        fl.plot(abs(d["ph1":j]), label=f"Δp={j}", alpha=0.5)
    centerfrq = abs(d["ph1", +1]).argmax("t2").item()
    axvline(x=centerfrq / 1e3, ls=":", color="r", alpha=0.25)
    # }}}
    Field = config_dict["carrierFreq_MHz"] / config_dict["gamma_eff_MHz_G"]
    config_dict["gamma_eff_MHz_G"] -= centerfrq * 1e-6 / Field
    config_dict.write()
