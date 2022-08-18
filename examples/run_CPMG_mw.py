# {{{ note on phase cycling
"""
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
# }}}
from pylab import *
from pyspecdata import *
from numpy import *
import os
import SpinCore_pp
from Instruments import Bridge12, prologix_connection, gigatronics
from datetime import datetime
import time

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "cpmg_mw"
config_dict["date"] = date
config_dict["cpmg_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{power settings
dB_settings = gen_powerlist(config_dict["max_power"], config_dict["power_steps"])
append_dB = [
    dB_settings[
        abs(10 ** (dB_settings / 10.0 - 3) - config_dict["max_power"] * frac).argmin()
    ]
    for frac in [0.75, 0.5, 0.25]
]
dB_settings = append(dB_settings, append_dB)
print("dB_settings", dB_settings)
print("correspond to powers in Watts", 10 ** (dB_settings / 10.0 - 3))
input("Look ok?")
powers = 1e-3 * 10 ** (dB_settings / 10.0)
# }}}
# {{{make better tau
marker = 1.0
tau_extra = 5000.0  # us, must be more than deadtime and more than deblank
pad_start = tau_extra - config_dict["deadtime_us"]
pad_end = tau_extra - config_dict["deblank_us"] * 2  # marker + deblank
twice_tau = (
    config_dict["deblank_us"]
    + 2 * config_dict["p90_us"]
    + config_dict["deadtime_us"]
    + pad_start
    + config_dict["acq_time_ms"] * 1e3
    + pad_end
    + marker
)
tau_us = twice_tau / 2.0
config_dict["tau_us"] = tau_us
# }}}
# {{{phase cycling
nPhaseSteps = 2
ph1_cyc = r_[0, 2]
# NOTE: Number of segments is nEchoes * nPhaseSteps
# }}}
# {{{run CPMG
cpmg_data = run_cpmg(
    nScans=config_dict["nScans"],
    indirect_idx=0,
    indirect_len=len(powers) + 1,
    ph1_cyc=ph1_cyc,
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    nEchoes=config_dict["nEchoes"],
    p90_us=config_dict["p90_us"],
    repetition_us=config_dict["repetition_us"],
    pad_start_us=pad_start,
    pad_end_us=pad_end,
    tau_us=config_dict["tau_us"],
    SW_kHz=config_dict["SW_kHz"],
    output_name=filename,
    ret_data=None,
)
# raw_input("CONNECT AND TURN ON BRIDGE12...")
with Bridge12() as b:
    b.set_wg(True)
    b.set_rf(True)
    b.set_amp(True)
    this_return = b.lock_on_dip(ini_range=(9.815e9, 9.83e9))
    dip_f = this_return[2]
    print("Frequency", dip_f)
    b.set_freq(dip_f)
    meter_powers = zeros_like(dB_settings)
    for j, this_power in enumerate(dB_settings):
        print("\n*** *** *** *** ***\n")
        print(
            "SETTING THIS POWER", this_power, "(", dB_settings[j - 1], powers[j], "W)"
        )
        if j > 0 and this_power > last_power + 3:
            last_power += 3
            print("SETTING TO...", last_power)
            b.set_power(last_power)
            time.sleep(3.0)
            while this_power > last_power + 3:
                last_power += 3
                print("SETTING TO...", last_power)
                b.set_power(last_power)
                time.sleep(3.0)
            print("FINALLY - SETTING TO DESIRED POWER")
            b.set_power(this_power)
        elif j == 0:
            threshold_power = 10
            if this_power > threshold_power:
                next_power = threshold_power + 3
                while next_power < this_power:
                    print("SETTING To...", next_power)
                    b.set_power(next_power)
                    time.sleep(3.0)
                    next_power += 3
            b.set_power(this_power)
        else:
            b.set_power(this_power)
        time.sleep(15)
        with prologix_connection() as p:
            with gigatronics(prologix_instance=p, address=7) as g:
                meter_powers[j] = g.read_power()
                print("POWER READING", meter_powers[j])
        run_cpmg(
            nScans=config_dict["nScans"],
            indirect_idx=j + 1,
            indirect_len=len(powers) + 1,
            ph1_cyc=ph1_cyc,
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            p90_us=config_dict["p90_us"],
            repetition_us=config_dict["repetition_us"],
            pad_start_us=pad_start,
            pad_end_us=pad_end,
            tau_us=config_dict["tau_us"],
            SW_kHz=config_dict["SW_kHz"],
            output_name=filename,
            ret_data=cpmg_data,
        )
        last_power = this_power
# }}}
# {{{save and show data
cpmg_data.set_prop("acq_params", config_dict.asdict()
cpmg_data.name(config_dict["type"] + "_" + config_dict["cpmg_counter"])
cpmg_data.chunk("t", ["ph1", "t2"], [len(ph1_cyc), -1])
cpmg_data.setaxis("ph1", len(ph1_cyc) / 4)
if config_dict["nScans"] > 1:
    cpmg_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/CPMG")
filename_out = filename + ".h5"
nodename = cpmg_data.name()
if os.path.exists(filename + ".h5"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp")
            cpmg_data.name("temp")
            nodename = "temp"
        cpmg_data.hdf5_write(f"{filename_out}/{nodename}", directory=target_directory)
else:
    try:
        cpmg_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp.h5 in the current directory"
        )
        if os.path.exists("temp.h5"):
            print("there is a temp.h5 already! -- I'm removing it")
            os.remove("temp.h5")
            cpmg_data.hdf5_write("temp.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
            )
config_dict.write()
fl.next("raw data")
fl.image(cpmg_data)
fl.next("abs raw data")
fl.image(abs(cpmg_data))
cpmg_data.ft("t", shift=True)
fl.next("raw data - ft")
fl.image(cpmg_data)
fl.next("abs raw data - ft")
fl.image(abs(cpmg_data))
fl.show()
# }}}
