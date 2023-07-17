from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
import h5py
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
from Instruments.XEPR_eth import xepr
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/nutation")
fl = figlist_var()
p90_range = linspace(3.,15.,25,endpoint=False)
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
#{{{ make tqu and phase cycling
marker = 1.0
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0,2]
    nPhaseSteps = 2
else:
    ph1_cyc = 0.0
    nPhaseSteps = 1.0
data_length = 2*nPoints*config_dict['nEchoes']*nPhaseSteps
# these are unique to the nutation aspect of it
pad_start = config_dict["tau_extra_us"] - config_dict["deadtime_us"]
pad_end = (
    config_dict["tau_extra_us"] - config_dict["deblank_us"] - marker
)  # marker + deblank
assert (
    pad_start > 0
), "tau_extra_us must be set to more than deadtime and more than deblank!"
assert (
    pad_end > 0
), "tau_extra_us must be set to more than deadtime and more than deblank!"
twice_tau_range = config_dict['deblank_us'] + 2*p90_range + config_dict['deadtime_us'] + pad_start + config_dict['acq_time_ms']*1e3 + pad_end + marker
tau1_range = twice_tau_range/2.0

assert (len(p90_range) == len(twice_tau_range) == len(tau1_range)), "Your axis of 90 times must be the same length as the twice tau and tau1 axes"
#}}}
#{{{ run ppg

nutation_data =generic(
    ppg_list=[
        ("phase_reset", 1),
        ("delay_TTL", config_dict["deblank_us"]),
        ("pulse_TTL", p90_range[0], "ph1", ph1_cyc),
        ("delay", tau1_range[0]),
        ("delay_TTL", config_dict["deblank_us"]),
        ("pulse_TTL", 2.0 * p90_range[0], 0.0),
        ("delay", config_dict["deadtime_us"]),
        ("delay", pad_start_us),
        ("acquire", config_dict["acq_time_ms"]),
        ("delay", pad_end_us),
        ("marker", "echo_label", (config_dict["nEchoes"] - 1)),  # 1 us delay
        ("delay_TTL", config_dict["deblank_us"]),
        ("pulse_TTL", 2.0 * p90_range[0], 0.0),
        ("delay", config_dict["deadtime_us"]),
        ("delay", pad_start_us),
        ("acquire", config_dict["acq_time_ms"]),
        ("delay", pad_end_us),
        ("jumpto", "echo_label"),  # 1 us delay
        ("delay", config_dict["repetition_us"]),
    ],
    nScans=config_dict["nScans"],
    indirect_idx=0,
    indirect_len=len(p90_range),
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    SW_kHz=config_dict["SW_kHz"],
    indirect_fields = ('p90','tau1'),
    ret_data=None,
)
nutation_axis = nutation_data.getaxis('indirect')
nutation_axis[0]['p90'] = p90_range[0]
nutation_axis[0]['tau1'] = tau1_range[0]
for index,val in enumerate(p90_range[1:]):
    p90 = val # us
    tau1 = tau1_range[index+1]
    nutation_axis[index+1]['p90'] = p90
    nutation_axis[index+1]['tau'] = tau1
    nutation_data = generic(
            ppg_list=[
                ("phase_reset", 1),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", p90_range[0], "ph1", ph1_cyc),
                ("delay", tau1),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * p90, 0.0),
                ("delay", config_dict["deadtime_us"]),
                ("delay", pad_start_us),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", pad_end_us),
                ("marker", "echo_label", (config_dict["nEchoes"] - 1)),  # 1 us delay
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * p90, 0.0),
                ("delay", config_dict["deadtime_us"]),
                ("delay", pad_start_us),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", pad_end_us),
                ("jumpto", "echo_label"),  # 1 us delay
                ("delay", config_dict["repetition_us"]),
            ],
            nScans=config_dict["nScans"],
            indirect_idx=index+1,
            indirect_len=len(p90_range),
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            SW_kHz=config_dict["SW_kHz"],
            indirect_fields = ('p90','tau1'),
            ret_data=nutation_data)
if phase_cycling:
    nutation_data.chunk('t',['ph1','t2'],[len(ph1_cyc),-1])
    nutation_data.setaxis('ph1',ph1_cyc/4)
else:
    nutation_data.rename('t','t2')
if config_dict['nScans'] > 1:
    nutation_data.setaxis('nScans',r_[0:config_dict['nScans']])
nutation_data.reorder(['ph1','nScans','t2'])    
nutation_data.name(config_dict['type'] + '_' +config_dict['echo_counter'])
nutation_data.setprop('acq_params',config_dict.asdict())
#}}}
#{{{ save
nodename = nutation_data.name()
filename_out = filename +'.h5'
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/nutation")
filename_out = filename + ".h5"
nodename = nutation_data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_nutation_CPMG")
            nutation_data.name("temp_nutation_CPMG")
            nodename = "temp_nutation_CPMG"
        nutation_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        nutation_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_nutation_CPMG.h5 in the current directory"
        )
        if os.path.exists("temp_nutation_CPMG.h5"):
            print("there is a temp_nutation_CPMG.h5 already! -- I'm removing it")
            os.remove("temp_nutation_CPMG.h5")
            nutation_data.hdf5_write("temp_nutation_CPMG.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_nutation_CPMG.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", nutation_data.name()))
config_dict.write()
fl.show
