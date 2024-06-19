# Use echo acq time instead of acq_time_ms
from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp
from SpinCore_pp import prog_plen
from SpinCore_pp.ppg import generic
import os
from datetime import datetime
import h5py
from Instruments.XEPR_eth import xepr
fl = figlist_var()
#{{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["echo_acq_ms"] * config_dict["SW_kHz"] + 0.5)
target_directory = getDATADIR(exp_type = 'ODNP_NMR_comp/Echoes')
config_dict['echo_acq_ms'] = nPoints/config_dict['SW_kHz']
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "echo"
config_dict["date"] = date
config_dict["cpmg_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_generic_{config_dict['type']}"
# }}}
#{{{let computer set field
print("I'm assuming that you've tuned your probe to",
        config_dict['carrierFreq_MHz'],
        "since that's what's in your .ini file",
        )
Field = config_dict['carrierFreq_MHz']/config_dict['gamma_eff_MHz_G']
print(
        "Based on that, and the gamma_eff_MHz_G you have in your .ini file, I'm setting the field to %f"
        %Field
        )
with xepr() as x:
    assert Field < 3700, "are you crazy??? field is too high!"
    assert Field > 3300, "are you crazy?? field is too low!"
    Field = x.set_field(Field)
    print("field set to ",Field)
#}}}
#{{{set phase cycling
phase_cycling = True
if phase_cycling:
    ph_overall = r_[0,1,2,3]
    ph_diff = r_[0,2]
    ph1_cyc = array([(j + k) % 4 for k in ph_overall for j in ph_diff])
    ph2_cyc = array([(k + 1) % 4 for k in ph_overall for j in ph_diff])
    nPhaseSteps = len(ph_overall) * len(ph_diff)
if not phase_cycling:
    nPhaseSteps = 1
# }}}    
prog_p90_us = prog_plen(config_dict['p90_us'])
prog_p180_us = prog_plen(2*config_dict['p90_us'])
# {{{check total points
total_pts = nPoints * nPhaseSteps# * config_dict['nEchoes']
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
# }}}
# {{{basic phasecycling
data = generic(
    ppg_list=[
        ("phase_reset", 1),
        ("delay_TTL", config_dict["deblank_us"]),
        ("pulse_TTL", prog_p90_us, "ph_cyc", ph1_cyc),
        ("delay", config_dict["tau_us"]),
        ("delay_TTL", config_dict["deblank_us"]),
        ("pulse_TTL", prog_p180_us, "ph_cyc", ph2_cyc),
        ("delay", config_dict["deadtime_us"]),
        ("acquire", config_dict["echo_acq_ms"]),
        ("delay", config_dict["repetition_us"]),
    ],
    nScans=config_dict["nScans"],
    indirect_idx=0,
    indirect_len=config_dict["nEchoes"],
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    acq_time_ms=config_dict["echo_acq_ms"],
    SW_kHz=config_dict["SW_kHz"],
    ret_data=None,
)
## {{{ chunk and save data
data.set_prop('postproc_type','proc_Hahn_echoph')
data.set_prop("acq_params", config_dict.asdict())
data.name(config_dict["type"] + "_" + str(config_dict["cpmg_counter"]))
data.chunk(
    "t", 
    ["ph_overall", "ph_diff", "nEcho", "t2"], 
    [len(ph_overall),len(ph_diff),int(config_dict['nEchoes']),-1])
data.labels({"nEcho":r_[0:int(config_dict['nEchoes'])],
    "ph_overall":r_[0:len(ph_overall)],
    "ph_diff":r_[0:len(ph_diff)]
    }
    )
data.setaxis('ph_overall',ph_overall/4)
data.setaxis('ph_diff',ph_diff/4)
# }}}
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/Echoes")
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

