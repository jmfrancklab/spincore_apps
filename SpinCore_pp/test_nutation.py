from pyspecdata import *
from . import SpinCore_pp
import socket
import sys
import time

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "nutation"
config_dict["date"] = date
config_dict["nutation_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{let computer set field
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
    print("field set to ", Field)
# }}}
tx_phases = r_[0.0, 90.0, 180.0, 270.0]
transient = 500.0
data_length = 2 * nPoints * config_dict["nEchoes"] * nPhaseSteps
p90_range = linspace(0.1, 10.1, 10, endpoint=False)
for index, val in enumerate(p90_range):
    p90 = val  # us
    SpinCore_pp.configureTX(
        config_dict["adcOffset"],
        config_dict["carrierFreq_MHz"],
        tx_phases,
        config_dict["amplitude"],
        nPoints,
    )
    acq_time = SpinCore_pp.configureRX(
        config_dict["SW_kHz"],
        nPoints,
        config_dict["nScans"],
        config_dict["nEchoes"],
        nPhaseSteps,
    )  # ms
    SpinCore_pp.init_ppg()
    SpinCore_pp.load(
        [
            ("marker", "start", config_dict["nScans"]),
            ("phase_reset", 1),
            ("pulse", p90, 0.0),
            ("delay", config_dict["tau_us"]),
            ("pulse", 2.0 * p90, 0.0),
            ("delay", transient),
            ("acquire", config_dict["acq_time_ms"]),
            ("delay", config_dict["repetition_us"]),
            ("jumpto", "start"),
        ]
    )
    SpinCore_pp.stop_ppg()
    SpinCore_pp.runBoard()
    raw_data = SpinCore_pp.getData(
        data_length, nPoints, config_dict["nEchoes"], nPhaseSteps
    )
    raw_data.astype(float)
    data = []
    # according to JF, this commented out line
    # should work same as line below and be more effic
    # data = raw_data.view(complex128)
    data[::] = complex128(raw_data[0::2] + 1j * raw_data[1::2])
    dataPoints = float(shape(data)[0])
    time_axis = linspace(
        0.0,
        config_dict["nEchoes"] * nPhaseSteps * config_dict["acq_time_ms"] * 1e-3,
        dataPoints,
    )
    data = nddata(array(data), "t")
    data.setaxis("t", time_axis).set_units("t", "s")
    data.name("signal")
    if index == 0:
        nutation_data = ndshape([len(p90_range), len(time_axis)], ["p_90", "t"]).alloc(
            dtype=complex128
        )
        nutation_data.setaxis("p_90", p90_range * 1e-6).set_units("p_90", "s")
        nutation_data.setaxis("t", time_axis).set_units("t", "s")
    nutation_data["p_90", index] = data
SpinCore_pp.stopBoard()
save_file = True
while save_file:
    try:
        nutation_data.name("nutation")
        nutation_data.hdf5_write(filename + ".h5")
        print("Name of saved data", nutation_data.name())
        print("Units of saved data", nutation_data.get_units("t"))
        print("Shape of saved data", ndshape(nutation_data))
        save_file = False
    except Exception as e:
        print(e)
        print("FILE ALREADY EXISTS.")
        save_file = False
fl.next("raw data")
fl.image(nutation_data)
nutation_data.ft("t", shift=True)
fl.next("FT raw data")
fl.image(nutation_data)
fl.show()
