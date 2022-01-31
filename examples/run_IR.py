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
output_name = 'TEMPOL_289uM_heat_exch_0C'
node_name = 'FIR_noPower_end'
adcOffset = 28
carrierFreq_MHz = 14.549013
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
p90 = 1.781
deadtime = 10.0
repetition = 4e6
SW_kHz = 10
acq_ms = 200.
nPoints = int(acq_ms*SW_kHz+0.5)
# rounding may need to be power of 2
# have to try this out
tau_adjust = 0
deblank = 1.0
#tau = deadtime + acq_time*1e3*(1./8.) + tau_adjust
tau = 3500
pad = 0
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
print("ACQUISITION TIME:",acq_time,"ms")
print("TAU DELAY:",tau,"us")
phase_cycling = True
ph1 = r_[0,2]
ph2 = r_[0,2]
if phase_cycling:
    nPhaseSteps = 4
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
#vd_list = r_[5e1,2e5,4e5,6e5,8e5]
#        1e6,1.2e6,1.4e6,1.6e6,1.8e6,2e6]
#vd_list = r_[5e1,9.1e4,1.8e5,2.7e5,3.6e5,
#        #4.5e5,5.5e5,6.4e5,7.3e5,8.2e5,9.1e5,1e6]
#vd_list = r_[5e1,1.8e4,3.6e4,5.5e4,7.3e4,9.1e4,
#        1.8e5,3.44e5,5.08e5,6.72e5,8.36e5,1e6]
#vd_list = r_[5e1,1.8e4,3.6e4,5.5e4,7.3e4,9.1e4,
#       1.8e5,3.44e5,5.08e5,6.72e5,8.36e5,1e6]
#vd_list = np.linspace(5e1,1.8e5,32)
#vd_list = np.linspace(5e1,12e6,12)
#vd_list = np.linspace(5e1,15e6,16)#5) 
#vd_list = np.linspace(5e1,10e6,16)
#vd_list = np.linspace(5e1,4e6,16)
vd_list = np.linspace(5e1,6e6,16)
#vd_list = np.linspace(5e1,3e6,15)
#vd_list = np.linspace(5e1,8e6,16)

for index,val in enumerate(vd_list):
    vd = val
    print("***")
    print("INDEX %d - VARIABLE DELAY %f"%(index,val))
    print("***")
    for x in range(nScans): 
        SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
        acq_params['acq_time_ms'] = acq_time
        SpinCore_pp.init_ppg();
        if phase_cycling:
            phase_cycles = dict(ph1 = r_[0,2],
                    ph2 = r_[0,2])
            SpinCore_pp.load([
                ('marker','start',1),
                ('phase_reset',1),
                ('delay_TTL',1.0),
                ('pulse_TTL',2.0*p90,'ph1',phase_cycles['ph1']),
                ('delay',vd),
                ('delay_TTL',1.0),
                ('pulse_TTL',p90,'ph2',phase_cycles['ph2']),
                ('delay',tau),
                ('delay_TTL',1.0),
                ('pulse_TTL',2.0*p90,0),
                ('delay',deadtime),
                ('acquire',acq_time),
                ('delay',repetition),
                ('jumpto','start')
                ])
        if not phase_cycling:
            SpinCore_pp.load([
                ('marker','start',nScans),
                ('phase_reset',1),
                ('delay_TTL',1.0),
                ('pulse_TTL',2.0*p90,0.0),
                ('delay',vd),
                ('delay_TTL',1.0),
                ('pulse_TTL',p90,0.0),
                ('delay',tau),
                ('delay_TTL',1.0),
                ('pulse_TTL',2.0*p90,0.0),
                ('delay',deadtime),
                ('acquire',acq_time),
                ('delay',repetition),
                ('jumpto','start')
                ])
        SpinCore_pp.stop_ppg();
        print("\nRUNNING BOARD...\n")
        SpinCore_pp.runBoard();
        raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
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
            vd_data = ndshape([len(vd_list),nScans,len(time_axis)],['vd','nScans','t']).alloc(dtype=np.complex128)
            vd_data.setaxis('vd',vd_list*1e-6).set_units('vd','s')
            vd_data.setaxis('nScans',r_[0:nScans])
            vd_data.setaxis('t',time_axis).set_units('t','s')
        vd_data['vd',index]['nScans',x] = data
        vd_data.set_prop('acq_params',acq_params)
SpinCore_pp.stopBoard();
print("EXITING...\n")
print("\n*** *** ***\n")
save_file = True
if phase_cycling:
    phcyc_names = list(phase_cycles.keys())
    phcyc_names.sort(reverse=True)
    phcyc_dims = [len(phase_cycles[j]) for j in phcyc_names]
    vd_data.chunk('t',phcyc_names+['t2'],phcyc_dims+[-1])
    vd_data.setaxis('ph1',ph1/4.)
    vd_data.setaxis('ph2',ph2/4.)
else:
    vd_data.rename('t','t2')
while save_file:
    try:
        print("SAVING FILE IN TARGET DIRECTORY...")
        vd_data.name(node_name)
        vd_data.hdf5_write(date+'_'+output_name+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/ODNP'))
        print("*** *** *** *** *** *** *** *** *** *** ***")
        print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
        print("*** *** *** *** *** *** *** *** *** *** ***")
        print(("Name of saved data",vd_data.name()))
        print(("Units of saved data",vd_data.get_units('t2')))
        print(("Shape of saved data",ndshape(vd_data)))
        save_file = False
    except Exception as e:
        print(e)
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER dNEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            vd_data.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
vd_data.reorder(['ph1','ph2','vd','t2'])
fl.next('raw data')
fl.image(vd_data.setaxis('vd','#'))
fl.next('abs raw data')
fl.image(abs(vd_data).setaxis('vd','#'))
vd_data.ft(['ph1','ph2'])
vd_data.ft('t2',shift=True)
fl.next('FT raw data')
fl.image(vd_data.setaxis('vd','#'))
fl.next('FT abs raw data')
fl.image(abs(vd_data).setaxis('vd','#')['t2':(-1e3,1e3)])
fl.show();quit()
