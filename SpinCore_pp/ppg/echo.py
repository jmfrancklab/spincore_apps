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
import time
import logging

# {{{spin echo ppg
def run_spin_echo(
    nScans,
    indirect_idx,
    indirect_len,
    adcOffset,
    carrierFreq_MHz,
    nPoints,
    nEchoes,
    p90_us,
    repetition,
    tau_us,
    SW_kHz,
    output_name,
    indirect_fields=None,
    ph1_cyc=psp.r_[0, 1, 2, 3],
    ph2_cyc=psp.r_[0],
    ret_data=None,
    deadtime_us = 10.0,
    deblank_us = 1.0,
    amplitude = 1.0,
):
    """run nScans and slot them into the indirect_idx index of ret_data -- assume
    that the first time this is run, it will be run with ret_data=None and that
    after that, you will pass in ret_data this generates an "indirect" axis.

    Parameters
    ==========
    nScans:         int
                    number of repeats of the pulse sequence (for averaging over data)
    indirect_idx:   int
                    index along the 'indirect' dimension
    indirect_len:   int
                    size of indirect axis.
                    Used to allocate space for the data once the first scan is run.
    adcOffset:      int
                    offset of ADC acquired with SpinCore_apps/C_examples/adc_offset.exe
    carrierFreq_MHz:    float
                        carrier frequency to be set in MHz
    nPoints:        int
                    number of points for the data
    nEchoes:        int
                    Number of Echoes to be acquired.
                    This should always be 1, since this pulse
                    program doesn't generate multiple echos.
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
    indirect_fields: tuple (pair) of str or (default) None
                    Name for the first field of the structured array
                    that stores the indirect dimension coordinates.
                    We use a structured array, e.g., to store both start and
                    stop times for the experiment.

                    If you want the indirect dimension coordinates
                    to be a normal array, set this to None

                    This parameter is only used when `ret_data` is set to `None`.
    ph1_cyc:        array
                    phase steps for the first pulse
    ph2_cyc:        array
                    phase steps for the second pulse
    ret_data:       nddata (default None)
                    returned data from previous run or `None` for the first run.
    """
    assert nEchoes == 1, "you must only choose nEchoes=1"
    tx_phases = psp.r_[0.0, 90.0, 180.0, 270.0]
    nPhaseSteps = len(ph1_cyc) * len(ph2_cyc)
    data_length = 2 * nPoints * nEchoes * nPhaseSteps
    for x in range(nScans):
        run_scans_time_list = [time.time()]
        run_scans_names = ["configure"]
        logging.info("*** *** *** SCAN NO. %d *** *** ***" % (x + 1))
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
                ("pulse_TTL", p90_us, "ph1", ph1_cyc),
                ("delay", tau_us),
                ("delay_TTL", deblank_us),
                ("pulse_TTL", 2.0 * p90_us, "ph2", ph2_cyc),
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
            if indirect_fields is None:
                times_dtype = np.double
            else:
                # {{{ dtype for structured array
                times_dtype = np.dtype(
                    [(indirect_fields[0], np.double), (indirect_fields[1], np.double)]
                )
                # }}}
            mytimes = np.zeros(indirect_len, dtype=times_dtype)
            time_axis = psp.r_[0:dataPoints] / (SW_kHz * 1e3)
            ret_data = psp.ndshape(
                [indirect_len, nScans, len(time_axis)], ["indirect", "nScans", "t"]
            ).alloc(dtype=np.complex128)
            ret_data.setaxis("indirect", mytimes)
            ret_data.setaxis("t", time_axis).set_units("t", "s")
            ret_data.setaxis("nScans", psp.r_[0:nScans])
        ret_data["indirect", indirect_idx]["nScans", x] = data_array
        run_scans_time_list.append(time.time())
        this_array = np.array(run_scans_time_list)
        logging.debug("stored scan", x, "for indirect_idx", indirect_idx)
        logging.debug(
                "time for each chunk",
                [
                    "%s %0.1f" % (run_scans_names[j], v)
                    for j, v in enumerate(np.diff(this_array))
                ],
        )
        return ret_data
