from pyspecdata import *
import os
import SpinCore_pp
import socket
import sys
import time
from datetime import datetime
import numpy as np
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
#{{{ for setting EPR magnet
def API_sender(value):
    IP = "jmfrancklab-bruker.syr.edu"
    if len(sys.argv) > 1:
        IP = sys.argv[1]
    PORT = 6001
    print("target IP:", IP)
    print("target port:", PORT)
    MESSAGE = str(value)
    print("SETTING FIELD TO...", MESSAGE)
    sock = socket.socket(socket.AF_INET, # Internet
            socket.SOCK_STREAM) # TCP
    sock.connect((IP, PORT))
    sock.send(MESSAGE)
    sock.close()
    print("FIELD SET TO...", MESSAGE)
    time.sleep(5)
    return
#}}}
#{{{ Edit here to set the actual field
set_field = False
if set_field:
    B0 = 3497 # Determine this from Field Sweep
    API_sender(B0)
#}}}
date = datetime.now().strftime('%y%m%d')
output_name = 'Ni_sol_probe_nutation_amp_3'
adcOffset = 41
carrierFreq_MHz = 14.891248
tx_phases = r_[0.0,90.0,180.0,270.0]
nScans = 1
nEchoes = 1
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
GDS = True
deadtime = 10.0
repetition = 1.3e6
SW_kHz = 50.0
aq = 24564
nPoints = 2048#int(aq/SW_kHz+0.5)#1024*2
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
tau = 5e3#deadtime + acq_time*1e3*(1./8.) + tau_adjust
p90 = 250#us (28x expected 90 time)
print("ACQUISITION TIME:",acq_time,"ms")
print("TAU DELAY:",tau,"us")
data_length = 2*nPoints*nEchoes*nPhaseSteps
amp_range = np.linspace(0,0.5,200)[1:]#,endpoint=False)
datalist = []
#{{{ setting acq_params dictizaonary
acq_params = {}
acq_params['adcOffset'] = adcOffset
acq_params['carrierFreq_MHz'] = carrierFreq_MHz
acq_params['amplitude'] = amp_range
acq_params['nScans'] = nScans
acq_params['nEchoes'] = nEchoes
acq_params['p90_us'] = p90
acq_params['deadtime_us'] = deadtime
acq_params['repetition_us'] = repetition
acq_params['SW_kHz'] = SW_kHz
acq_params['nPoints'] = nPoints
acq_params['tau_adjust_us'] = tau_adjust
acq_params['deblank_us'] = 1.0
acq_params['tau_us'] = tau
#acq_params['pad_us'] = pad 
if phase_cycling:
    acq_params['nPhaseSteps'] = nPhaseSteps
#}}}
for index,val in enumerate(amp_range):
    #p90 = val # us
    amplitude = val # pulse amp, set from 0.0 to 1.0
    print("***")
    print("INDEX %d - AMPLITUDE %f"%(index,val))
    print("***")
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    acq_params['acq_time_ms'] = acq_time
    SpinCore_pp.init_ppg();
    if phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',1.0),
            ('pulse_TTL',p90,'ph1',r_[0,1,2,3]),
            ('delay',tau),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90,'ph2',r_[0,2]),
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
    if phase_cycling:
        for x in range(nScans):
            print("SCAN NO. %d"%(x+1))
            SpinCore_pp.runBoard();
    if not phase_cycling:
        SpinCore_pp.runBoard();
    raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps)
    raw_data.astype(float)
    if GDS:
        datalist=[]
        with GDS_scope() as g:
            g.acquire_mode('HIR')
            for j in range(amp_range):
                datalist.append(g.waveform(ch=1))
    else:
        data = []
    # according to JF, this commented out line
    # should work same as line below and be more effic
        data = raw_data.view(complex128)
        data[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
        print("COMPLEX DATA ARRAY LENGTH:",np.shape(data)[0])
        print("RAW DATA ARRAY LENGTH:",np.shape(raw_data)[0])
        dataPoints = float(np.shape(data)[0])
        time_axis = np.linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
        data = nddata(np.array(data),'t')
        data.setaxis('t',time_axis).set_units('t','s')
        data.name('signal')
        if index == 0:
            nutation_data = ndshape([len(amp_range),len(time_axis)],['amp','t']).alloc(dtype=np.complex128)
            nutation_data.setaxis('amp',amp_range).set_units('amp','arb_units')
            nutation_data.setaxis('t',time_axis).set_units('t','s')
        nutation_data['amp',index] = data
    SpinCore_pp.stopBoard();
nutation_data = concat(datalist,'repeats').reorder('t')







print("EXITING...\n")
print("\n*** *** ***\n")
nutation_data.chunk('t',['ph2','ph1','t2'],[2,4,-1])
nutation_data.setaxis('ph2',r_[0:2]/4).setaxis('ph1',r_[0:4]/4)
nutation_data.set_units('t2','s')
nutation_data.set_prop('postproc_type','spincore_nutation_v2')

save_file = True
while save_file:
    try:
        print("SAVING FILE...")
        nutation_data.set_prop('acq_params',acq_params)
        nutation_data.name('nutation')
        nutation_data.hdf5_write(date+'_'+output_name+'.h5')
        print("Name of saved data",nutation_data.name())
        print("Units of saved data",nutation_data.get_units('t2'))
        print("Shape of saved data",ndshape(nutation_data))
        save_file = False
    except Exception as e:
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            nutation_data.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
        save_file = False
fl.next('raw data')
fl.image(nutation_data)
nutation_data.ft('t2',shift=True)
fl.next('FT raw data')
fl.image(nutation_data)
fl.show()

