from pyspecdata import *
import os
import SpinCore_pp
import socket
import sys
import time
from datetime import datetime
#init_logging(level='debug')
fl = figlist_var()
#{{{ Verify arguments compatible with board
raise RuntimeError("This pulse program has not been updated. Before running again, it should be possible to replace a lot of the code below with a call to the function provided by the 'generic' pulse program inside the ppg directory!")
def verifyParams():
    if (nPoints > 16*1024 or nPoints < 1):
        print("ERROR: MAXIMUM NUMBER OF POINTS IS 16384.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED NUMBER OF POINTS.")
    if (nScans < 1):
        print("ERROR: THERE MUST BE AT LEAST 1 SCAN.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED NUMBER OF SCANS.")
    if (p90 < 0.065):
        print("ERROR: PULSE TIME TOO SMALL.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED PULSE TIME.")
    if (tau < 0.065):
        print("ERROR: DELAY TIME TOO SMALL.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED DELAY TIME.")
    return
#}}}
date = datetime.now().strftime('%y%m%d')
clock_correction = 0
output_name = 'EtOH_cap_probe_COSY'
node_name = 'COSY_4'
adcOffset = 31
carrierFreq_MHz = 14.817993
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
p90 = 4.69
deadtime = 10.0
repetition = 8.3e6
SW_kHz = 6.206
nPoints = 1024*2
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
deblank = 1.0
tau = 1000.
pad = 0.
print("ACQUISITION TIME:",acq_time,"ms")
print("TAU DELAY:",tau,"us")
phase_cycling = True
ph1 = r_[0,1,2,3]
ph2 = r_[0,2]
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1 
#{{{ setting acq_params dictionary
acq_params = {}
acq_params['adcOffset'] = adcOffset
acq_params['carrierFreq_MHz'] = carrierFreq_MHz
acq_params['amplitude'] = amplitude
acq_params['nScans'] = nScans
acq_params['nEchoes'] = nEchoes
acq_params['p90_us'] = p90
acq_params['deadtime_us'] = deadtime
acq_params['repetition_us'] = repetition
acq_params['SW_kHz'] = SW_kHz
acq_params['nPoints'] = nPoints
acq_params['tau_adjust_us'] = tau_adjust
acq_params['deblank_us'] = deblank
acq_params['tau_us'] = tau
if phase_cycling:
    acq_params['nPhaseSteps'] = nPhaseSteps
#}}}
data_length = 2*nPoints*nEchoes*nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
# cannot have a delay of 0, so set to minimum SpinCore can take
min_t1 = 0.065 # us (lower limit of SpinCore)
max_t1 = 200*1e3
t1_step = 1.25*1e3
t1_list = r_[min_t1:max_t1:t1_step]
acq_params['t1_list'] = t1_list
for index,val in enumerate(t1_list):
    t1 = val
    print("***")
    print("INDEX %d - t1 %f"%(index,val))
    print("***")
    for x in range(nScans): 
        SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
        acq_params['acq_time_ms'] = acq_time
        SpinCore_pp.init_ppg();
        if phase_cycling:
            SpinCore_pp.load([
                ('marker','start',1),
                ('phase_reset',1),
                ('delay_TTL',deblank),
                ('pulse_TTL',p90,'ph1',r_[0,1,2,3]),
                ('delay',t1),
                ('delay_TTL',deblank),
                ('pulse_TTL',p90,'ph2',r_[0,2]),
                ('delay',deadtime),
                ('acquire',acq_time),
                ('delay',repetition),
                ('jumpto','start')
                ])
        if not phase_cycling:
            SpinCore_pp.load([
                ('marker','start',nScans),
                ('phase_reset',1),
                ('delay_TTL',deblank),
                ('pulse_TTL',p90,0),
                ('delay',t1),
                ('delay_TTL',deblank),
                ('pulse_TTL',p90,0),
                ('delay',deadtime),
                ('acquire',acq_time),
                ('delay',repetition),
                ('jumpto','start')
                ])
        SpinCore_pp.stop_ppg();
        print("\nRUNNING BOARD...\n")
        SpinCore_pp.runBoard();
        raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps)
        raw_data.astype(float)
        data = []
        data[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
        print("COMPLEX DATA ARRAY LENGTH:",np.shape(data)[0])
        print("RAW DATA ARRAY LENGTH:",np.shape(raw_data)[0])
        dataPoints = float(np.shape(data)[0])
        time_axis = np.linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
        data = nddata(np.array(data),'t')
        data.setaxis('t',time_axis).set_units('t','s')
        data.name('signal')
        data.set_prop('acq_params',acq_params)
        if index == 0 and x == 0:
            COSY_data = ndshape([len(t1_list),nScans,len(time_axis)],['t1','nScans','t']).alloc(dtype=np.complex128)
            COSY_data.setaxis('t1',t1_list*1e-6).set_units('t1','s')
            COSY_data.setaxis('nScans',r_[0:nScans])
            COSY_data.setaxis('t',time_axis).set_units('t','s')
        COSY_data['t1',index]['nScans',x] = data
        COSY_data.set_prop('acq_params',acq_params)
SpinCore_pp.stopBoard();
print("EXITING...\n")
print("\n*** *** ***\n")
save_file = True
if phase_cycling:
    COSY_data.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    COSY_data.setaxis('ph1',r_[0,1,2,3]/4.)
    COSY_data.setaxis('ph2',r_[0,2]/4.)
else:
    COSY_data.rename('t','t2')
while save_file:
    try:
        print("SAVING FILE IN TARGET DIRECTORY...")
        COSY_data.name(node_name)
        COSY_data.hdf5_write(date+'_'+output_name+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/COSY'))
        print("*** *** *** *** *** *** *** *** *** *** ***")
        print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
        print("*** *** *** *** *** *** *** *** *** *** ***")
        print(("Name of saved data",COSY_data.name()))
        print(("Units of saved data",COSY_data.get_units('t2')))
        print(("Shape of saved data",ndshape(COSY_data)))
        save_file = False
    except Exception as e:
        print(e)
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            COSY_data.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
fl.next('raw data')
fl.image(COSY_data.setaxis('t1','#'))
fl.next('abs raw data')
fl.image(abs(COSY_data).setaxis('t1','#'))
COSY_data.ft('t2',shift=True)
fl.next('FT raw data')
fl.image(COSY_data.setaxis('t1','#'))
fl.next('FT abs raw data')
fl.image(abs(COSY_data).setaxis('t1','#'))
fl.show();quit()
