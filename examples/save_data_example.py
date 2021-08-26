from numpy import *
from numpy.random import rand
from pyspecdata import *
from Instruments import *
import os
import sys
import time
import random
long_delay = time.sleep(5)
short_delay = time.sleep(1)
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
#{{{ params for Bridge 12/power
dB_settings = gen_powerlist(4,30.0)
powers =1e-3*10**(dB_settings/10.)
#}}}
#{{{ time of pulse prog
DNP_data = None
#{{{ pulse prog
def run_scans(nScans, power_idx, field_idx, DNP_data=None):
    """run nScans and slot them into he power_idx index of DNP_data -- assume
    that the first time this is run, it will be run with DNP_data=None and that
    after that, you will pass in DNP_data
    
    assume that the power axis is 1 longer than the "powers" array
    (note that powers and other parameters are defined globally w/in the
    script, as this function is not designed to be moved outside the module
    """
    print("about to run acquisition for POWER INDEX:",power_idx)
    print("about to run acquisition for FIELD INDEX:",field_idx)
    ph1_cyc = r_[0,1,2,3]
    ph2_cyc = r_[0]
    nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)
    data_length = 2*2048*1*nPhaseSteps
    for x in range(nScans):
        run_scans_time_list = [time.time()]
        run_scans_names = ['configure']
        print("*** *** *** SCAN NO. %d *** *** ***"%(x+1))
        print("\n*** *** ***\n")
        print("CONFIGURING TRANSMITTER...")
        #SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        print("\nTRANSMITTER CONFIGURED.")
        run_scans_time_list.append(time.time())
        run_scans_names.append('configure Rx')
        print("***")
        print("CONFIGURING RECEIVER...")
        #acq_time_ms = SpinCore_pp.configureRX(SW_kHz, nPoints, 1, nEchoes, nPhaseSteps)
        # acq_time_ms is in msec!
        acq_time_ms = 85.3
        print("ACQUISITION TIME IS",acq_time_ms,"ms")
        #verifyParams(nPoints=nPoints, nScans=nScans, p90_us=p90_us, tau_us=tau_us)
        run_scans_time_list.append(time.time())
        run_scans_names.append('init')
        print("\nRECEIVER CONFIGURED.")
        print("***")
        print("\nINITIALIZING PROG BOARD...\n")
        #SpinCore_pp.init_ppg()
        run_scans_time_list.append(time.time())
        run_scans_names.append('prog')
        print("PROGRAMMING BOARD...")
        print("\nLOADING PULSE PROG...\n")
        #SpinCore_pp.load([
        #    ('marker','start',1),
        #    ('phase_reset',1),
        #    ('delay_TTL',deblank_us),
        #    ('pulse_TTL',p90_us,'ph1',ph1_cyc),
        #    ('delay',tau_us),
        #    ('delay_TTL',deblank_us),
        #    ('pulse_TTL',2.0*p90_us,'ph2',ph2_cyc),
        #    ('delay',deadtime_us),
        #    ('acquire',acq_time_ms),
        #    ('delay',repetition_us),
        #    ('jumpto','start')
        #    ])
        run_scans_time_list.append(time.time())
        run_scans_names.append('prog')
        print("\nSTOPPING PROG BOARD...\n")
        #SpinCore_pp.stop_ppg()
        run_scans_time_list.append(time.time())
        run_scans_names.append('run')
        print("\nRUNNING BOARD...\n")
        #SpinCore_pp.runBoard()
        run_scans_time_list.append(time.time())
        run_scans_names.append('get data')
        raw_data = np.random.random(2048) + np.random.random(2048) * 1j#SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
        run_scans_time_list.append(time.time())
        run_scans_names.append('shape data')
        data_array = complex128(raw_data[0::2]+1j*raw_data[1::2])
        print("COMPLEX DATA ARRAY LENGTH:",shape(data_array)[0])
        print("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
        dataPoints = int(shape(data_array)[0])
        if DNP_data is None and power_idx ==0 and field_idx == 0:
            time_axis = linspace(0.0,1*nPhaseSteps*acq_time_ms*1e-3,dataPoints)
            DNP_data = ndshape([len(powers),len(r_[3503:3508:0.1]),1,dataPoints],['power','field','nScans','t']).alloc(dtype=complex128)
            DNP_data.setaxis('power',r_[powers]).set_units('W')
            DNP_data.setaxis('field',r_[3503:3508:0.1]).set_units('G')
            DNP_data.setaxis('t',time_axis).set_units('t','s')
            DNP_data.setaxis('nScans',r_[0:1])
            DNP_data.name("node_name")
        DNP_data['power',power_idx]['field',field_idx]['nScans',x] = data_array
        #SpinCore_pp.stopBoard()
        run_scans_time_list.append(time.time())
        this_array = array(run_scans_time_list)
        print("checkpoints:",this_array-this_array[0])
        print("time for each chunk",['%s %0.1f'%(run_scans_names[j],v) for j,v in enumerate(diff(this_array))])
        print("stored scan",x,"for power_idx",power_idx)
        if nScans > 1:
            DNP_data.setaxis('nScans',r_[0:1])
        return DNP_data
#}}}

#}}}
#{{{where error occurs
meter_powers = zeros_like(dB_settings)
carrierFreqs_MHz = zeros_like(r_[3503:3508:0.1], dtype=float)
fields_Set = zeros_like(r_[3503:3508:0.1],dtype=float)

with power_control() as p:
    for j,this_dB in enumerate(dB_settings):
        if j == 0:
            short_delay
            p.start_log()
        p.set_power(this_dB)
        for k in range(10):
            short_delay
            if p.get_power_setting() >= this_dB: break
        long_delay
        meter_powers[j] = p.get_power_setting()
        if True:
            for B0_index,desired_B0 in enumerate(r_[3503:3508:0.1]):
                #carrierFreq_MHz = rand()
                carrierFreqs_MHz[B0_index] = rand()
                fields_Set[B0_index] = rand()
                short_delay
                if True:
                    if DNP_data is None:
                        DNP_data = run_scans(1,j,B0_index, DNP_data = None)
                    else:
                        DNP_data = run_scans(1,j,B0_index,DNP_data)
                    long_delay
    log_array, log_dict = p.stop_log()# where error occurred originally!
print("EXITING...")    
    #}}}

