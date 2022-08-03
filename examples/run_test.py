from pyspecdata import *
import os
import sys
from . import SpinCore_pp

fl = figlist_var()
date = "190404"
output_name = "test"
adcOffset = 48
carrierFreq_MHz = 14.86
tx_phases = r_[0.0, 90.0, 180.0, 270.0]
amplitude = 1.0
tau = 10.0
nScans = 1
nEchoes = 1
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 1
if not phase_cycling:
    nPhaseSteps = 1
p90 = 5.0
RX_delay = 100.0
repetition = 1e6
SW_kHz = 80.0
nPoints = 128
acq_time = nPoints / SW_kHz
data_length = 2 * nPoints * nEchoes * nPhaseSteps
SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps)
verifyParams()
SpinCore_pp.init_ppg()
if phase_cycling:
    SpinCore_pp.load(
        [
            ("marker", "start", 1),
            ("phase_reset", 1),
            ("delay_TTL", 1.0),
            ("pulse_TTL", p90, "ph1", r_[0, 1, 2, 3]),
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
            ("pulse_TTL", p90, 0.0),
            ("delay", 3e6),
            ("jumpto", "start"),
        ]
    )
SpinCore_pp.stop_ppg()
if phase_cycling:
    for x in range(nScans):
        print("SCAN NO. %d" % (x + 1))
        SpinCore_pp.runBoard()
if not phase_cycling:
    SpinCore_pp.runBoard()
SpinCore_pp.stopBoard()
print("EXITING...")
