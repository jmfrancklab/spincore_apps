from .. import configureTX,configureRX, configureRX, init_ppg, stop_ppg, runBoard, getData, verifyParams
from .. import load as spincore_load
# remove import *
from pyspecdata import *
from numpy import *
import time
def run_spin_echo(nScans, indirect_idx, indirect_len,adcOffset, carrierFreq_MHz, 
        nPoints, nEchoes,p90_us, repetition, tau_us, SW_kHz, output_name,
        ph1_cyc=r_[0,1,2,3], ph2_cyc=r_[0], DNP_data=None):
    """run nScans and slot them into the indirect_idx index of DNP_data -- assume
    that the first time this is run, it will be run with DNP_data=None and that
    after that, you will pass in DNP_data this generates an "indirect" axis.

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
    DNP_data:       nddata (default None)
                    returned data from previous run or `None` for the first run.
    """
    deadtime_us = 10.0
    deblank_us = 1.0
    amplitude = 1.0
    tx_phases = r_[0.0,90.0,180.0,270.0]
    print("about to run run_spin_echo for",indirect_idx)
    nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)
    data_length = 2*nPoints*nEchoes*nPhaseSteps
    for x in range(nScans):
        run_scans_time_list = [time.time()]
        run_scans_names = ['configure']
        print("*** *** *** SCAN NO. %d *** *** ***"%(x+1))
        configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        run_scans_time_list.append(time.time())
        run_scans_names.append('configure Rx')
        print("***")
        print("CONFIGURING RECEIVER...")
        acq_time_ms = configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps)
        # acq_time_ms is in msec!
        run_scans_time_list.append(time.time())
        run_scans_names.append('init')
        init_ppg()
        run_scans_time_list.append(time.time())
        run_scans_names.append('prog')
        spincore_load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',p90_us,'ph1',ph1_cyc),
            ('delay',tau_us),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',2.0*p90_us,'ph2',ph2_cyc),
            ('delay',deadtime_us),
            ('acquire',acq_time_ms),
            ('delay',repetition),
            ('jumpto','start')
            ])
        run_scans_time_list.append(time.time())
        run_scans_names.append('prog')
        stop_ppg()
        run_scans_time_list.append(time.time())
        run_scans_names.append('run')
        runBoard()
        run_scans_time_list.append(time.time())
        run_scans_names.append('get data')
        # On reviewing the code, and comparing to line 119-120 of
        # SpinCore_pp.i, it looks like this last argument is not used -- could
        # it just be removed?? 
        raw_data = getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
        run_scans_time_list.append(time.time())
        run_scans_names.append('shape data')
        data_array=[]
        data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
        dataPoints = float(shape(data_array)[0])
        if DNP_data is None:
            times_dtype = dtype([('start_times',double),('stop_times',double)])
            mytimes = zeros(indirect_len,dtype=times_dtype)
            time_axis = r_[0:dataPoints]/(SW_kHz*1e3) 
            DNP_data = ndshape([indirect_len,nScans,len(time_axis)],['indirect','nScans','t']).alloc(dtype=complex128)
            DNP_data.setaxis('indirect',mytimes)
            DNP_data.setaxis('t',time_axis).set_units('t','s')
            DNP_data.setaxis('nScans',r_[0:nScans])
            data_array = nddata(array(data_array),[-1],['t'])
            data_array.setaxis('t',time_axis)
        # (delete on reading) JF edited -- there was an else block
        # w/ reference to "j", but j is not defined in the function!
        # If I assume that j+1 was intended to be indirect_idx, then
        # the following works for "if" as well as "else"
        DNP_data['indirect',indirect_idx]['nScans',x] = data_array
        run_scans_time_list.append(time.time())
        print("stored scan",x,"for indirect_idx",indirect_idx)
        return DNP_data
