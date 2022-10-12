from pyspecdata import *
from numpy import *
import os
import sys
import SpinCore_pp
from Instruments import Bridge12,prologix_connection,gigatronics
from serial import Serial
import time
from datetime import datetime
raise RuntimeError("This pulse program has not been updated.  Before running again, it should be possible to replace a lot of the code below with a call to the function provided by the 'generic' pulse program inside the ppg directory!")
fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "FID_mw"
config_dict["date"] = date
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
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
dB_settings = gen_powerlist(config_dict['max_power'],config_dict['power_steps'])
append_dB = [dB_settings[abs(10**(dB_settings/10.-3)-config_dict['max_power']*frac).argmin()]
        for frac in [0.75,0.5,0.25]]
dB_settings = append(dB_settings,append_dB)
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)
tx_phases = r_[0.0,90.0,180.0,270.0]
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
data_length = 2*nPoints*config_dict['nEchoes']*nPhaseSteps
for x in range(config_dict['nScans']):
    print("\n*** *** ***\n")
    print("CONFIGURING TRANSMITTER...")
    SpinCore_pp.configureTX(config_dict['adcOffset'], config_dict['carrierFreq_MHz'], 
            tx_phases, config_dict['amplitude'], nPoints)
    print("\nTRANSMITTER CONFIGURED.")
    print("***")
    print("CONFIGURING RECEIVER...")
    acq_time = SpinCore_pp.configureRX(config_dict['SW_kHz'], nPoints, 1, 
            config_dict['nEchoes'], nPhaseSteps)
    print("ACQUISITION TIME IS",config_dict['acq_time_ms'],"ms")
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
            ('delay_TTL',config_dict['deblank_us']),
            ('pulse_TTL',config_dict['p90_us'],'ph1',r_[0,1,2,3]),
            ('delay',config_dict['deadtime_us']),
            ('acquire',config_dict['acq_time_ms']),
            ('delay',config_dict['repetition_us']),
            ('jumpto','start')
            ])
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',config_dict['deblank_us']),
            ('pulse_TTL',config_dict['p90_us'],0.0),
            ('delay',config_dict['deadtime_us']),
            ('acquire',config_dict['acq_time_ms']),
            ('delay',config_dict['repetition_us']),
            ('jumpto','start')
            ])
    print("\nSTOPPING PROG BOARD...\n")
    SpinCore_pp.stop_ppg();
    print("\nRUNNING BOARD...\n")
    SpinCore_pp.runBoard();
    raw_data = SpinCore_pp.getData(data_length, nPoints, config_dict['nEchoes'], nPhaseSteps)
    raw_data.astype(float)
    data = []
    data[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
    print("COMPLEX DATA ARRAY LENGTH:",np.shape(data)[0])
    print("RAW DATA ARRAY LENGTH:",np.shape(raw_data)[0])
    dataPoints = float(np.shape(data)[0])
    data = nddata(np.array(data),'t')
    if x == 0:
        time_axis = linspace(0.0,config_dict['nEchoes']*nPhaseSteps*config_dict['acq_time_ms']*1e-3,dataPoints)
        data.setaxis('t',time_axis).set_units('t','s')
        data.name('signal')
        data.set_prop('acq_params',config_dict())
    # Define nddata to store along the new power dimension
        DNP_data = ndshape([len(powers)+1,nScans,len(time_axis)],['power','nScans','t']).alloc(dtype=np.complex128)
        DNP_data.setaxis('power',r_[0,powers]).set_units('W')
        DNP_data.setaxis('nScans',r_[0:config_dict['nScans']])
        DNP_data.setaxis('t',time_axis).set_units('t','s')
    DNP_data['power',0]['nScans',x] = data

with Bridge12() as b:
    b.set_wg(True)
    b.set_rf(True)
    b.set_amp(True)
    this_return = b.lock_on_dip(
            config_dict['uw_dip_center_GHz']-config_dict['uw_dip_width_GHz'] / 2,
            config_dict['uw_dip_center_GHz']+config_dict['uw_dip_width_GHz']/2)
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
        print("\n*** *** *** *** ***\n")
        for x in range(config_dict['nScans']):
            print("\n*** *** ***\n")
            print("CONFIGURING TRANSMITTER...")
            SpinCore_pp.configureTX(config_dict['adcOffset'], config_dict['carrierFreq_MHz'], 
                    tx_phases, config_dict['amplitude'], nPoints)
            print("\nTRANSMITTER CONFIGURED.")
            print("***")
            print("CONFIGURING RECEIVER...")
            acq_time = SpinCore_pp.configureRX(config_dict['SW_kHz'], nPoints, 
                    1, config_dict['nEchoes'], nPhaseSteps)
            print("ACQUISITION TIME IS",config_dict['acq_time_ms'],"ms")
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
                    ('delay_TTL',config_dict['deblank_us']),
                    ('pulse_TTL',config_dict['p90_us'],'ph1',r_[0,1,2,3]),
                    ('delay',config_dict['deadtime_us']),
                    ('acquire',config_dict['acq_time_ms']),
                    ('delay',config_dict['repetition_us']),
                    ('jumpto','start')
                    ])
            if not phase_cycling:
                SpinCore_pp.load([
                    ('marker','start',1),
                    ('phase_reset',1),
                    ('delay_TTL',config_dict['deblank_us']),
                    ('pulse_TTL',config_dict['p90_us'],0.0),
                    ('delay',config_dict['deadtime_us']),
                    ('acquire',config_dict['acq_time_ms']),
                    ('delay',config_dict['repetition_us']),
                    ('jumpto','start')
                    ])
            print("\nSTOPPING PROG BOARD...\n")
            SpinCore_pp.stop_ppg();
            print("\nRUNNING BOARD...\n")
            SpinCore_pp.runBoard();
            raw_data = SpinCore_pp.getData(data_length, nPoints, config_dict['nEchoes'], nPhaseSteps)
            raw_data.astype(float)
            data = []
            data[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
            print("COMPLEX DATA ARRAY LENGTH:",np.shape(data)[0])
            print("RAW DATA ARRAY LENGTH:",np.shape(raw_data)[0])
            dataPoints = float(np.shape(data)[0])
            data = nddata(np.array(data),'t')
            DNP_data['power',j+1]['nScans',x] = data
        last_power = this_power
DNP_data.name('signal')
DNP_data.set_prop('meter_powers',meter_powers)
SpinCore_pp.stopBoard();
print("EXITING...")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        print("SAVING FILE IN TARGET DIRECTORY...")
        DNP_data.set_prop('acq_params',config_dict())
        DNP_data.name('signal')
        DNP_data.hdf5_write(filename+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/ODNP'))
        print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
        print("Name of saved data",DNP_data.name())
        print("Units of saved data",DNP_data.get_units('t'))
        print("Shape of saved data",ndshape(DNP_data))
        save_file = False
    except Exception as e:
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        filename = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(filename) is not 0:
            DNP_data.hdf5_write(filename+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
        save_file = False
fl.next('raw data')
fl.image(DNP_data.setaxis('power','#'))
fl.next('abs raw data')
fl.image(abs(DNP_data).setaxis('power','#'))
data.ft('t',shift=True)
fl.next('raw data - ft')
fl.image(DNP_data.setaxis('power','#'))
fl.next('abs raw data - ft')
fl.image(abs(DNP_data).setaxis('power','#'))
fl.show()
