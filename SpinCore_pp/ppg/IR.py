from .. import configureRX, configureRX, init_ppg, stop_ppg, runBoard, getData
from .. import load as spincore_load
from pyspecdata import *
from numpy import *
#{{{IR ppg
def run_scans_IR(nPoints, nEchoes, vd_list, nScans, adcOffset, carrierFreq_MHz,
        p90_us, tau_us, repetition, output_name, SW_kHz, indirect_idx, node_name, 
        ph1_cyc = r_[0,2], ph2_cyc = r_[0,2],vd_data=None):
    """run nScans and slots them into the indirect idx  index of vd_data. We assume the first    time this is run, vd_data=None, after which we will pass in vd_data. 
    Generates an "indirect" axis.

    Parameters
    ==========
    nPoints:    int
                Number of points to be collected for dataset
    nEchoes:    int
                Number of echoes for each T1
    vd_list:    array
                array of varied delays for IR experiment
    nScans: int 
            number of averages over data
    adcOffset:  int 
                offset of ADC acquired with SpinCore_apps/C_examples/adc_offset.exe
    carrierFreq_MHz:    int
                        carrier frequency in MHz
    p90_us:     int
                90 time of probe in use in us.
    tau_us:     int
                echo time in us. Our standard is 3500.
    repetition:     int
                    repetition delay (3-5 x T1)
    output_name:    str
                    filename for the data to be saved under
    SW_kHz:     int
                spectral width for data acquisition in kHz. Minimum is 1.9 kHz
    indirect_idx:   int
                    index of the indirect dimension which we are storing the data to
    node_name:  str
                nodename for which the data will be saved under
                useful when running multiple IR at different temps
                or powers.
    ph1_cyc:    array
                phase steps for first pulse
    ph_2_cyc:   array
                phase steps for second pulse
    vd_data:    nddata
                returned data from previous run (useful when keeping the 
                same dataname but multiple nodenames e.g. testing the same 
                sample at different powers)
    """
    # (JF delete on reading): convert this to a real docstring!!
    # nScans is number of scans you want
    # rd is the repetition delay
    # power_setting is what you want to run power at
    # vd list is a list of the vd's you want to use
    # node_name is the name of the node must specify power
    deblank_us = 1.0
    deadtime_us = 10.0
    tx_phases = r_[0.0,90.0,180.0,270.0]
    ph3_cyc = 0    
    nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)*len(ph3_cyc)
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
            acq_time_ms = configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
            run_scans_time_list.append(time.time())
            run_scans_names.append('configure Rx')
            verifyParams(nPoints=nPoints, nScans=nScans, p90_us=p90_us, tau_us=tau_us)
            run_scans_time_list.append(time.time())
            run_scans_names.append('init')
            init_ppg()
            run_scans_time_list.append(time.time())
            run_scans_names.append('prog')
            Spincore_load([
                ('marker','start',1),
                ('phase_reset',1),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,'ph1',ph1_cyc),
                ('delay',vd),
                ('delay_TTL',1.0),
                ('pulse_TTL',p90_us,'ph2',ph2_cyc),
                ('delay',tau_us),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,ph3_cyc),
                ('delay',deadtime_us),
                ('acquire',acq_time_ms),
                ('delay',repetition),
                ('jumpto','start')
                ])
            run_scans_time_list.append(time.time())
            run_scans_names.append('prog')
            stop_ppg()
            print("\nRUNNING BOARD...\n")
            run_scans_time_list.append(time.time())
            run_scans_names.append('run')
            runBoard()
            run_scans_time_list.append(time.time())
            run_scans_names.append('get data')
            raw_data = getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
            run_scans_time_list.append(time.time())
            run_scans_names.append('shape data')
            data_array=[]
            data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
            print("COMPLEX DATA ARRAY LENGTH:",np.shape(data_array)[0])
            print("RAW DATA ARRAY LENGTH:",np.shape(raw_data)[0])
            dataPoints = float(np.shape(data_array)[0])
            if vd_data is None:
                time_axis = r_[0:dataPoints]/(SW_kHz*1e3)
                vd_data = ndshape([len(vd_list),nScans,len(time_axis),len(vd_list)+1],['vd','nScans','t','indirect']).alloc(dtype=complex128)
                vd_data.setaxis('indirect',zeros(len(vd_list)+1)).set_units('s')
                vd_data.setaxis('vd',vd_list*1e-6).set_units('vd','s')
                vd_data.setaxis('nScans',r_[0:nScans])
                vd_data.setaxis('t',time_axis).set_units('t','s')
            vd_data['vd',index]['nScans',x]['indirect',indirect_idx] = data_array
            vd_data.name(node_name)
            run_scans_time_list.append(time.time())
            this_array = array(run_scans_time_list)
            print("checkpoints:",this_array-this_array[0])
            print("time for each chunk",['%s %0.1f'%(run_scans_names[j],v) for j,v in enumerate(diff(this_array))])
            print("stored scan",x,"for indirect_idx",indirect_idx)
            if nScans > 1:
                vd_data.setaxis('nScans',r_[0:nScans])
    return vd_data
#}}}

