from .. import configureTX,configureRX, configureRX, init_ppg, stop_ppg, runBoard, getData
from .. import load as spincore_load
from pyspecdata import *
import time
def run_field_sweep(B0_idx, indirect_len, nScans, adcoffset, carrierFreq_MHz, 
        nPoints, SW_kHz, nEchoes, tau_us, p90_us, repetition_us, output_name, 
        ph1_cyc = r_[0,1,2,3],ph2_cyc = r_[0], sweep_data = None):
        print("About to run run_scans for", B0_index)
        deadtime_us = 10.0
        deblank_us = 1.0
        amplitude = 1.0
        tx_phases = r_[0.0,90.0,180.0,270.0]
        nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)
        total_pts = nPoints*nPhaseSteps
        data_length = 2*nPoints*nEchoes*nPhaseSteps
        for x in range(nScans):
                logger.debug("CONFIGURING TRANSMITTER...")
                configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
                logger.debug("\nTRANSMITTER CONFIGURED.")
                logger.debug("***")
                logger.debug("CONFIGURING RECEIVER...")
                acq_time = configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps)                logger.debug("\nRECEIVER CONFIGURED.")
                logger.debug("***")
                logger.debug("\nINITIALIZING PROG BOARD...\n")
                init_ppg();
                logger.debug("\nLOADING PULSE PROG...\n")
                spincore_load([
                    ('marker','start',1),
                    ('phase_reset',1),
                    ('delay_TTL',deblank_us),
                    ('pulse_TTL',p90_us,'ph1',ph1_cyc),
                    ('delay',tau_us),
                    ('delay_TTL',deblank_us),
                    ('pulse_TTL',2.0*p90_us,'ph2',ph2_cyc),
                    ('delay',deadtime),
                    ('acquire',acq_time),
                    ('delay',repetition_us),
                    ('jumpto','start')
                    ])
                logger.debug("\nSTOPPING PROG BOARD...\n")
                stop_ppg();
                logger.debug("\nRUNNING BOARD...\n")
                runBoard();
                raw_data = getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
                raw_data.astype(float)
                data_array = []
                data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
                dataPoints = float(np.shape(data_array)[0])
                if x ==0 and B0_idx == 0:
                    freqs_dtype = dtype([('Field',double),('carrierFreq',double)])
                    myfreqs = zeros(indirect_len,dtype = freqs_dtype)
                    time_axis = r_[0:dataPoints]/(SW_kHz*1e3)
                    sweep_data = ndshape([len(time_axis),nScans,indirect_len,1],['t','nScans','indirect','power']).alloc(dtype=np.complex128)
                    sweep_data.setaxis('t',time_axis).set_units('t','s')
                    sweep_data.setaxis('nScans',r_[0:nScans])
                    sweep_data.setaxis('indirect',myfreqs)
                    sweep_data.setaxis('power',r_[powers])
                if sweep_data == None:
                    time_axis = r_[0:dataPoints]/(SW_kHz*1e3)
                    data_array = nddata(array(data_array),'t')
                    data_array.setaxis('t',time_axis)
                    sweep_data.name('Field_sweep')
                sweep_data['nScans',x]['indirect',B0_idx]['power',0] = data_array
                logger.debug(strm("FINISHED B0 INDEX %d..."%B0_index))
                logger.debug("\n*** *** ***\n")
                return sweep_data

