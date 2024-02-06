from .. import (
    configureTX,
    configureRX,
    init_ppg,
    stop_ppg,
    runBoard,
    getData,
    stopBoard,
)
from .. import load as spincore_load
import pyspecdata as psp
import numpy as np
from numpy import r_
from pyspecdata import strm
import time
import logging

# {{{IR ppg
def run_IR(
    nScans,
    vd,
    indirect_idx,
    indirect_len,
    adcOffset,
    carrierFreq_MHz,
    nPoints,
    nEchoes,
    p90_us,
    repetition_us,
    tau_us,
    SW_kHz,
    indirect_fields=None,
    ph1_cyc=r_[0, 2],
    ph2_cyc=r_[0, 2],
    ret_data=None,
    deadtime_us=10.0,
    deblank_us=1.0,
    amplitude=1.0,
):
    """Run a single (signal averaged) scan out of an inversion recovery and generate a single nddata with a vd dimension.
    We assume the first time this is run, ret_data=None, after which we will pass in ret_data.

    Parameters
    ==========
    nScans:         int
                    number of repeats of the pulse sequence (for averaging over data)
    vd:             The variable delay to use for this scan
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
    repetition_us:  float
                    3-5 x T1 of the sample in seconds
    tau_us:         float
                    Echo Time should be a few ms for a good hermitian function to be
                    applied later in processing. Standard tau_us = 3500.
    SW_kHz:         float
                    spectral width of the data. Minimum = 1.9
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
    # take the desired p90 and p180
    # (2*desired_p90) and convert to what needs to
    # be programmed in order to get the desired
    # times
    prog_p90_us = prog_plen(p90_us)
    prog_p180_us = prog_plen(2 * p90_us)
    tx_phases = r_[0.0, 90.0, 180.0, 270.0]
    nPhaseSteps = len(ph1_cyc) * len(ph2_cyc)
    data_length = 2 * nPoints * nEchoes * nPhaseSteps
    for nScans_idx in range(nScans):
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
                ("phase_reset", 1),
                ("delay_TTL", deblank_us),
                ("pulse_TTL", prog_p180_us, "ph1", ph1_cyc),
                ("delay", vd),
                ("delay_TTL", 1.0),
                ("pulse_TTL", prog_p90_us, "ph2", ph2_cyc),
                ("delay", tau_us),
                ("delay_TTL", deblank_us),
                ("pulse_TTL", prog_p180_us, 0),
                ("delay", deadtime_us),
                ("acquire", acq_time_ms),
                ("delay", repetition_us),
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
        raw_data = getData(data_length, nPoints, nEchoes, nPhaseSteps)
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
            time_axis = r_[0:dataPoints] / (SW_kHz * 1e3)
            ret_data = psp.ndshape(
                [indirect_len, nScans, len(time_axis)], ["indirect", "nScans", "t"]
            ).alloc(dtype=np.complex128)
            ret_data.setaxis("indirect", mytimes)
            ret_data.setaxis("t", time_axis).set_units("t", "s")
            ret_data.setaxis("nScans", r_[0:nScans])
        elif indirect_idx == 0 and nScans_idx == 0:
            raise ValueError(
                "you seem to be on the first scan, but ret_data is not None -- it is "
                + str(ret_data)
                + " and we're not currently running ppgs where this makes sense"
            )
        ret_data["indirect", indirect_idx]["nScans", nScans_idx] = data_array
        stopBoard()
        run_scans_time_list.append(time.time())
        this_array = np.array(run_scans_time_list)
        logging.debug(strm("stored scan", nScans_idx, "for indirect_idx", indirect_idx))
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
