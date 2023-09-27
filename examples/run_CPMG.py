"""
CPMG
====

This script will perform a standard CPMG experiment. 
In order to form a symmetric echo, a padding time is added before 
and after your tau. 
"""
from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp
from SpinCore_pp.ppg import generic
import os
from datetime import datetime
import h5py

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict['acq_time_ms'] * config_dict['SW_kHz'] + 0.5)
config_dict['acq_time_ms'] = nPoints / config_dict['SW_kHz']
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "CPMG"
config_dict["date"] = date
config_dict["cpmg_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{set phase cycling
phase_cycling = True
if phase_cycling:
    Nph_overall = r_[0,1,2,3]
    Nph_diff = r_[0,2]
    ph1_cyc = array([(j+k)%4 for k in Nph_overall for j in Nph_diff])
    ph2_cyc = array([(k+1)%4 for k in Nph_overall for j in Nph_diff])
    nPhaseSteps = len(Nph_overall) * len(Nph_diff)
if not phase_cycling:
    ph1_cyc = 0.0
    ph2_cyc = 0.0
    Nph_overall = r_[0]
    Nph_diff = r_[0]
    nPhaseSteps = 1
# }}}
# {{{symmetric tau
marker = 1.0
jumpto = 1.0
tau_evol = 2*config_dict['p90_us']/pi #evolution during pulse -- see eq 6 of coherence paper
pad_end = config_dict['deadtime_us'] - config_dict['deblank_us'] - marker - jumpto
twice_tau_echo_us = config_dict['acq_time_ms'] + (2 * config_dict['deadtime_us'])# the period between end of first 180 pulse and start of next
config_dict["tau_us"] = twice_tau_echo_us / 2.0 - tau_evol - config_dict['deblank_us']
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps * config_dict['nEchoes']
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
# {{{run cpmg
data = generic(
        ppg_list = [
                ("marker","start",1),
                ("phase_reset", 1),
                ("delay_TTL", config_dict['deblank_us']),
                ("pulse_TTL", config_dict['p90_us'], "ph_cyc", ph1_cyc),
                ("delay", tau_us),
                ("delay_TTL", config_dict['deblank_us']),
                ("pulse_TTL", 2.0 * config_dict['p90_us'], "ph_cyc", ph2_cyc),
                ("delay", config_dict['deadtime_us']),
                ("acquire", acq),
                ("delay", pad_end),
                ("delay",1.0), #matching the jumpto delay
                ("marker", "echo_label", (config_dict['nEchoes'] - 1)), 
                ("delay_TTL", config_dict['deblank_us']),
                ("pulse_TTL", 2.0 * config_dict['p90_us'], "ph_cyc",ph2_cyc),
                ("delay", config_dict['deadtime_us']),
                ("acquire", acq),
                ("delay", pad_end),
                ("jumpto", "echo_label"), 
                ("delay", config_dict['repetition_us']),
                ("jumpto","start")
            ],
        nScans = config_dict["nScans"],
        indirect_idx = 0,
        indirect_len = len(config_dict['nEchoes']),
        adcOffset = config_dict["adc_offset"],
        carrierFreq_MHz = config_dict["carrierFreq_MHz"],
        nPoints = nPoints,
        SW_kHz = config_dict["SW_kHz"],
        ret_data = None,
    )
# }}}
# {{{ chunk and save data
data.chunk("t", ["ph_overall", "ph_diff", "tE", "t2"], [len(Nph_overall), len(Nph_diff), config_dict["nEchoes"], nPoints])
data.setaxis("ph_overall", Nph_overall / len(Nph_overall))
data.setaxis("ph_diff", Nph_diff / len(Nph_diff))
data.name(config_dict["type"] + "_" + config_dict["cpmg_counter"])
data.set_prop("postproc_type", "spincore_CPMGv2")
data.set_prop("acq_params", config_dict.asdict())
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/CPMG")
filename_out = filename + ".h5"
nodename = data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_cpmg")
            data.name("temp_cpmg")
            nodename = "temp_cpmg"
    data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_cpmg.h5 in the current h5 file"
        )
        if os.path.exists("temp_cpmg.h5"):
            print("there is a temp_cpmg.h5 already! -- I'm removing it")
            os.remove("temp_cpmg.h5")
            data.hdf5_write("temp_cpmg.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_cpmg.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", data.name()))
config_dict.write()
#{{{ Image raw data
fl.next("Raw - time")
fl.image(data)
data.reorder("t2", first=False)
for_plot = data.C
for_plot.ft('t2',shift=True)
for_plot.ft(['ph_overall','ph_diff'], unitary = True)
fl.next('FTed data')
fl.image(for_plot)
fl.show()
#}}}
