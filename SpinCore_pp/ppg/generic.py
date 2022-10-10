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

# {{{spin echo ppg
def generic(
    ppg_list,
    nScans,
    indirect_idx,
    indirect_len,
    adcOffset,
    carrierFreq_MHz,
    nPoints,
    SW_kHz,
    indirect_fields=None,
    ph1_cyc=r_[0, 1, 2, 3],
    ph2_cyc=r_[0],
    ret_data=None,
    amplitude=1.0,
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
    ret_data:       nddata (default None)
                    returned data from previous run or `None` for the first run.
    """
    tx_phases = r_[0.0, 90.0, 180.0, 270.0]
    all_ppg_arrays = [j[3] for j in ppg_list if len(j)>3]
    nPhaseSteps = prod([len(j) for j in all_ppg_arrays])
    nEchoes = [j[2]+1 for j in ppg_list if len(j)>2 and j[0] == 'marker' and j[1] == 'echo_label']
    data_length = 2 * nPoints * nEchoes * nPhaseSteps
    for nScans_idx in range(nScans):
        run_scans_time_list = [time.time()]
        run_scans_names = ["configure"]
        logging.debug("*** *** *** SCAN NO. %d *** *** ***" % (nScans_idx + 1))
        configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        run_scans_time_list.append(time.time())
        run_scans_names.append("configure Rx")
        check = configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps)
        assert acq_time_ms == check
        run_scans_time_list.append(time.time())
        run_scans_names.append("init")
        init_ppg()
        run_scans_time_list.append(time.time())
        run_scans_names.append("prog")
        spincore_load(ppg_list)
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
