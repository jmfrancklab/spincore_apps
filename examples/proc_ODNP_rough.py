"""
An example of rough processing for ODNP -- this is designed to automatically pull the last dataset acquired.

For an example of how this works, if you have *not* just run a dataset, set the following key/values in your active.ini:
```
[sample]
....
```
"""
from numpy import empty
import pylab as plt
import h5py, time
from pyspecdata import *
from matplotlib.ticker import FuncFormatter
import matplotlib.transforms as transforms
from dateutil import parser
from datetime import timedelta
import SpinCore_pp

time_origin = parser.parse("0:00")


@FuncFormatter
def thetime(x, position):
    return (time_origin + timedelta(seconds=x)).strftime("%H:%M:%S")


with figlist_var() as fl:
    config_dict = SpinCore_pp.configuration("active.ini")
    config_dict["type"] = "ODNP"
    filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}_{config_dict['odnp_counter']}"
    Ep = find_file(
        filename,
        exp_type="ODNP_NMR_comp/ODNP",
        expno='enhancement'),
    assert Ep.get_units("t2") is not None, "bad data file!  units of s for t2 should be stored in nddata!"
    Ep.rename('indirect','power')
    Ep.reorder(['ph1','power'])
    if nScans in Ep.dimlabels:
        Ep.mean("nScans")
    fl.next("raw Ep")
    fl.image(Ep)
    Ep.ft(["ph1"], unitary=True)
    Ep.ft("t2", shift=True)
    fl.next("FTed Ep")
    fl.image(Ep)
    all_nodes = find_file(filename, exp_type="ODNP_NMR_comp/ODNP", return_list=True)
    IR_nodenames = [j for j in all_nodes if "IR" in j]
    for (j, nodename) in enumerate(IR_nodenames):
        IR = find_file(
            filename,
            exp_type="ODNP_NMR_comp/ODNP",
            expno=nodename,
            postproc=IR_postproc,
            lookup=lookup_table,
        )
        IR.reorder(["ph1", "ph2", "nScans", "vd", "t2"])
        fl.next("Raw phase cycling - time -- %s" % nodename)
        fl.image(IR.C.mean("nScans"))
        IR.ft("t2", shift=True)
        fl.next("phase cycling - freq - %s" % nodename)
        fl.image(IR.C.mean("nScans"))
        IR.ft(["ph1", "ph2"], unitary=True)
        fl.next("Raw DCCT  -- %s" % nodename)
        fl.image(IR.C.mean("nScans"))
