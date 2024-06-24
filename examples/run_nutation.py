"""
Nutation
========

A standard echo where the 90 time is varied so 
that we are able to see when the signal rotates through 90 to 
180 degrees.
"""
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp import get_integer_sampling_intervals
from Instruments.XEPR_eth import xepr
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
import h5py

fl = figlist_var()
p90_range_us = linspace(1.0, 10.0, 20, endpoint=False)
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints, config_dict['SW_kHz'], config_dict['acq_time_ms'] = get_integer_sampling_intervals(config_dict['SW_kHz'], config_dict['acq_time_ms'])
my_exp_type = "ODNP_NMR_comp/nutation"
target_directory = getDATADIR(exp_type=my_exp_type)
assert os.path.exists(target_directory)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "nutation"
config_dict["date"] = date
config_dict["echo_counter"] += 1
filename = (
    f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
)
# }}}
# {{{let computer set field
print(
    "I'm assuming that you've tuned your probe to:,
    config_dict["carrierFreq_MHz"],
    "since that's what's in your .ini file",
)
field_G = config_dict["carrierFreq_MHz"] / config_dict["gamma_eff_MHz_G"]
print(
    "Based on that, and the gamma_eff_MHz_G you have in your .ini file, I'm setting the field to %f"
    % field_G
)
with xepr() as x:
    assert field_G < 3700, "are you crazy??? field is too high!"
    assert field_G > 3300, "are you crazy?? field is too low!"
    field_G = x.set_field(field_G)
    print("field set to ", field_G)
# }}}
# {{{set phase cycling
ph1_cyc = r_[0, 1, 2, 3]
nPhaseSteps = 4
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
nutation_data = None
for idx, p90_us in enumerate(p90_range_us):
    run_spin_echo(
        nScans=config_dict["nScans"],
        indirect_idx=idx,
        indirect_len=len(p90_range_us),
        ph1_cyc=ph1_cyc,
        amplitude=config_dict["amplitude"],
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        nEchoes=config_dict["nEchoes"],
        p90_us=p90_us,
        repetition_us=config_dict["repetition_us"],
        tau_us=config_dict["tau_us"],
        SW_kHz=config_dict["SW_kHz"],
        indirect_fields=("p_90", "index"),
        ret_data=nutation_data,
    )
# {{{ for some reason, axis coordinates were
#     given as a structured array with p90
#     and index fields, so I'm staying
#     consistent
mytimes = nutation_data.getaxis("indirect")
mytimes["p_90"][:] = p90_range_us
mytimes["index"][:] = arange(len(p90_range_us))
# }}}
# {{{ chunk and save data
nutation_data.set_prop("postproc_type", "spincore_nutation_v1")
nutation_data.set_prop("coherence_pathway", {"ph1": +1})
nutation_data.set_prop("acq_params", config_dict.asdict())
nutation_data.name(config_dict["type"] + "_" + str(config_dict["echo_counter"]))
nutation_data.chunk(
        "t", 
        ["ph1", "t2"], 
        [4, -1]
)
nutation_data.labels(
    {
        "ph1": r_[0 : len(ph1_cyc)]
    }
)
nutation_data.setaxis("ph1", ph1_cyc / 4)
if config_dict["nScans"] > 1:
    nutation_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
nutation_data.reorder(["ph1", "nScans", "t2"])
filename_out = filename + ".h5"
nodename = nutation_data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_nutation")
            nutation_data.name("temp_nutation")
            nodename = "temp_nutation"
    nutation_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        nutation_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_nutation.h5 in the current directory"
        )
        if os.path.exists("temp_nutation.h5"):
            print("there is a temp_nutation.h5 already! -- I'm removing it")
            os.remove("temp_nutation.h5")
        nutation_data.hdf5_write("temp_nutation.h5")
        print(
            "if I got this far, that probably worked -- be sure to move/rename temp_nutation.h5 to the correct name!!"
        )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print("saved data to (node, file, exp_type):", nutation_data.name(), filename_out, my_exp_type)
config_dict.write()
nutation_data.ft("t2", shift=True)
fl.next("image - ft")
fl.image(nutation_data)
fl.next("image - ft, coherence")
nutation_data.ft("ph1")
fl.image(nutation_data)
fl.show()
