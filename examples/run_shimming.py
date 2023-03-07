"""ppg for obtaining performing shimming calibration
=====================================================
The following is used when the shims are replaced or moved in any way. When moved the calibration or settings for the z and y shims need to be recalculated for certainty. Here, the user can calculated the appropriate voltage setting for each shim for optimal signal
"""
#{{{ Notes for use # To run this experiment, please open Xepr on the EPR computer, connect to # spectrometer, and enable XEPR API. Then, in a # separate terminal, run the program XEPR_API_server.py, and wait for it to # tell you 'I am listening' - then, you should be able to run this program from # the NMR computer to set the field etc.  # Note the booleans user_sets_Freq and
# user_sets_Field allow you to run experiments as previously run in this lab.
# If both values are set to True, this is the way we used to run them. If both
# values are set to False, you specify what field you want, and the computer
# will do the rest.
#}}}
from pylab import *
from pyspecdata import *
import os, sys
import SpinCore_pp
from datetime import datetime
import numpy as np
from Instruments.XEPR_eth import xepr
from Instruments import HP6623A, prologix_connection
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
#{{{Parameters for sample - user should check and edit as needed
output_name = 'NiSO4'
node_name = 'shims_addr5_Z_yOpt'
adcOffset = 32
carrierFreq_MHz = 14.890000
field = 3504.0
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 4
nEchoes = 1
phase_cycling = True
coherence_pathway = [('ph1',1),('ph2',-2)]
date = datetime.now().strftime('%y%m%d')
#{{{ note on timing
# all times in microseconds
# acq is in milliseconds
#}}}
p90 = 4.51
deadtime = 10
repetition = 1e6
SW_kHz = 1.9
acq_ms = 1024
nPoints = int(acq_ms*SW_kHz+0.5)
# rounding may need to be power of 2
# have to try this out
tau_adjust = 0
deblank = 1.0
tau = 2500. + deadtime
pad = 0
#}}}
#The standard procedure is to manually se the field and frequency but this can later be updated when the config file branch is merged
#{{{set field
with xepr() as x:
    true_B0 = x.set_field(field)
print("My field in G is %f"%field)
#}}}
#{{{phase cycling steps
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
#}}}    
#{{{ verify info is okay
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#}}}
#{{{set up voltage info for the test 
data_length = 2*nPoints*nEchoes*nPhaseSteps
voltage_array = r_[0.0:0.15:0.01]
current_readings = ones_like(voltage_array)
voltage_readings = ones_like(voltage_array)
# channel that is currently being investigated
test_ch = 3
# channel that was previously investigated/has predetermined value that you want to set 
# set_ch : (ch #, voltage setting)
set_ch = [(2,0.1)]
#}}}
#{{{ Run actual ppg
with prologix_connection() as p:
    with HP6623A(prologix_instance=p, address=5) as HP:
        for index,this_val in enumerate(voltage_array):
            if index == 0:
                HP.set_voltage(set_ch[0][0],set_ch[0][1])
                HP.set_voltage(test_ch,0.0)
                HP.set_current(test_ch,0.0)
                this_curr = HP.get_current(test_ch)
                this_volt = HP.get_voltage(test_ch)
                current_readings[0] = this_curr
                voltage_readings[0] = this_volt
                HP.output(test_ch,False)
                HP.output(set_ch[0][0],True)
            else:
                HP.set_voltage(test_ch,this_val)
                this_curr = HP.get_current(test_ch)
                this_volt = HP.get_voltage(test_ch)
                current_readings[index] = this_curr
                voltage_readings[index] = this_volt
                HP.output(test_ch,True)
                get_volt_ch1 = HP.get_voltage(1)
                get_volt_ch2 = HP.get_voltage(2)
                get_volt_ch3 = HP.get_voltage(3)
                get_volt = [('ch1',get_volt_ch1),
                        ('ch2',get_volt_ch2),
                        ('ch3',get_volt_ch3)]
                acq_params['shim_readings'] = get_volt
            print("CURRENT READING IS: %f"%this_curr)
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
                if index == 0 and x == 0:
                    time_axis = np.linspace(0,nEchoes*nPhaseSteps*acq_ms*1e-3,int(dataPoints))
                    shim_data = ndshape([len(data_array),nScans,len(current_readings)],['t','nScans','I']).alloc(dtype=complex128)
                    shim_data.setaxis('t',time_axis).set_units('t','s')
                    shim_data.setaxis('nScans',r_[0:nScans])
                    shim_data.setaxis('I',current_readings).set_units('I','A')
                    shim_data.name(node_name)
                    acq_params['voltage_setting'] = voltage_array
                    acq_params['voltage_reading'] = voltage_readings
                    acq_params['current_reading'] = current_readings
                    acq_params['shim_settings'] = set_ch
                    shim_data.set_prop('acq_params',acq_params)
                shim_data['nScans',x]['I',index] = data_array
                SpinCore_pp.stopBoard();
        print("Turning shim power off")
        HP.output(test_ch,False)
print("EXITING...")
print("\n*** *** ***\n")
#}}}
#{{{save acquisition parameters
acq_params = {j: eval(j) for j in dir() if j in [
    "adcOffset",
    "carrierFreq_MHz",
    "amplitude",
    "true_B0",
    "nScans",
    "nEchoes",
    "p90_us",
    "deadtime_us",
    "repetition_us",
    "SW_kHz",
    "nPoints",
    "deblank_us",
    "tau_us",
    "nPhaseSteps",
    ]
    }
echo_data.set_prop("acq_params",acq_params)
#}}}
#{{{saving file
save_file = True
while save_file:
    try:
        print("SAVING FILE IN TARGET DIRECTORY...")
        shim_data.hdf5_write(date+'_'+output_name+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/Echoes'))
        print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
        print(("Name of saved data",shim_data.name()))
        print(("Units of saved data",shim_data.get_units('t')))
        print(("Shape of saved data",ndshape(shim_data)))
        save_file = False
    except Exception as e:
        print(e)
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            shim_data.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
#}}}
#{{{Plotting
shim_data.set_units('t','data')
print(ndshape(shim_data))
print(" *** *** *** ")
print("My field in G is %f"%true_B0)
print("My frequency in MHz is",carrierFreq_MHz)
print(" *** *** *** ")
if not phase_cycling:
    fl.next('raw data')
    fl.image(shim_data)
    data.ft('t',shift=True)
    fl.next('ft')
    fl.image(abs(shim_data), color='k', alpha=0.5)
if phase_cycling:
    shim_data.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    shim_data.setaxis('ph2',r_[0.,2.]/4)
    shim_data.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    if nScans > 1:
        shim_data.setaxis('nScans',r_[0:nScans])
    fl.next('image')
    shim_data.mean('nScans')
    fl.image(shim_data.C.setaxis('I','#'))
    t2_max = shim_data.getaxis('t2')[-1]
    shim_data -= shim_data['t2':(0.75*t2_max,None)].C.mean('t2')
    shim_data.ft('t2',shift=True)
    fl.next('image - ft')
    fl.image(shim_data.C.setaxis('I','#'))
    fl.next('image - ft, coherence')
    shim_data.ft(['ph1','ph2'])
    fl.image(shim_data.C.setaxis('I','#'))
    fl.next('data plot')
    data_slice = shim_data['ph1',1]['ph2',-2]
    fl.plot(data_slice, alpha=0.5)
    fl.plot(abs(data_slice), color='k', alpha=0.5)
fl.show()
#}}}
