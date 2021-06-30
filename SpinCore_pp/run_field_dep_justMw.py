from pylab import *
from pyspecdata import *
import os
import sys
import SpinCore_pp
from datetime import datetime
import numpy as np
from Instruments import Bridge12,prologix_connection,gigatronics
from serial import Serial
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

mw_freqs = []
#field_axis = r_[3475:3530:0.3]
uneven = 1.0*r_[3,2,1,1,2,3]
uneven /= sum(uneven)
uneven = cumsum(uneven)
start_field = 3502
stop_field = 3508
field_axis = start_field + (stop_field-start_field)*uneven

#field_axis = r_[3504:3506:.1]
print("Here is my field axis:",field_axis)

# Parameters for Bridge12
powers = r_[3.16]
min_dBm_step = 0.5
for x in range(len(powers)):
    print(powers)
    dB_settings = round(10*(log10(powers[x])+3.0)/min_dBm_step)*min_dBm_step # round to nearest min_dBm_step
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)
#}}}

output_name = '500uM_TEMPO_hexane_field_dep_uneven'
node_name = 'field_sweep'
adcOffset = 26 
gamma_eff = (14.890865/3504.85)
#{{{ acq params
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
phase_cycling = True
coherence_pathway = [('ph1',1)]
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
deadtime = 10.0
repetition = 10e6

SW_kHz = 24
nPoints = 1024*2

acq_time = nPoints/SW_kHz # ms
tau_adjust = 0
deblank = 1.0
tau = 1000.
pad = 0
#{{{ setting acq_params dictionary
acq_params = {}
acq_params['adcOffset'] = adcOffset
acq_params['field_axis_G'] = field_axis
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
#}}}

with xepr() as x_server:
    for B0_index,desired_B0 in enumerate(field_axis):
        true_B0 = x_server.set_field(desired_B0)
        print("My field in G is %f"%true_B0)
        time.sleep(3.0)
        carrierFreq_MHz = gamma_eff*true_B0
        print("My frequency in MHz is",carrierFreq_MHz)
        acq_params['carrierFreq_MHz'] = carrierFreq_MHz
        data_length = 2*nPoints*nEchoes*nPhaseSteps
        with Bridge12() as b:
            b.set_wg(True)
            b.set_rf(True)
            b.set_amp(True)
            this_return = b.lock_on_dip(ini_range=(9.819e9,9.825e9))
            dip_f = this_return[2]
            print("Frequency",dip_f)
            mw_freqs.append(dip_f)
            acq_params['mw_freqs'] = mw_freqs
            b.set_freq(dip_f)
            meter_powers = zeros_like(dB_settings)
            for j,this_power in enumerate(r_[dB_settings]):
                print("\n*** *** *** *** ***\n") 
                if j>0 and this_power > last_power + 3:
                    last_power += 3
                    print("SETTING TO...",last_power)
                    b.set_power(last_power)
                    time.sleep(3.0)
                    while this_power > last_power+3:
                        last_power += 3
                        print("SETTING TO...",last_power)
                        b.set_power(last_power)
                        time.sleep(3.0)
                    print("FINALLY - SETTING TO DESIRED POWER")
                    b.set_power(this_power)
                elif j == 0:
                    threshold_power = 10
                    if this_power > threshold_power:
                        next_power = threshold_power + 3
                        while next_power < this_power:
                            print("SETTING To...",next_power)
                            b.set_power(next_power)
                            time.sleep(3.0)
                            next_power += 3
                    b.set_power(this_power)
                else:
                    b.set_power(this_power)
                time.sleep(15)
                with prologix_connection() as p:
                    with gigatronics(prologix_instance=p, address=7) as g:
                        meter_powers = g.read_power()
                        print("POWER READING",meter_powers)
                for x in range(nScans):
                    print("\n*** *** *** *** ***\n")
                    print("\n*** *** ***\n")
                    print("CONFIGURING TRANSMITTER...")
                    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
                    print("\nTRANSMITTER CONFIGURED.")
                    print("***")
                    print("CONFIGURING RECEIVER...")
                    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
                    print("\nRECEIVER CONFIGURED.")
                    print("***")
                    print("\nINITIALIZING PROG BOARD...\n")
                    SpinCore_pp.init_ppg();
                    print("\nLOADING PULSE PROG...\n")
                    if phase_cycling:
                        SpinCore_pp.load([
                            ('marker','start',1),
                            ('phase_reset',1),
                            ('delay_TTL',deblank),
                            ('pulse_TTL',p90,'ph1',r_[0,1,2,3]),
                            ('delay',tau),
                            ('delay_TTL',deblank),
                            ('pulse_TTL',2.0*p90,0),
                            ('delay',deadtime),
                            ('acquire',acq_time),
                            ('delay',repetition),
                            ('jumpto','start')
                            ])
                        #{{{
                    if not phase_cycling:
                        SpinCore_pp.load([
                            ('marker','start',nScans),
                            ('phase_reset',1),
                            ('delay_TTL',deblank),
                            ('pulse_TTL',p90,0.0),
                            ('delay',tau),
                            ('delay_TTL',deblank),
                            ('pulse_TTL',2.0*p90,0.0),
                            ('delay',deadtime),
                            ('acquire',acq_time),
                            ('delay',repetition),
                            ('jumpto','start')
                            ])
                        #}}}
                    print("\nSTOPPING PROG BOARD...\n")
                    SpinCore_pp.stop_ppg();
                    print("\nRUNNING BOARD...\n")
                    SpinCore_pp.runBoard();
                    raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
                    raw_data.astype(float)
                    data_array = []
                    data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
                    print("COMPLEX DATA ARRAY LENGTH:",shape(data_array)[0])
                    print("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
                    dataPoints = float(np.shape(data_array)[0])
                    if x == 0 and B0_index == 0:
                        time_axis = np.linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
                        data = ndshape([len(data_array),nScans,len(field_axis),1],['t','nScans','Field','power']).alloc(dtype=np.complex128)
                        data.setaxis('t',time_axis).set_units('t','s')
                        data.setaxis('nScans',r_[0:nScans])
                        data.setaxis('Field',field_axis)
                        data.setaxis('power',r_[powers])
                        data.name(node_name)
                        data.set_prop('acq_params',acq_params)
                    data['nScans',x]['Field',B0_index]['power',0] = data_array
                last_power = this_power
            SpinCore_pp.stopBoard();
            print("FINISHED B0 INDEX %d..."%B0_index)
            print("\n*** *** ***\n")
print("EXITING...")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        print("SAVING FILE IN TARGET DIRECTORY...")
        data.hdf5_write(date+'_'+output_name+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/field_dependent'))
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
# {{{ once files are saved correctly, the following become obsolete
print(ndshape(data))
if not phase_cycling:
    fl.next('raw data')
    fl.plot(data)
    data.ft('t',shift=True)
    fl.next('ft')
    fl.plot(data.real)
    fl.plot(data.imag)
if phase_cycling:
    data.chunk('t',['ph1','t2'],[4,-1])
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
    data.ft(['ph1'])
    fl.image(data)
    fl.next('data plot')
    fl.plot(data['ph1',1])
    fl.plot(data.imag['ph1',1])
fl.show();quit()
