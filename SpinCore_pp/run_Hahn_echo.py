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

from pylab import *
from pyspecdata import *
import os
import sys
import SpinCore_pp
from datetime import datetime
import numpy as np
from Instruments.XEPR_eth import xepr
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

output_name = '50mM_4AT_AOT_w11_cap_probe_echo'
node_name = 'echo_noPower_2'
adcOffset = 33

user_sets_Freq = True
user_sets_Field = True

#{{{ set field here
if user_sets_Field:
    # You must enter field set on XEPR here
    true_B0 = 3505.8 
    print("My field in G should be %f"%true_B0)
#}}}
#{{{let computer set field
if not user_sets_Field:
    desired_B0 = 3488.17
    with xepr() as x:
        true_B0 = x.set_field(desired_B0)
        print("My field in G is %f"%true_B0)
repetition = 15e6
#}}}
#{{{ set frequency here
if user_sets_Freq:
    carrierFreq_MHz = 14.817993
    print("My frequency in MHz is",carrierFreq_MHz)
#}}}za
#{{{ let computer set frequency
if not user_sets_Freq:
    gamma_eff = 0.0042490125
    carrierFreq_MHz = gamma_eff*true_B0
    print("My frequency in MHz is",carrierFreq_MHz)
#}}}

tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 64
nEchoes = 1
phase_cycling = True
coherence_pathway = [('ph1',1),('ph2',-2)]
date = datetime.now().strftime('%y%m%d')
if phase_cycling:
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
p90 = 4.69 
deadtime = 10
repetition = 0.8e6

SW_kHz = 24
nPoints = 1024*2

acq_time = nPoints/SW_kHz # ms
tau_adjust = 0
deblank = 1.0
#tau = deadtime + acq_time*1e3*(1./8.) + tau_adjust
tau = 1000.
pad = 0
#pad = 2.0*tau - deadtime - acq_time*1e3 - deblank
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
print(("ACQUISITION TIME:",acq_time,"ms"))
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
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, 1, nEchoes, nPhaseSteps)
    acq_params['acq_time_ms'] = acq_time
    # acq_time is in msec!
    print(("ACQUISITION TIME IS",acq_time,"ms"))
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
            ('pulse_TTL',p90,'ph1',r_[0,2]),
            ('delay',tau),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,'ph2',r_[0,2]),
            ('delay',deadtime),
            ('acquire',acq_time),
            #('delay',pad),
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
            ('acquire',acq_time),
            #('delay',pad),
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
        time_axis = np.linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
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
if phase_cycling:
    data.chunk('t',['ph2','ph1','t2'],[2,2,-1])
    data.setaxis('ph2',r_[0.,2.]/4)
    data.setaxis('ph1',r_[0.,2.]/4)
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
    fl.plot(data['ph1',1]['ph2',0])
    fl.plot(data.imag['ph1',1]['ph2',0])
fl.show();quit()
