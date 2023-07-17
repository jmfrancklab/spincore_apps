from pyspecdata import *
from numpy import *
import os, sys, time
import SpinCore_pp
import h5py
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
from Instruments import Bridge12, prologix_connection, gigatronics
from serial import Serial
from datetime import datetime
from SpinCore.power_helper import gen_powerlist

fl = figlist_var()
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/ODNP")
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "STE_mw"
config_dict["date"] = date
config_dict["echo_counter"] += 1
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
# {{{phase cycling
tx_phases = r_[0.0, 90.0, 180.0, 270.0]
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
# }}}
# {{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
# }}}
tau1 = 2
tau2 = 80000
# {{{run ppg
data_length = 2 * nPoints * config_dict["nEchoes"] * nPhaseSteps
for x in range(config_dict["nScans"]):
    SpinCore_pp.configureTX(
        config_dict["adcOffset"],
        config_dict["carrierFreq_MHz"],
        tx_phases,
        config_dict["amplitude"],
        nPoints,
    )
    SpinCore_pp.init_ppg()
    if phase_cycling:
        SpinCore_pp.load(
            [
                ("marker", "start", 1),
                ("phase_reset", 1),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", config_dict["p90_us"], "ph1", r_[0, 2]),
                ("delay", tau1),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", config_dict["p90_us"], "ph2", r_[0, 2]),
                ("delay", tau2),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", config_dict["p90_us"], "ph3", r_[0, 2]),
                ("delay", config_dict["deadtime_us"]),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", config_dict["repetition_us"]),
                ("jumpto", "start"),
            ]
        )
    if not phase_cycling:
        SpinCore_pp.load(
            [
                ("marker", "start", config_dict["nScans"]),
                ("phase_reset", 1),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", config_dict["p90_us"], 0.0),
                ("delay", config_dict["tau_us"]),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
                ("delay", config_dict["deadtime_us"]),
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
    data[::] = complex128(raw_data[0::2] + 1j * raw_data[1::2])
    dataPoints = float(shape(data)[0])
    if x == 0:
        time_axis = linspace(
            0.0,
            config_dict["nEchoes"] * nPhaseSteps * config_dict["acq_time_ms"] * 1e-3,
            dataPoints,
        )
        DNP_data = ndshape(
            [len(powers) + 1, config_dict["nScans"], len(time_axis)],
            ["power", "nScans", "t"],
        ).alloc(dtype=complex128)
        DNP_data.setaxis("power", r_[0, powers]).set_units("W")
        DNP_data.setaxis("t", time_axis).set_units("t", "s")
        DNP_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    data = nddata(array(data), "t")
    data.setaxis("t", time_axis)
    # Define nddata to store along the new power dimension
    DNP_data["power", 0]["nScans", x] = data
# }}}
# {{{run ppg with B12
with Bridge12() as b:
    b.set_wg(True)
    b.set_rf(True)
    b.set_amp(True)
    this_return = b.lock_on_dip(
        ini_range=(
            parser_dict["uw_dip_center_GHz"] - parser_dict["uw_dip_width_GHz"] / 2,
            parser_dict["uw_dip_center_GHz"] + parser_dict["uw_dip_width_GHz"] / 2,
        )
    )
    dip_f = this_return[2]
    b.set_freq(dip_f)
    meter_powers = zeros_like(dB_settings)
    for j, this_power in enumerate(dB_settings):
        if j > 0 and this_power > last_power + 3:
            last_power += 3
            b.set_power(last_power)
            time.sleep(3.0)
            while this_power > last_power + 3:
                last_power += 3
                b.set_power(last_power)
                time.sleep(3.0)
            b.set_power(this_power)
        elif j == 0:
            threshold_power = 10
            if this_power > threshold_power:
                next_power = threshold_power + 3
                while next_power < this_power:
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
        for x in range(config_dict["nScans"]):
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
            if phase_cycling:
                SpinCore_pp.load(
                    [
                        ("marker", "start", 1),
                        ("phase_reset", 1),
                        ("delay_TTL", config_dict["deblank_us"]),
                        ("pulse_TTL", config_dict["p90_us"], "ph1", r_[0, 2]),
                        ("delay", tau1),
                        ("delay_TTL", config_dict["deblank_us"]),
                        ("pulse_TTL", config_dict["p90_us"], "ph2", r_[0, 2]),
                        ("delay", tau2),
                        ("delay_TTL", config_dict["deblank_us"]),
                        ("pulse_TTL", config_dict["p90"], "ph3", r_[0, 2]),
                        ("delay", config_dict["deadtime_us"]),
                        ("acquire", config_dict["acq_time_ms"]),
                        ("delay", config_dict["repetition_us"]),
                        ("jumpto", "start"),
                    ]
                )
                # {{{
            if not phase_cycling:
                SpinCore_pp.load(
                    [
                        ("marker", "start", config_dict["nScans"]),
                        ("phase_reset", 1),
                        ("delay_TTL", config_dict["deblank_us"]),
                        ("pulse_TTL", config_dict["p90_us"], 0.0),
                        ("delay", config_dict["tau_us"]),
                        ("delay_TTL", config_dict["deblank_us"]),
                        ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
                        ("delay", config_dict["deadtime_us"]),
                        ("acquire", config_dict["acq_time_ms"]),
                        ("delay", config_dict["repetition_us"]),
                        ("jumpto", "start"),
                    ]
                )
                # }}}
            SpinCore_pp.stop_ppg()
            SpinCore_pp.runBoard()
            raw_data = SpinCore_pp.getData(
                data_length, nPoints, config_dict["nEchoes"], nPhaseSteps
            )
            raw_data.astype(float)
            data = []
            data[::] = complex128(raw_data[0::2] + 1j * raw_data[1::2])
            dataPoints = float(shape(data)[0])
            time_axis = linspace(
                0.0,
                config_dict["nEchoes"]
                * nPhaseSteps
                * config_dict["acq_time_ms"]
                * 1e-3,
                dataPoints,
            )
            data = nddata(array(data), "t")
            data.setaxis("t", time_axis).set_units("t", "s")
            data.name("signal")
            DNP_data["power", j + 1]["nScans", x] = data
        last_power = this_power
DNP_data.name(config_dict["type"] + "_" + config_dict["echo_counter"])
DNP_data.set_prop("meter_powers", meter_powers)
SpinCore_pp.stopBoard()
# }}}
# {{{ save data
DNP_data.set_prop("acq_params", config_dict.asdict())
config_dict.write()
nodename = DNP_data.name()
filename_out = filename + ".h5"
with h5py.File(
    os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
) as fp:
    if nodename in fp.keys():
        print(
            "this nodename already exists, so I will call it temp_STE_mw_%d"
            % config_dict["odnp_counter"]
        )
        DNP_data.name("temp_STE_mw%d" % config_dict["odnp_counter"])
        nodename = "temp_STE_mw_%d" % config_dict["odnp_counter"]
        DNP_data.hdf5_write(f"{filename_out}", directory=target_directory)
    else:
        DNP_data.hdf5_write(f"{filename_out}", directory=target_directory)
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", DNP_data.name()))
print(("Shape of saved data", ndshape(DNP_data)))
# }}}
# {{{ image data
fl.next("raw data")
fl.image(DNP_data.C.setaxis("power", "#").set_units("power", "scan #"))
data.ft("t", shift=True)
DNP_data.ft(["ph1", "ph2", "ph3"])
fl.next("abs coherence domain - ft")
fl.image(abs(DNP_data).C.setaxis("power", "#").set_units("power", "scan #"))
fl.show()
# }}}
