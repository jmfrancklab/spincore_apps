"""Run Inversion Recovery at set power
======================================
You will need to manually set the power manually with FLInst setfield and the B12. Once the power is set and the parameters are adjusted, you can run this program to collect the inversion recovery dataset at the set power.
"""
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import run_IR
from datetime import datetime
import h5py

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "IR"
config_dict["date"] = date
config_dict["IR_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{set phase cycling
phase_cycling = True
if phase_cycling:
    ph1 = r_[0, 2]
    ph2 = r_[0, 2]
    nPhaseSteps = 4
if not phase_cycling:
    ph1 = 0.0
    ph2 = 0.0
    nPhaseSteps = 1
# {{{make vd list
vd_kwargs = {
    j: config_dict[j]
    for j in ["krho_cold", "krho_hot", "T1water_cold", "T1water_hot"]
    if j in config_dict.keys()
}
vd_list_us = (
    SpinCore_pp.vdlist_from_relaxivities(config_dict["concentration"], **vd_kwargs)
    * 1e6
)  # put vd list into microseconds
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
# {{{run IR
vd_data = None
for vd_idx, vd in enumerate(vd_list_us):
    vd_data = run_IR(
        nScans=config_dict["nScans"],
        indirect_idx=vd_idx,
        indirect_len=len(vd_list_us),
        ph1_cyc=ph1,
        ph2_cyc=ph2,
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        nEchoes=config_dict["nEchoes"],
        vd=vd,
        p90_us=config_dict["p90_us"],
        repetition_us=config_dict["repetition_us"],
        tau_us=config_dict["tau_us"],
        SW_kHz=config_dict["SW_kHz"],
        ret_data=vd_data,
    )
# }}}
# {{{ chunk and save data
if phase_cycling:    
    vd_data.chunk("t", ["ph2", "ph1", "t2"], [len(ph1), len(ph2), -1])
    vd_data.setaxis("ph1", ph1 / 4)
    vd_data.setaxis("ph2", ph2 / 4)
    if config_dict['nScans'] > 1:
        vd_data.setaxis('nScans',[0:config_dict['nScans']])
    vd_data.reorder(["ph1", "ph2", "vd", "t2"])
    vd_data.squeeze()
    vd.data.set_uits("t2","s")
    fl.next("Raw - time")
    fl.image(vd_data)
    for_plot = vd_data.C
    for_plot.ft('t2')
    for_plot.ft(['ph1','ph2'],unitary = True)
    fl.next('FTed data')
    fl.image(for_plot)
else:
    if config_dict["nScans"] > 1:
        vd_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    vd_data.rename("t", "t2")
    fl.next("Raw - time")
    fl.image(
        vd_data.C.mean("nScans"))
    vd_data.reorder("t2", first=False)
    for_plot = vd_data.C
    for_plot.ft('t2',shift=True)
    fl.next('FTed data')
    fl.image(for_plot)
vd_data.name(config_dict["type"] + "_" + str(config_dict["ir_counter"]))
vd_data.set_prop("postproc_type", "Spincore_IR_v1")
vd_data.set_prop("acq_params", config_dict.asdict())
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/inv_rec")
filename_out = filename + ".h5"
nodename = vd_data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_IR")
            vd_data.name("temp_IR")
            nodename = "temp_IR"
    vd_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        vd_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_IR.h5 in the current directory"
        )
        if os.path.exists("temp_IR.h5"):
            print("there is a temp_IR.h5 already! -- I'm removing it")
            os.remove("temp_IR.h5")
            echo_data.hdf5_write("temp_IR.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_IR.h5 to the correct name!!"
            )
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_IR.h5 in the current directory"
        )
        if os.path.exists("temp_IR.h5"):
            print("there is a temp_IR.h5 -- I'm removing it")
            os.remove("temp_IR.h5")
        vd_data.hdf5_write("temp_IR.h5")
        print(
            "if I got this far, that probably worked -- be sure to move/rename temp_IR.h5 to the correct name!!"
        )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", vd_data.name()))
config_dict.write()
fl.show()
