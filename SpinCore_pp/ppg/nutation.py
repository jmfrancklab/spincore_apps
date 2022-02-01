from .. import configureTX,configureRX,init_ppg,stop_ppg,runBoard,getData,verifyParams
from .. import load as spincore_load
import pyspecdata as psp
import numpy as np
import time
#{{{nutation ppg
def run_nutation(nScans, p90_range, adcOffset, carrierFreq_MHz,
        nPoints, nEchoes, p90_us, repetition, tau_us,SW_kHz, ph1_cyc = psp.r_[0,2],
        ph2_cyc = psp.r_[0,2], ret_data=None):
    nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)
    tx_phases = r_[0.0,90.0,180.0,270.0]
    amplitude = 1.0
    deadtime = 10.0
    data_length = 2*nPoints*nEchoes*nPhaseSteps
    deblank_us = 1.0
    for index,val in enumerate(p90_range):
        p90 = val # us
        print("***")
        print("INDEX %d - 90 TIME %f"%(index,val))
        print("***")
        configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        acq_time = configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
        init_ppg()
        spincore_load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',p90_us,'ph1',ph1_cyc),
            ('delay',tau),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',2.0*p90_us,'ph2',ph2_cyc),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',repetition),
            ('jumpto','start')
            ])
        stop_ppg()
        for x in range(nScans):
            print("SCAN NO. %d"%(x+1))
            runBoard()
        raw_data = getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
        data_array = []
        # according to JF, this commented out line
        # should work same as line below and be more effic
        #data = raw_data.view(complex128)
        data_array[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
        print("COMPLEX DATA ARRAY LENGTH:",shape(data)[0])
        print("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
        dataPoints = float(np.shape(data_array)[0])
        time_axis = psp.r_[0:dataPoints]/(SW_kHz*1e3)
        if index == 0:
            ret_data = psp.ndshape([len(p90_range),nScans,len(time_axis)],
                    ['p_90','nScans','t']).alloc(dtype=np.complex128)
            ret_data.setaxis('p_90',p90_range*1e-6).set_units('p_90','s')
            ret_data.setaxis('t',time_axis).set_units('t','s')
            ret_data.setaxis('nScans',psp.r_[0:nScans])
        for x in range(nScans):
            nutation_data['p_90',index]['nScans',x] = data
    SpinCore_pp.stopBoard();

