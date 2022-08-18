from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
import h5py
from Instruments.XEPR_eth import xepr
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime

fl = figlist_var()
p90_range_us = linspace(1.0, 15.0, 5, endpoint=False)
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
nutation_data = run_spin_echo(
    nScans=config_dict["nScans"],
    indirect_idx=0,
    indirect_len=len(p90_range_us),
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    nEchoes=config_dict["nEchoes"],
    p90_us=p90_us[0],
    ph1_cyc = ph1_cyc,
    ph2_cyc = ph2_cyc,
    repetition=config_dict["repetition_us"],
    tau_us=config_dict["tau_us"],
    SW_kHz=config_dict["SW_kHz"],
    output_name=filename,
    ret_data=None,
)
for index, val in enumerate(p90_range_us[1:]):
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
        ph1_cyc = ph1_cyc,
        ph2_cyc = ph2_cyc,
        output_name=filename,
        ret_data=nutation_data,
    )
nutation_data.set_prop("acq_params", config_dict.asdict())
nutation_data.name(config_dict["type"]+'_'+config_dict['echo_counter'])
nutation_data.chunk("t", ["ph2", "ph1", "t2"], [len(ph2_cyc), len(ph1_cyc), -1])
nutation_data.setaxis("ph2", ph2_cyc)
nutation_data.setaxis("ph1", ph1_cyc)
nutation_data.setaxis('nScans',config_dict['nScans'])
fl.next("raw data")
fl.image(nutation_data)
nutation_data.ft("t2", shift=True)
fl.next("FT raw data")
fl.image(nutation_data)
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
        nutation_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        nutation_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp.h5 in the current directory"
        )
        if os.path.exists("temp.h5"):
            print("there is a temp.h5 already! -- I'm removing it")
            os.remove("temp.h5")
            nutation_data.hdf5_write("temp.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", nutation_data.name()))
print(("Shape of saved data", ndshape(nutation_data)))
config_dict.write()
fl.show()
