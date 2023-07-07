"""
Test Run
========
A simple 90 pulse to test the spincore when we initially began
"""
from pyspecdata import *
import os
import SpinCore_pp
from datetime import datetime
import h5py
fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "test"
config_dict["date"] = date
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{set phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0, 1, 2, 3]
    nPhaseSteps = 4
if not phase_cycling:
    ph1_cyc = 0.0
    nPhaseSteps = 1
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
# {{{extra parameters
tx_phases = r_[0.0, 90.0, 180.0, 270.0]
amplitude = 1.0
RX_delay = 100.0
acq_time = nPoints / config_dict['SW_kHz']
config_dict['acq_time'] = acq_time
data_length = 2 * nPoints * config_dict['nEchoes'] * nPhaseSteps
SpinCore_pp.configureTX(config_dict['adcOffset'], config_dict['carrierFreq_MHz'], 
        tx_phases, amplitude, nPoints)
SpinCore_pp.init_ppg()
if phase_cycling:
    SpinCore_pp.load(
        [
            ("marker", "start", 1),
            ("phase_reset", 1),
            ("delay_TTL", 1.0),
            ("pulse_TTL", config_dict['p90'], "ph1", ph1_cyc,
            ("delay", 3e6),
            ("jumpto", "start"),
        ]
    )
if not phase_cycling:
    SpinCore_pp.load(
        [
            ("marker", "start", 1),
            ("phase_reset", 1),
            ("delay_TTL", 1.0),
            ("pulse_TTL", config_dict['p90'], 0.0),
            ("delay", 3e6),
            ("jumpto", "start"),
        ]
    )
SpinCore_pp.stop_ppg()
if phase_cycling:
    for x in range(config_dict['nScans']):
        print("SCAN NO. %d" % (x + 1))
        SpinCore_pp.runBoard()
if not phase_cycling:
    SpinCore_pp.runBoard()
SpinCore_pp.stopBoard()
print("EXITING...")
