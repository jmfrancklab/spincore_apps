from numpy import *
from pyspecdata import *
import os
import sys
import SpinCore_pp
import time
from Instruments import power_control
from datetime import datetime
from SpinCore_pp.verifyParams import verifyParams
from SpinCore_pp.power_helper import gen_powerlist
import h5py
# {{{ from run_Hahn_echo_mw.py
fl = figlist_var()
# {{{ experimental parameters
# {{{ these need to change every time
adcOffset = 30
carrierFreq_MHz = 14.895863
# }}}
max_power = 2.51 #W
power_steps = 3
dB_settings = gen_powerlist(max_power,power_steps)
threedown = False
if threedown:
    append_dB = [dB_settings[abs(10**(dB_settings/10.-3)-max_power*frac).argmin()]
            for frac in [0.75,0.5,0.25]]
    dB_settings = append(dB_settings,append_dB)
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
myinput = input("Look ok?")
time_list = [time.time()]
if myinput.lower().startswith('n'):
    raise ValueError("you said no!!!")
powers = 1e-3*10**(dB_settings/10.)
ph1_cyc = r_[0,1,2,3]
ph2_cyc = r_[0,2]
output_name = 'TEMPOL_capillary_probe_1kHz'
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
coherence_pathway = [('ph1',1),('ph2',-2)]
date = datetime.now().strftime('%y%m%d')
nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time_ms is always milliseconds
#}}}
p90_us = 3.8
deadtime_us = 10.0
repetition_us = 0.5e6

SW_kHz = 1 
aq = 0.25
nPoints = int(2**ceil(log2(aq*(SW_kHz*1e3))))
print("you set an aq of",aq,"and a SW of",SW_kHz,"so, I'm going to use",nPoints,"for an actual aq of",nPoints/(SW_kHz*1e3))
assert nPoints * len(ph2_cyc) * len(ph1_cyc) <= 2**14, "too many points!"

acq_time_ms = nPoints/SW_kHz # ms
tau_adjust_us = 0.0
deblank_us = 1.0
#tau_us = deadtime_us + acq_time_ms*1e3*(1./8.) + tau_adjust_us
# Fixed tau_us for comparison
tau_us = 3280
pad_us = 0
#pad_us = 2.0*tau_us - deadtime_us - acq_time_ms*1e3 - deblank_us
# }}}
print("ACQUISITION TIME:",acq_time_ms,"ms")
print("TAU DELAY:",tau_us,"us")
print("PAD DELAY:",pad_us,"us")
data_length = 2*nPoints*nEchoes*nPhaseSteps
time_list.append(time.time())
def run_scans(nScans, power_idx, DNP_data=None):
    """run nScans and slot them into he power_idx index of DNP_data -- assume
    that the first time this is run, it will be run with DNP_data=None and that
    after that, you will pass in DNP_data
    
    assume that the power axis is 1 longer than the "powers" array
    (note that powers and other parameters are defined globally w/in the
    script, as this function is not designed to be moved outside the module
    """
    for x in range(nScans):
        run_scans_time_list = [time.time()]
        run_scans_names = ['configure']
        print("*** *** *** SCAN NO. %d *** *** ***"%(x+1))
        print("\n*** *** ***\n")
        print("CONFIGURING TRANSMITTER...")
        SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        print("\nTRANSMITTER CONFIGURED.")
        run_scans_time_list.append(time.time())
        run_scans_names.append('configure Rx')
        print("***")
        print("CONFIGURING RECEIVER...")
        acq_time_ms = SpinCore_pp.configureRX(SW_kHz, nPoints, 1, nEchoes, nPhaseSteps)
        # acq_time_ms is in msec!
        print("ACQUISITION TIME IS",acq_time_ms,"ms")
        verifyParams(nPoints=nPoints, nScans=nScans, p90_us=p90_us, tau_us=tau_us)
        run_scans_time_list.append(time.time())
        run_scans_names.append('init')
        print("\nRECEIVER CONFIGURED.")
        print("***")
        print("\nINITIALIZING PROG BOARD...\n")
        SpinCore_pp.init_ppg()
        run_scans_time_list.append(time.time())
        run_scans_names.append('prog')
        print("PROGRAMMING BOARD...")
        print("\nLOADING PULSE PROG...\n")
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',p90_us,'ph1',ph1_cyc),
            ('delay',tau_us),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',2.0*p90_us,'ph2',ph2_cyc),
            ('delay',deadtime_us),
            ('acquire',acq_time_ms),
            #('delay',pad_us),
            ('delay',repetition_us),
            ('jumpto','start')
            ])
        run_scans_time_list.append(time.time())
        run_scans_names.append('prog')
        print("\nSTOPPING PROG BOARD...\n")
        SpinCore_pp.stop_ppg()
        run_scans_time_list.append(time.time())
        run_scans_names.append('run')
        print("\nRUNNING BOARD...\n")
        SpinCore_pp.runBoard()
        run_scans_time_list.append(time.time())
        run_scans_names.append('get data')
        raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
        run_scans_time_list.append(time.time())
        run_scans_names.append('shape data')
        data_array = complex128(raw_data[0::2]+1j*raw_data[1::2])
        print("COMPLEX DATA ARRAY LENGTH:",shape(data_array)[0])
        print("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
        dataPoints = int(shape(data_array)[0])
        if x == 0 and power_idx == 0:
            time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time_ms*1e-3,dataPoints)
            DNP_data = ndshape([len(powers)+1,nScans,dataPoints],['power','nScans','t']).alloc(dtype=complex128)
            DNP_data.setaxis('power',r_[0,powers]).set_units('W')
            DNP_data.setaxis('t',time_axis).set_units('t','s')
            DNP_data.setaxis('nScans',r_[0:nScans])
            DNP_data.name('enhancement_curve')
        DNP_data['power',power_idx]['nScans',x] = data_array
        SpinCore_pp.stopBoard()
        run_scans_time_list.append(time.time())
        this_array = array(run_scans_time_list)
        print("checkpoints:",this_array-this_array[0])
        print("time for each chunk",['%s %0.1f'%(run_scans_names[j],v) for j,v in enumerate(diff(this_array))])
        return DNP_data
time_list.append(time.time())
DNP_data = run_scans(nScans,0)
time_list.append(time.time())
with power_control() as p:
    for j,this_dB in enumerate(dB_settings):
        if j == 0:
            MWfreq = p.dip_lock(9.81,9.83)
            print(MWfreq)
            p.start_log()
        p.set_power(this_dB)
        time.sleep(5)
        run_scans(nScans,j+1,DNP_data)
    p.set_power(0)
log_array, log_dict = p.stop_log()
time_list.append(time.time())
print("EXITING...")
print("\n*** *** ***\n")
save_file = True
acq_params = {j:eval(j) for j in dir() if j in ['adcOffset', 'carrierFreq_MHz', 'amplitude',
    'nScans', 'nEchoes', 'p90_us', 'deadtime_us', 'repetition_us', 'SW_kHz',
    'nPoints', 'tau_adjust_us', 'deblank_us', 'tau_us', 'nPhaseSteps', 'MWfreq']}
acq_params['pulprog'] = 'spincore_power_step_test_v1'
DNP_data.set_prop('acq_params',acq_params)
# {{{ manipulate the data as needed
DNP_data.set_units('t','s')
DNP_data.chunk('t',['ph2','ph1','t2'],[2,4,-1])
DNP_data.setaxis('ph2',ph2_cyc/4)
DNP_data.setaxis('ph1',ph1_cyc/4)
if nScans > 1:
    DNP_data.setaxis('nScans',r_[0:nScans])
# }}}
time_list.append(time.time())
# {{{ save the file
myfilename = date+'_'+output_name+'.h5'
while save_file:
    try:
        print("SAVING FILE...")
        DNP_data.hdf5_write(myfilename)
        print("FILE SAVED!")
        print("Name of saved DNP_data",DNP_data.name())
        print("Units of saved DNP_data",DNP_data.get_units('t'))
        print("Shape of saved DNP_data",ndshape(DNP_data))
        save_file = False
    except Exception as e:
        print(e)
        print("EXCEPTION ERROR - FILE MAY ALREADY EXIST.")
        save_file = False
# }}}
time_list.append(time.time())
time_array = array(time_list)
print("checkpoints:",time_array-time_array[0])
print("time for each chunk",['%0.1f'%j for j in diff(time_array)])
with h5py.File(myfilename, 'a') as f:
    log_grp = f.create_group('log') # normally, I would actually put this under the node with the data
    dset = log_grp.create_dataset("log",data=log_array)
    dset.attrs['dict_len'] = len(log_dict)
    for j,(k,v) in enumerate(log_dict.items()):
       dset.attrs['key%d'%j] = k 
       dset.attrs['val%d'%j] = v 
