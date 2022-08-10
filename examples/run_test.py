from pyspecdata import *
import os
import sys
from . import SpinCore_pp
from datetime import datetime
fl = figlist_var()
config_dict = SpinCore_pp.configuration("active.ini")
date = datetime.now().strftime("%y%m%d")
config_dict['type'] = 'test'
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
tx_phases = r_[0.0, 90.0, 180.0, 270.0]
amplitude = 1.0
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
RX_delay = 100.0
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
acq_time = nPoints / config_dict['SW_kHz']
config_dict['acq_time'] = acq_time
data_length = 2 * nPoints * config_dict['nEchoes'] * nPhaseSteps
SpinCore_pp.configureTX(config_dict['adcOffset'], config_dict['carrierFreq_MHz'], 
        tx_phases, amplitude, nPoints)
acq_time = SpinCore_pp.configureRX(config_dict['SW_kHz'], nPoints, config_dict['nScans'], 
        config_dict['nEchoes'], nPhaseSteps)
verifyParams()
SpinCore_pp.init_ppg()
if phase_cycling:
    SpinCore_pp.load(
        [
            ("marker", "start", 1),
            ("phase_reset", 1),
            ("delay_TTL", 1.0),
            ("pulse_TTL", config_dict['p90'], "ph1", r_[0, 1, 2, 3]),
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
