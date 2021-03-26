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
field_axis = linspace(3485.0,3495.0,3)
print("Here is my field axis:",field_axis)

#{{{ for setting microwave power
def gen_powerlist(max_power, steps, min_dBm_step=0.5):
    "generate a list of (roughly) evenly spaced powers up to max_power"
    lin_steps = steps
    def det_allowed(lin_steps):
        powers = r_[0:max_power:1j*lin_steps][1:]
        vectorize(powers)
        rdB_settings = ones_like(powers)
        for x in range(len(powers)):
            rdB_settings[x] = round(10*(log10(powers[x])+3.0)/min_dBm_step)*min_dBm_step # round to nearest min_dBm_step
        return unique(rdB_settings)
    dB_settings = det_allowed(lin_steps)
    while len(dB_settings) < steps-1:
        lin_steps += 1
        dB_settings = det_allowed(lin_steps)
        if lin_steps >= 200:
            raise ValueError("I think I'm in an infinite loop -- maybe you"
                    "can't request %d steps between 0 and %f W without going"
                    "below %f a step?")%(steps,max_power,min_dBm_step)
    return dB_settings

# Parameters for Bridge12
max_power = 4.0
power_steps = 2
dB_settings = gen_powerlist(max_power,power_steps)
#append_dB = [dB_settings[abs(10**(dB_settings/10.-3)-max_power*frac).argmin()]
#        for frac in [0.75,0.5,0.25]]
#dB_settings = append(dB_settings,append_dB)
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)
#}}}

output_name = 'Ni_cap_probe_field_dep_mw_1'
adcOffset = 45
gamma_eff = 0.004249215249
#{{{ acq params
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 2
nEchoes = 1
phase_cycling = True
coherence_pathway = [('ph1',1),('ph2',-2)]
date = datetime.now().strftime('%y%m%d')
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
p90 = 4.69
deadtime = 10.0
repetition = 1e6
#repetition = .7e6

SW_kHz = 24
nPoints = 1024*2

acq_time = nPoints/SW_kHz # ms
tau_adjust = 0
deblank = 1.0
tau = 3500.
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
                    ('pulse_TTL',p90,'ph1',r_[0,1,2,3]),
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
            if x == 0 and B0_index == 0:
                time_axis = np.linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
                data = ndshape([len(data_array),nScans,len(field_axis),len(powers)+1],['t','nScans','Field','power']).alloc(dtype=np.complex128)
                data.setaxis('t',time_axis).set_units('t','s')
                data.setaxis('nScans',r_[0:nScans])
                data.setaxis('Field',field_axis)
                data.setaxis('power',r_[0,powers])
                data.name('signal')
                data.set_prop('acq_params',acq_params)
        data['nScans',x]['Field',B0_index]['power',0] = data_array

        # Begin power loop
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
            for j,this_power in enumerate(dB_settings):
                print("\n*** *** *** *** ***\n")
                print("SETTING THIS POWER",this_power,"(",dB_settings[j-1],powers[j],"W)")
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
                        meter_powers[j] = g.read_power()
                        print("POWER READING",meter_powers[j])
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
                            ('pulse_TTL',2.0*p90,'ph2',r_[0,2]),
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
                    data['nScans',x]['Field',B0_index]['power',j+1] = data_array
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
    fl.plot(data['ph1',1]['ph2',0])
    fl.plot(data.imag['ph1',1]['ph2',0])
fl.show();quit()
