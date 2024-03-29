"""ppg for obtaining performing shimming calibration
=====================================================
The following is used when the shims are replaced or moved in any way. When
moved the calibration or settings for the z and y shims need to be recalculated
for certainty. Here, the user can calculate the appropriate voltage setting for
each shim for optimal signal. Note: The XEPR_API server must be running for
this script. Normally this script is run with 4 scans 
"""
from pylab import ones_like, shape
from pyspecdata import getDATADIR, r_, figlist_var
import os, h5py
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
from Instruments.XEPR_eth import xepr
from Instruments import HP6623A, prologix_connection

target_directory = getDATADIR(exp_type="ODNP_NMR_comp/test_equipment")
# {{{ importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
config_dict["tau_us"] = (
    2500.0 + config_dict["deadtime_us"]
)  # optimal tau for NiSO4 sample used by AB
# }}}
# {{{filename
date = datetime.now().strftime("%y%m%d")
config_dict["date"] = date
filename = f"{config_dict['date']}_{config_dict['chemical']}_shimming" + ".h5"
# }}}
# {{{phase cycling steps
ph1_cyc = r_[0, 1, 2, 3]
ph2_cyc = r_[0, 2]
nPhaseSteps = 8
# }}}
# channel that is currently being investigated
test_ch = 3
file_nodename = "shimming_ch" + str(test_ch) 
# channel that was previously investigated/has predetermined value that you want to set
# set_ch : (ch #, voltage setting)
set_ch = [(2, 0.1)]
# {{{set up voltage info for the test
data_length = 2 * nPoints * config_dict["nEchoes"] * nPhaseSteps
voltage_array = r_[0.0:0.15:0.01]
current_readings = ones_like(voltage_array)
voltage_readings = ones_like(voltage_array)
# }}}
# {{{set field
print(
    "I'm assuming that you've tuned your probe to",
    config_dict["carrierFreq_MHz"],
    "since that's what's in your .ini file",
)
Field = config_dict["carrierFreq_MHz"] / config_dict["gamma_eff_MHz_G"]
print(
    "Based on that, and the gamma_eff_MHz_G you have in your .ini file, I'm setting the field to %f"
    % Field
)
with xepr() as x:
    assert Field < 3700, "are you crazy??? field is too high!"
    assert Field > 3300, "are you crazy?? field is too low!"
    Field = x.set_field(Field)
# }}}
# {{{ Check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"
    % total_pts
)
# }}}
# {{{ Run actual ppg
with prologix_connection() as p:
    with HP6623A(prologix_instance=p, address=5) as HP:
        HP.set_voltage(set_ch[0][0], set_ch[0][1])
        HP.set_voltage(test_ch, 0.0)
        HP.set_current(test_ch, 0.0)
        this_curr = HP.get_current(test_ch)
        this_volt = HP.get_voltage(test_ch)
        HP.output(test_ch, False)
        HP.output(set_ch[0][0], True)
        shim_data = run_spin_echo(
            nScans=config_dict["nScans"],
            indirect_idx=0,
            indirect_len=len(voltage_array),
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            p90_us=config_dict["p90_us"],
            repetition_us=config_dict["repetition_us"],
            tau_us=config_dict["tau_us"],
            SW_kHz=config_dict["SW_kHz"],
            indirect_fields=("Voltage", "Current"),
            ret_data=None,
        )
        volts_currents = shim_data.getaxis("indirect")
        volts_currents[0]["Voltage"] = this_volt
        volts_currents[0]["Current"] = this_curr
        shim_data.set_prop("acq_params")["voltage_setting"] = voltage_array
        shim_data.set_prop("acq_params")["shim_settings"] = set_ch
        for index, this_val in enumerate(voltage_array[1:]):
            HP.set_voltage(test_ch, this_val)
            this_curr = HP.get_current(test_ch)
            this_volt = HP.get_voltage(test_ch)
            HP.output(test_ch, True)
            get_volt_ch1 = HP.get_voltage(1)
            get_volt_ch2 = HP.get_voltage(2)
            get_volt_ch3 = HP.get_voltage(3)
            get_volt = [
                ("ch1", get_volt_ch1),
                ("ch2", get_volt_ch2),
                ("ch3", get_volt_ch3),
            ]
            shim_data.set_prop("acq_params")["shim_readings"] = get_volt
            print("CURRENT READING IS: %f" % this_curr)
            volts_currents[index + 1]["Voltage"] = this_volt
            volts_currents[index + 1]["Current"] = this_curr
            run_spin_echo(
                nScans=config_dict["nScans"],
                indirect_idx=index + 1,
                indirect_len=len(voltage_array),
                adcOffset=config_dict["adc_offset"],
                carrierFreq_MHz=config_dict["carrierFreq_MHz"],
                nPoints=nPoints,
                nEchoes=config_dict["nEchoes"],
                p90_us=config_dict["p90_us"],
                repetition_us=config_dict["repetition_us"],
                tau_us=config_dict["tau_us"],
                SW_kHz=config_dict["SW_kHz"],
                ret_data=shim_data,
            )
        print("Turning shim power off")
        HP.output(test_ch, False)
# }}}
# {{{save acquisition parameters
shim_data.set_prop("acq_params", config_dict.asdict())
# }}}
# {{{ chunk and set axes
shim_data.set_units("t", "s")
shim_data.chunk("t", ["ph2", "ph1", "t2"], [len(ph2_cyc), len(ph1_cyc), -1])
shim_data.setaxis("ph2", ph2_cyc / 4)
shim_data.setaxis("ph1", ph1_cyc / 4)
# }}}
# {{{saving file
nodename = shim_data.name(file_nodename)
if os.path.exists(filename):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, lets delete it to overwrite")
            del fp[nodename]
    shim_data.hdf5_write(f"{filename}/{nodename}", directory=target_directory)
else:
    try:
        shim_data.hdf5_write(filename, directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}, so I'm going to try to save your file to temp.h5 in the current directory"
        )
        if os.path.exists("temp.h5"):
            print("there is a temp.h5 -- I'm removing it")
            os.remove("temp.h5")
        shim_data.hdf5_write("temp.h5")
        print(
            "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
        )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", shim_data.name()))
config_dict.write()
# }}}
# {{{Plotting
I_axis = []
for indir_val in range(shape(shim_data.getaxis("indirect"))[0]):
    I_axis.append(shim_data.getaxis("indirect")[indir_val][1])
shim_data.setaxis("indirect", I_axis)
shim_data.rename("indirect", "I")
if config_dict["nScans"] > 1:
    shim_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
with figlist_var() as fl:
    fl.next("image")
    shim_data.mean("nScans")
    fl.image(shim_data.C.setaxis("I", "#"))
    t2_max = shim_data.getaxis("t2")[-1]
    shim_data -= shim_data["t2" : (0.75 * t2_max, None)].C.mean("t2")
    shim_data.ft("t2", shift=True)
    fl.next("image - ft")
    fl.image(shim_data.C.setaxis("I", "#"))
    fl.next("image - ft, coherence")
    shim_data.ft(["ph1", "ph2"])
    fl.image(shim_data.C.setaxis("I", "#"))
    fl.next("data plot")
    data_slice = shim_data["ph1", 1]["ph2", -2]
    fl.plot(data_slice, alpha=0.5)
    fl.plot(abs(data_slice), color="k", alpha=0.5)
# }}}
