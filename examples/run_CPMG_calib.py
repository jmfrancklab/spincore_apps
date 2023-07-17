"""
CPMG_calibration
================
CPMG meant for the purpose of calibration.

FOR PHASE CYCLING: Provide both a phase cycle label (e.g.,
'ph1', 'ph2') as str and an array containing the indices
(i.e., registers) of the phases you which to use that are
specified in the numpy array 'tx_phases'.  Note that
specifying the same phase cycle label will loop the
corresponding phase steps together, regardless of whether
the indices are the same or not.
    e.g.,
    The following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph1',r_[2,3]),
    will provide two transients with phases of the two pulses (p1,p2):
        (0,2)
        (1,3)
    whereas the following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph2',r_[2,3]),
    will provide four transients with phases of the two pulses (p1,p2):
        (0,2)
        (0,3)
        (1,2)
        (1,3)
FURTHER: The total number of transients that will be
collected are determined by both nScans (determined when
calling the appropriate marker) and the number of steps
calculated in the phase cycle as shown above.  Thus for
nScans = 1, the SpinCore will trigger 2 times in the first
case and 4 times in the second case.  for nScans = 2, the
SpinCore will trigger 4 times in the first case and 8 times
in the second case.
"""
from pyspecdata import *
from numpy import *
from datetime import datetime
import SpinCore_pp
import h5py
raise RuntimeError("This pulse proram has not been updated.  Before running again, it should be possible to replace a lot of the code below with a call to the function provided by the 'generic' pulse program inside the ppg directory!")

fl = figlist_var()
p90_range = linspace(3.0, 4.0, 5)
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "CPMG_calib"
config_dict["date"] = date
config_dict["cpmg_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{set phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0, 2]
    nPhaseSteps = 2
if not phase_cycling:
    ph1_cyc = 0.0
    nPhaseSteps = 1
# }}}
#{{{making tau
marker = 1.0
pad_start = config_dict['tau_extra_us'] - config_dict["deadtime_us"]
pad_end = config_dict['tau_extra_us'] - config_dict["deblank_us"] - marker
assert (
    pad_start > 0
), "tau_extra_us must be set to more than deadtime and more than deblank!"
assert (
    pad_end > 0
), "tau_extra_us must be set to more than deadtime and more than deblank!"
twice_tau_echo_us = (  # the period between 180 pulses
    config_dict["tau_extra_us"] * 2 + config_dict["acq_time_ms"] * 1e3
)
#}}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
#{{{run ppg
for index, val in enumerate(p90_range):
    p90_us = val  # us
    config_dict['tau_us'] = twice_tau_echo_us / 2.0 - (
            2*p90
            /pi #evolution during pulse -- see eq 6 of coherence paper
            + config_dict['deadtime_us'] # following 90
            +config_dict['deblank_us'] #before 180
            )

    print("***")
    print("INDEX %d - 90 TIME %f" % (index, val))
    print("***")
    if index == 0:
        data = run_cpmg(
            nScans=config_dict["nScans"],
            indirect_idx=0,
            indirect_len=len(p90_range) + 1,
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            p90_us=p90_us,
            repetition_us=config_dict["repetition_us"],
            pad_start_us=pad_start,
            pad_end_us=pad_end,
            tau_us=tau_us,
            SW_kHz=config_dict["SW_kHz"],
            ph1_cyc=ph1_cyc,
            indirect_fields=('p90_idx','p90_us')
            ret_data=None,
        )
     p90_axis = data.getaxis('indirect')
     p90_axis[0]['p90_index'] = index
     p90_axis[0]['p90_us'] = p90
    else:
        run_cpmg(
            nScans=config_dict["nScans"],
            indirect_idx=index + 1,
            indirect_len=len(p90_range + 1),
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            p90_us=p90,
            repetition_us=config_dict["repetition_us"],
            pad_start_us=pad_start,
            pad_end_us=pad_end,
            tau_us=tau_us,
            SW_kHz=config_dict["SW_kHz"],
            ph1_cyc=ph1_cyc,
            ret_data=data,
        )
        p90_axis[index+1]['p90_us'] = p90
#}}}
#{{{Save data
data.chunk("t", ["ph1", "t2"], [len(ph1_cyc), -1])
data.setaxis("ph1", ph1_cyc / 4)
if config_dict["nScans"] > 1:
    data.setaxis("nScans", r_[0 : config_dict["nScans"]])
if phase_cycling:    
    fl.next("Raw - time")
    fl.image(
        data.C.mean("nScans"))
    data.reorder("t2", first=False)
    for_plot = data.C
    for_plot.ft('t2',shift=True)
    for_plot.ft(['ph1'], unitary = True)
    fl.next('FTed data')
    fl.image(for_plot.C.mean("nScans")
    )
else:
    if config_dict["nScans"] > 1:
        data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    data.rename('t','t2')
    fl.next("Raw - time")
    fl.image(
        data.C.mean("nScans"))
    data.reorder("t2", first=False)
    for_plot = data.C
    for_plot.ft('t2',shift=True)
    fl.next('FTed data')
    fl.image(for_plot)
data.name(config_dict["type"] + "_" + config_dict["cpmg_counter"])
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
            print("this nodename already exists, so I will call it temp_cpmg_calib")
            data.name("temp_cpmg_calib")
            nodename = "temp_cpmg_calib"
    data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_cpmg_calib.h5 in the current directory"
        )
        if os.path.exists("temp_cpmg_echo.h5"):
            print("there is a temp_cpmg_calib.h5 already! -- I'm removing it")
            os.remove("temp.h5")
            data.hdf5_write("temp.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", data.name())
config_dict.write()
fl.show()
