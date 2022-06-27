from .. import (
    configureTX,
    configureRX,
    init_ppg,
    stop_ppg,
    runBoard,
    getData,
)
from .. import load as spincore_load
import pyspecdata as psp
import numpy as np
from numpy import r_
import time
import logging

# {{{IR ppg
def run_IR(
    nScans,
    vd_list_us,
    adcOffset,
    carrierFreq_MHz,
    nPoints,
    nEchoes,
    p90_us,
    repetition,
    tau_us,
    SW_kHz,
    output_name,
    ph1_cyc=r_[0, 2],
    ph2_cyc=r_[0, 2],
    ret_data=None,
    deadtime_us = 10.0,
    deblank_us = 1.0,
    amplitude = 1.0,
):
    """Run an inversion recovery and generate a single nddata with a vd dimension.
    We assume the first time this is run, ret_data=None, after which we will pass in ret_data.

    Parameters
    ==========
    nScans:         int
                    number of repeats of the pulse sequence (for averaging over data)
    adcOffset:      int
                    offset of ADC acquired with SpinCore_apps/C_examples/adc_offset.exe
    carrierFreq_MHz:    float
                        carrier frequency to be set in MHz
    nPoints:        int
                    number of points for the data
    nEchoes:        int
                    Number of Echoes to be acquired
    p90_us:         float
                    90 time of the probe in us
    repetition:     int
                    3-5 x T1 of the sample in seconds
    tau_us:         float
                    Echo Time should be a few ms for a good hermitian function to be
                    applied later in processing. Standard tau_us = 3500.
    SW_kHz:         float
                    spectral width of the data. Minimum = 1.9
    output_name:    str
                    file name the data will be saved under??
                    (as noted below this might be obsolete/bogus)
    ph1_cyc:        array
                    phase steps for the first pulse
    ph2_cyc:        array
                    phase steps for the second pulse
    ret_data:       nddata (default None)
                    returned data from previous run or `None` for the first run.
    """
    assert nEchoes==1, "you must only choose nEchoes=1"
    tx_phases = r_[0.0, 90.0, 180.0, 270.0]
    nPhaseSteps = len(ph1_cyc) * len(ph2_cyc)
    data_length = 2 * nPoints * nEchoes * nPhaseSteps
    if type(vd_list_us) is list:
        vd_list_us = np.array(vd_list_us)
    for index, vd in enumerate(vd_list_us):
        logging.info("***")
        logging.info("INDEX %d - VARIABLE DELAY %f" % (index, vd))
        logging.info("***")
        for x in range(nScans):
            run_scans_time_list = [time.time()]
            run_scans_names = ["configure"]
            configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
            run_scans_time_list.append(time.time())
            run_scans_names.append("configure Rx")
            acq_time_ms = configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps)
            run_scans_time_list.append(time.time())
            run_scans_names.append("init")
            init_ppg()
            run_scans_time_list.append(time.time())
            run_scans_names.append("prog")
            spincore_load(
                [
                    ("marker", "start", 1),
                    ("phase_reset", 1),
                    ("delay_TTL", deblank_us),
                    ("pulse_TTL", 2.0 * p90_us, "ph1", ph1_cyc),
                    ("delay", vd),
                    ("delay_TTL", 1.0),
                    ("pulse_TTL", p90_us, "ph2", ph2_cyc),
                    ("delay", tau_us),
                    ("delay_TTL", deblank_us),
                    ("pulse_TTL", 2.0 * p90_us, 0),
                    ("delay", deadtime_us),
                    ("acquire", acq_time_ms),
                    ("delay", repetition),
                    ("jumpto", "start"),
                ]
            )
            run_scans_time_list.append(time.time())
            run_scans_names.append("stop ppg")
            stop_ppg()
            run_scans_time_list.append(time.time())
            run_scans_names.append("run")
            runBoard()
            run_scans_time_list.append(time.time())
            run_scans_names.append("get data")
            # On reviewing the code, and comparing to line 119-120 of
            # SpinCore_pp.i, it looks like this last argument is not used -- could
            # it just be removed?? (output_name)
            raw_data = getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
            run_scans_time_list.append(time.time())
            run_scans_names.append("shape data")
            data_array = []
            data_array[::] = np.complex128(raw_data[0::2] + 1j * raw_data[1::2])
            dataPoints = float(np.shape(data_array)[0])
            if ret_data is None:
                indirect_len = len(vd_list_us)
                time_axis = r_[0:dataPoints] / (SW_kHz * 1e3)
                ret_data = psp.ndshape(
                    [indirect_len, nScans, len(time_axis)], ["vd", "nScans", "t"]
                ).alloc(dtype=np.complex128)
                ret_data.setaxis("vd", vd_list_us * 1e-6).set_units("vd", "s")
                ret_data.setaxis("t", time_axis).set_units("t", "s")
                ret_data.setaxis("nScans", r_[0:nScans])
            ret_data["vd", index]["nScans", x] = data_array
            run_scans_time_list.append(time.time())
            this_array = np.array(run_scans_time_list)
            logging.debug(strm("checkpoints:", this_array - this_array[0]))
            logging.debug(
                strm(
                    "time for each chunk",
                    [
                        "%s %0.1f" % (run_scans_names[j], v)
                        for j, v in enumerate(np.diff(this_array))
                    ],
                )
            )
    return ret_data
# }}}
