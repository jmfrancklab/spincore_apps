#{{{ note on phase cycling
'''
FOR PHASE CYCLING: Provide both a phase cycle label (e.g.,
'ph1', 'ph2') as str and an array containing the indices
(i.e., registers) of the phases you which to use that are
specified in the numpy array 'tx_phases'.  Note that
specifying the same phase cycle label will loop the
corresponding phase steps together, regardless of whether
the indices are the same or not.
    e.g.,
    The following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph1',r_[2,3]),
    will provide two transients with phases of the two pulses (p1,p2):
        (0,2)
        (1,3)
    whereas the following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph2',r_[2,3]),
    will provide four transients with phases of the two pulses (p1,p2):
        (0,2)
        (0,3)
        (1,2)
        (1,3)
FURTHER: The total number of transients that will be
collected are determined by both nScans (determined when
calling the appropriate marker) and the number of steps
calculated in the phase cycle as shown above.  Thus for
nScans = 1, the SpinCore will trigger 2 times in the first
case and 4 times in the second case.  for nScans = 2, the
SpinCore will trigger 4 times in the first case and 8 times
in the second case.
'''
#}}}
from pylab import *
from pyspecdata import *
from numpy import *
import os
import sys
import SpinCore_pp
from Instruments import Bridge12,prologix_connection,gigatronics
from serial import Serial
from datetime import datetime
import time

fl = figlist_var()
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

# Parameters for Bridge12
max_power = 2.0
power_steps = 10
dB_settings = gen_powerlist(max_power,power_steps)
append_dB = [dB_settings[abs(10**(dB_settings/10.-3)-max_power*frac).argmin()]
        for frac in [0.75,0.5,0.25]]
dB_settings = append(dB_settings,append_dB)
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)

date = datetime.now().strftime('%y%m%d')
output_name = 'TEMPOL_CPMG_DNP_1'
adcOffset = 42
carrierFreq_MHz = 14.896597
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
p90_us = 4.625765
deadtime_us = 10.0
repetition_us = 15e6
deblank_us = 1.0
marker = 1.0

SW_kHz = 4.0
nPoints = 128
acq_time_ms = nPoints/SW_kHz # ms

tau_extra = 5000.0 # us, must be more than deadtime and more than deblank
pad_start = tau_extra - deadtime_us
pad_end = tau_extra - deblank_us*2 # marker + deblank
twice_tau = deblank_us + 2*p90_us + deadtime_us + pad_start + acq_time_ms*1e3 + pad_end + marker
tau_us = twice_tau/2.0

nScans = 16
nEchoes = 64
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 2
if not phase_cycling:
    nPhaseSteps = 1 
data_length = 2*nPoints*nEchoes*nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
for k in range(nScans):
    print("\n*** *** ***\n")
    print("CONFIGURING TRANSMITTER...")
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    print("\nTRANSMITTER CONFIGURED.")
    print("***")
    print("CONFIGURING RECEIVER...")
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    acq_params['acq_time_ms'] = acq_time_ms
    print("\nRECEIVER CONFIGURED.")
    print("***")
    print("\nINITIALIZING PROG BOARD...\n")
    SpinCore_pp.init_ppg();
    print("\nLOADING PULSE PROG...\n")
    if phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',p90_us,'ph1',r_[0,2]),
                ('delay',tau_us),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,1),
                ('delay',deadtime_us),
                ('delay',pad_start),
                ('acquire',acq_time_ms),
                ('delay',pad_end),
                ('marker','echo_label',(nEchoes-1)), # 1 us delay
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,1),
                ('delay',deadtime_us),
                ('delay',pad_start),
                ('acquire',acq_time_ms),
                ('delay',pad_end),
                ('jumpto','echo_label'), # 1 us delay
                ('delay',repetition_us),
                ('jumpto','start')
                ])
        if not phase_cycling:
            SpinCore_pp.load([
                ('marker','start',1),
                ('phase_reset',1),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',p90_us,0.0),
                ('delay',tau_us),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,0.0),
                ('delay',deadtime_us),
                ('delay',pad_start),
                ('acquire',acq_time_ms),
                ('delay',pad_end),
                ('marker','echo_label',(nEchoes-1)), # 1 us delay
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,0.0),
                ('delay',deadtime_us),
                ('delay',pad_start),
                ('acquire',acq_time_ms),
                ('delay',pad_end),
                ('jumpto','echo_label'), # 1 us delay
                ('delay',repetition_us),
                ('jumpto','start')
                ])
    print("\nSTOPPING PROG BOARD...\n")
    SpinCore_pp.stop_ppg();
    print("\nRUNNING BOARD...\n")
    SpinCore_pp.runBoard();
    raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
    raw_data.astype(float)
    data = []
    data[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
    print("COMPLEX DATA ARRAY LENGTH:",shape(data)[0])
    print("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
    dataPoints = float(shape(data)[0])
    time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time_ms*1e-3,dataPoints)
    data = nddata(array(data),'t')
    data.setaxis('t',time_axis).set_units('t','s')
    data.name('signal')
    # Define nddata to store along the new power dimension
    if k == 0:
        DNP_data = ndshape([len(powers)+1,nScans,len(time_axis)],['power','nScans','t']).alloc(dtype=complex128)
        DNP_data.setaxis('power',r_[0,powers]).set_units('W')
        DNP_data.setaxis('nScans',r_[0:nScans])
        DNP_data.setaxis('t',time_axis).set_units('t','s')
    DNP_data['power',0]['nScans',k] = data
#raw_input("CONNECT AND TURN ON BRIDGE12...")
with Bridge12() as b:
    b.set_wg(True)
    b.set_rf(True)
    b.set_amp(True)
    this_return = b.lock_on_dip(ini_range=(9.815e9,9.83e9))
    dip_f = this_return[2]
    print("Frequency",dip_f)
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
        for k in range(nScans):
            print("\n*** *** *** *** ***\n")
            print("\n*** *** ***\n")
            print("CONFIGURING TRANSMITTER...")
            SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
            print("\nTRANSMITTER CONFIGURED.")
            print("***")
            print("CONFIGURING RECEIVER...")
            acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
            # acq_time is in msec!
            print("\nRECEIVER CONFIGURED.")
            print("***")
            # MORE CODE GOES HERE
            print("\nINITIALIZING PROG BOARD...\n")
            SpinCore_pp.init_ppg();
            print("\nLOADING PULSE PROG...\n")
            if phase_cycling:
                SpinCore_pp.load([
                    ('marker','start',1),
                    ('phase_reset',1),
                        ('delay_TTL',deblank_us),
                        ('pulse_TTL',p90_us,'ph1',r_[0,2]),
                        ('delay',tau_us),
                        ('delay_TTL',deblank_us),
                        ('pulse_TTL',2.0*p90_us,1),
                        ('delay',deadtime_us),
                        ('delay',pad_start),
                        ('acquire',acq_time_ms),
                        ('delay',pad_end),
                        ('marker','echo_label',(nEchoes-1)), # 1 us delay
                        ('delay_TTL',deblank_us),
                        ('pulse_TTL',2.0*p90_us,1),
                        ('delay',deadtime_us),
                        ('delay',pad_start),
                        ('acquire',acq_time_ms),
                        ('delay',pad_end),
                        ('jumpto','echo_label'), # 1 us delay
                        ('delay',repetition_us),
                        ('jumpto','start')
                        ])
                if not phase_cycling:
                    SpinCore_pp.load([
                        ('marker','start',nScans),
                        ('phase_reset',1),
                        ('delay_TTL',deblank_us),
                        ('pulse_TTL',p90_us,0.0),
                        ('delay',tau_us),
                        ('delay_TTL',deblank_us),
                        ('pulse_TTL',2.0*p90_us,0.0),
                        ('delay',deadtime_us),
                        ('delay',pad_start),
                        ('acquire',acq_time_ms),
                        ('delay',pad_end),
                        ('marker','echo_label',(nEchoes-1)), # 1 us delay
                        ('delay_TTL',deblank_us),
                        ('pulse_TTL',2.0*p90_us,0.0),
                        ('delay',deadtime_us),
                        ('delay',pad_start),
                        ('acquire',acq_time_ms),
                        ('delay',pad_end),
                        ('jumpto','echo_label'), # 1 us delay
                        ('delay',repetition_us),
                        ('jumpto','start')
                        ])
            print("\nSTOPPING PROG BOARD...\n")

            SpinCore_pp.stop_ppg();
            print("\nRUNNING BOARD...\n")
            SpinCore_pp.runBoard();
            raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
            raw_data.astype(float)
            data = []
            data[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
            print("COMPLEX DATA ARRAY LENGTH:",shape(data)[0])
            print("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
            dataPoints = float(shape(data)[0])
            time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time_ms*1e-3,dataPoints)
            data = nddata(array(data),'t')
            data.setaxis('t',time_axis).set_units('t','s')
            data.name('signal')
            DNP_data['power',j+1]['nScans',k] = data
        last_power = this_power
DNP_data.name('signal')
DNP_data.set_prop('meter_powers',meter_powers)
SpinCore_pp.stopBoard();
print("EXITING...")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        print("SAVING FILE...")
        acq_params = {j: eval(j) for j in dir() if j in [
            "adcOffset",
            "carrierFreq_MHz",
            "amplitude",
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
        DNP_data.set_prop('acq_params',acq_params)
        DNP_data.name('signal')
        DNP_data.hdf5_write(date+'_'+output_name+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/DNP'))
        print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
        print("Name of saved data",DNP_data.name())
        print("Units of saved data",DNP_data.get_units('t'))
        print("Shape of saved data",ndshape(DNP_data))
        save_file = False
    except Exception as e:
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            DNP_data.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
        save_file = False
fl.next('raw data')
fl.image(DNP_data)
fl.next('abs raw data')
fl.image(abs(DNP_data))
data.ft('t',shift=True)
fl.next('raw data - ft')
fl.image(DNP_data)
fl.next('abs raw data - ft')
fl.image(abs(DNP_data))
fl.show()
