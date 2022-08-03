from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
import configparser

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "nutation"
config_dict["date"] = f"{date}"
config_dict["echo_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}

# {{{ Edit here to set the actual field
set_field = False
if set_field:
    B0 = (
        config_dict["carrierFreq_MHz"] / config_dict["gamma_eff_MHz_G"]
    )  # Determine this from Field Sweep
    thisB0 = xepr().set_field(B0)
# }}}
# {{{phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0, 1, 2, 3]
    ph2_cyc = r_[0, 2]
    nPhaseSteps = 8
if not phase_cycling:
    ph1_cyc = r_[0]
    ph2_cyc = r_[0]
    nPhaseSteps = 1
# }}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
p90_range_us = linspace(1.0, 15.0, 5, endpoint=False)
for index, val in enumerate(p90_range_us):
    p90_us = val  # us
    print("***")
    print("INDEX %d - 90 TIME %f" % (index, val))
    print("***")
    nutation_data = run_spin_echo(
        nScans=config_dict["nScans"],
        indirect_idx=0,
        indirect_len=len(p90_range_us),
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        nEchoes=config_dict["nEchoes"],
        p90_us=p90_us,
        repetition=config_dict["repetition_us"],
        tau_us=config_dict["tau_us"],
        SW_kHz=config_dict["SW_kHz"],
        output_name=filename,
        ret_data=None,
    )
SpinCore_pp.stopBoard()
nutation_data.set_prop("acq_params", config_dict.asdict())
print("EXITING...\n")
print("\n*** *** ***\n")
nutation_data.name(config_dict["type"])
nutation_data.chunk("t", ["ph2", "ph1", "t2"], [len(ph2_cyc), len(ph1_cyc), -1])
nutation_data.setaxis("ph2",ph2_cyc)
nutation_data.setaxis("ph1",ph1_cyc)
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/nutation")
filename_out = filename + ".h5"
nodename = nutation_data.name()
if os.path.exists(filename + ".h5"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp")
            nutation_data.name("temp")
            nodename = "temp"
    nutation_data.hdf5_write(f"{filename_out}/{nodename}", directory=target_directory)
else:
    nutation_data.hdf5_write(filename + ".h5", directory=target_directory)
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", nutation_data.name()))
print(("Shape of saved data", ndshape(nutation_data)))
config_dict.write()
fl.next("raw data")
fl.image(nutation_data)
nutation_data.ft("t", shift=True)
fl.next("FT raw data")
fl.image(nutation_data)
fl.show()
