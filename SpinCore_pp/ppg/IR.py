from .. import configureTX, configureRX, configureRX, init_ppg, stop_ppg, runBoard, getData
from .. import load as spincore_load
# remove import *
from pyspecdata import *
from numpy import *
import time
#{{{IR ppg
def run_scans_IR(nPoints, nEchoes, vd_list, nScans, adcOffset, carrierFreq_MHz,
        p90_us, tau_us, repetition, output_name, SW_kHz,
        ph1_cyc = r_[0,2], ph2_cyc = r_[0,2],ret_data=None):
    """Run an inversion recovery and generate a single nddata with a vd dimension.
    We assume the first time this is run, ret_data=None, after which we will pass in ret_data. 
    Generates an "indirect" axis.

    Parameters
    ==========
    nScans:         int
                    number of repeats of the pulse sequence (for averaging over data)
    nEchoes:        int
                    Number of echoes for each T1
    adcOffset:      int 
                    offset of ADC acquired with SpinCore_apps/C_examples/adc_offset.exe
    carrierFreq_MHz:    int
                        carrier frequency in MHz
    vd_list:        list or array
                    list of varied delays for IR experiment,
                    in microseconds
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
    ph1_cyc:    array
                phase steps for the first pulse
    ph2_cyc:    array
                phase steps for the second pulse
    ret_data:       nddata (default None)
                    returned data from previous run or `None` for the first run.
    """
    deadtime_us = 10.0
    deblank_us = 1.0
    amplitude = 1.0
    tx_phases = r_[0.0,90.0,180.0,270.0]
    nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)
    data_length = 2*nPoints*nEchoes*nPhaseSteps
    for index,val in enumerate(vd_list):
        vd = val
        print("***")
        print("INDEX %d - VARIABLE DELAY %f"%(index,val))
        print("***")
        for x in range(nScans):
            run_scans_time_list = [time.time()]
            run_scans_names = ['configure']
            configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
            run_scans_time_list.append(time.time())
            run_scans_names.append('configure Rx')
            acq_time_ms = configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps)
            run_scans_time_list.append(time.time())
            run_scans_names.append('init')
            init_ppg()
            run_scans_time_list.append(time.time())
            run_scans_names.append('prog')
            spincore_load([
                ('marker','start',1),
                ('phase_reset',1),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,'ph1',ph1_cyc),
                ('delay',vd),
                ('delay_TTL',1.0),
                ('pulse_TTL',p90_us,'ph2',ph2_cyc),
                ('delay',tau_us),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,0),
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
            dataPoints = float(np.shape(data_array)[0])
            if ret_data is None:
                indirect_len = len(vd_list)
                time_axis = r_[0:dataPoints]/(SW_kHz*1e3)
                ret_data = ndshape([indirect_len,nScans,len(time_axis)],
                        ['vd','nScans','t']).alloc(dtype=complex128)
                ret_data.setaxis('vd',vd_list*1e-6).set_units('vd','s')
                ret_data.setaxis('t',time_axis).set_units('t','s')
                ret_data.setaxis('nScans',r_[0:nScans])
            ret_data['vd',index]['nScans',x]['indirect',indirect_idx] = data_array
            run_scans_time_list.append(time.time())
            this_array = array(run_scans_time_list)
            print("checkpoints:",this_array-this_array[0])
            print("time for each chunk",['%s %0.1f'%(run_scans_names[j],v) for j,v in enumerate(diff(this_array))])
            print("stored scan",x,"for indirect_idx",indirect_idx)
            if nScans > 1:
                ret_data.setaxis('nScans',r_[0:nScans])
    return ret_data
#}}}

