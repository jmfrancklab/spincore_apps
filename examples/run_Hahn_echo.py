#{{{ Notes for use
# To run this experiment, please open Xepr on the EPR computer, connect to
# spectrometer, load the experiemnt 'set_field' and enable XEPR API. Then, in a
# separate terminal, run the program XEPR_API_server.py, and wait for it to
# tell you 'I am listening' - then, you should be able to run this program from
# the NMR computer to set the field etc. 

# Note the booleans user_sets_Freq and
# user_sets_Field allow you to run experiments as previously run in this lab.
# If both values are set to True, this is the way we used to run them. If both
# values are set to False, you specify what field you want, and the computer
# will do the rest.
#}}}
import configparser
from pylab import *
from pyspecdata import *
import os
import sys
import SpinCore_pp
from datetime import datetime
import numpy as np
from Instruments.XEPR_eth import xepr
fl = figlist_var()
config = configparser.ConfigParser()
config.read('../exp_params_config.ini')
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
#{{{get parameters from config file
p90 = config.get('acq_params','p90')
deadtime = config.get('acq_params','deadtime')
adcOffset = config.get('acq_params','adc_offset')
tx_phases = config.get('acq_params','tx_phases')
amplitude = config.get('acq_params','amplitude')
deblank = config.get('acq_params','deblank')
tau = config.get('acq_params','tau')
#}}}
output_name = 'test'
node_name = 'echo'

user_sets_Freq = True
user_sets_Field = True

#{{{ set field here
if user_sets_Field:
    # You must enter field set on XEPR here
    true_B0 = 3424.42
    print("My field in G should be %f"%true_B0)
#}}}
#{{{let computer set field
if not user_sets_Field:
    desired_B0 = 3506.50
    with xepr() as x:
        true_B0 = x.set_field(desired_B0)
    print("My field in G is %f"%true_B0)
#}}}
#{{{ set frequency here
if user_sets_Freq:
    carrierFreq_MHz = 14.8978438
    print("My frequency in MHz is",carrierFreq_MHz)
#}}}
#{{{ let computer set frequency
if not user_sets_Freq:
    gamma_eff = (14.897706/3506.5)
    carrierFreq_MHz = gamma_eff*true_B0
    print("My frequency in MHz is",carrierFreq_MHz)
#}}}
nScans = 1
nEchoes = 1
phase_cycling = True
coherence_pathway = [('ph1',1),('ph2',-2)]
date = datetime.now().strftime('%y%m%d')
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
#{{{ note on timing
# all times in microseconds
# acq is in milliseconds
#}}}
repetition = 1e6

SW_kHz = 10
acq_ms = 200.
nPoints = int(acq_ms*SW_kHz+0.5)
# rounding may need to be power of 2
# have to try this out
tau_adjust = 0
pad = 0
#{{{ setting acq_params dictionary
acq_params = {}
acq_params['adcOffset'] = adcOffset
acq_params['carrierFreq_MHz'] = carrierFreq_MHz
acq_params['Ffield_G'] = true_B0
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
acq_params['pad_us'] = pad 
if phase_cycling:
    acq_params['nPhaseSteps'] = nPhaseSteps
#}}}
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
print(("ACQUISITION TIME:",acq_ms,"ms"))
print(("TAU DELAY:",tau,"us"))
print(("PAD DELAY:",pad,"us"))
data_length = 2*nPoints*nEchoes*nPhaseSteps
for x in range(nScans):
    print(("*** *** *** SCAN NO. %d *** *** ***"%(x+1)))
    print("\n*** *** ***\n")
    print("CONFIGURING TRANSMITTER...")
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    print("\nTRANSMITTER CONFIGURED.")
    print("***")
    print("CONFIGURING RECEIVER...")
    acq_ms = SpinCore_pp.configureRX(SW_kHz, nPoints, 1, nEchoes, nPhaseSteps)
    acq_params['acq_time_ms'] = acq_ms
    print(("ACQUISITION TIME IS",acq_ms,"ms"))
    verifyParams()
    print("\nRECEIVER CONFIGURED.")
    print("***")
    print("\nINITIALIZING PROG BOARD...\n")
    SpinCore_pp.init_ppg();
    print("PROGRAMMING BOARD...")
    print("\nLOADING PULSE PROG...\n")
    if phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank),
            ('pulse_TTL',p90,'ph1',r_[0,1,2,3]),
            ('delay',tau),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,'ph2',r_[0,2]),
            ('delay',deadtime),
            ('acquire',acq_ms),
            ('delay',repetition),
            ('jumpto','start')
            ])
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank),
            ('pulse_TTL',p90,0),
            ('delay',tau),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,0),
            ('delay',deadtime),
            ('acquire',acq_ms),
            ('delay',repetition),
            ('jumpto','start')
            ])
    print("\nSTOPPING PROG BOARD...\n")
    SpinCore_pp.stop_ppg();
    print("\nRUNNING BOARD...\n")
    SpinCore_pp.runBoard();
    raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
    raw_data.astype(float)
    data_array = []
    data_array[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
    print(("COMPLEX DATA ARRAY LENGTH:",np.shape(data_array)[0]))
    print(("RAW DATA ARRAY LENGTH:",np.shape(raw_data)[0]))
    dataPoints = float(np.shape(data_array)[0])
    if x == 0:
        time_axis = np.linspace(0.0,nEchoes*nPhaseSteps*acq_ms*1e-3,dataPoints)
        data = ndshape([len(data_array),nScans],['t','nScans']).alloc(dtype=np.complex128)
        data.setaxis('t',time_axis).set_units('t','s')
        data.setaxis('nScans',r_[0:nScans])
        data.name(node_name)
        data.set_prop('acq_params',acq_params)
    data['nScans',x] = data_array
    SpinCore_pp.stopBoard();
print("EXITING...")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        print("SAVING FILE IN TARGET DIRECTORY...")
        data.hdf5_write(date+'_'+output_name+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/Echoes'))
        print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
        print(("Name of saved data",data.name()))
        print(("Units of saved data",data.get_units('t')))
        print(("Shape of saved data",ndshape(data)))
        save_file = False
    except Exception as e:
        print(e)
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            data.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break

data.set_units('t','data')
print(ndshape(data))
print(" *** *** *** ")
print("My field in G is %f"%true_B0)
print("My frequency in MHz is",carrierFreq_MHz)
print(" *** *** *** ")
if not phase_cycling:
    fl.next('raw data')
    fl.plot(data)
    data.ft('t',shift=True)
    fl.next('ft')
    fl.plot(data.real)
    fl.plot(data.imag)
    fl.plot(abs(data),color='k',alpha=0.5)
if phase_cycling:
    data.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    data.setaxis('ph2',r_[0.,2.]/4)
    data.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    if nScans > 1:
        data.setaxis('nScans',r_[0:nScans])
    fl.next('image')
    data.mean('nScans')
    fl.image(data)
    data.ft('t2',shift=True)
    fl.next('image - ft')
    fl.image(data)
    fl.next('image - ft, coherence')
    data.ft(['ph1','ph2'])
    fl.image(data)
    fl.next('data plot')
    data_slice = data['ph1',1]['ph2',-2]
    fl.plot(data_slice, alpha=0.5)
    fl.plot(data_slice.imag, alpha=0.5)
    fl.plot(abs(data_slice), color='k', alpha=0.5)
fl.show();quit()
