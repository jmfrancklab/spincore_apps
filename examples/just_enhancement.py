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
# {{{ these need to change for each sample
output_name = '6mM_TEMPOL_test_1'
adcOffset = 29
carrierFreq_MHz = 14.896314
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
date = datetime.now().strftime('%y%m%d')
# all times in microseconds
# note that acq_time_ms is always milliseconds
p90_us = 4.477
deadtime_us = 10.0
repetition_us = 1e6
SW_kHz = 2 
nPoints = 64
acq_time_ms = nPoints/SW_kHz # ms
tau_adjust_us = 0.0
deblank_us = 1.0
tau_us = 3500
pad_us = 0
# }}}
#{{{Power settings
max_power = 4 #W
power_steps = 3
dB_settings = gen_powerlist(max_power,power_steps)
threedown = True
if threedown:
    append_dB = [dB_settings[abs(10**(dB_settings/10.-3)-max_power*frac).argmin()]
            for frac in [0.75,0.5,0.25]]
    dB_settings = append(dB_settings,append_dB)
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
myinput = input("Look ok?")
#}}}
time_list = [time.time()]
if myinput.lower().startswith('n'):
    raise ValueError("you said no!!!")
powers = 1e-3*10**(dB_settings/10.)
time_list.append(time.time())
#{{{ enhancement curve pulse prog
def run_scans(nScans, power_idx, DNP_data=None):
    """run nScans and slot them into he power_idx index of DNP_data -- assume
    that the first time this is run, it will be run with DNP_data=None and that
    after that, you will pass in DNP_data
    
    assume that the power axis is 1 longer than the "powers" array
    (note that powers and other parameters are defined globally w/in the
    script, as this function is not designed to be moved outside the module
    """
    print("about to run run_scans for",power_idx)
    ph1_cyc = r_[0,1,2,3]
    ph2_cyc = r_[0]
    nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)
    data_length = 2*nPoints*nEchoes*nPhaseSteps
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
        if DNP_data is None:
            time_axis = r_[0:dataPoints]/(SW_kHz*1e3) 
            DNP_data = ndshape([len(powers)+1,nScans,dataPoints],['indirect','nScans','t']).alloc(dtype=complex128)
            DNP_data.setaxis('indirect',zeros(len(powers)+1)).set_units('s')
            DNP_data.setaxis('t',time_axis).set_units('t','s')
            DNP_data.setaxis('nScans',r_[0:nScans])
            DNP_data.name('enhancement_curve')
        DNP_data['indirect',power_idx]['nScans',x] = data_array
        DNP_data['indirect',power_idx] = time.time()
        SpinCore_pp.stopBoard()
        run_scans_time_list.append(time.time())
        this_array = array(run_scans_time_list)
        print("checkpoints:",this_array-this_array[0])
        print("time for each chunk",['%s %0.1f'%(run_scans_names[j],v) for j,v in enumerate(diff(this_array))])
        print("stored scan",x,"for power_idx",power_idx)
        if nScans > 1:
            DNP_data.setaxis('nScans',r_[0:nScans])
        return DNP_data
#}}}
ini_time = time.time() # needed b/c data object doesn't exist yet
DNP_data = run_scans(nScans,0)
time_axis_coords = DNP_data.getaxis('indirect')
time_axis_coords[0] = ini_time
time_list.append(time.time())
power_settings = zeros_like(dB_settings)
with power_control() as p:
    for j, this_dB in enumerate(dB_settings):
        print("SETTING THIS POWER",this_dB,"(",dB_settings[j-1],powers[j],"W)")
        if j == 0:
            retval = p.dip_lock(9.81,9.83)
            print(retval)
            p.start_log()
        p.set_power(this_dB)
        for k in range(10):
            time.sleep(0.5)
            if p.get_power_setting() >= this_dB: break
        if p.get_power_setting() < this_dB: raise ValueError("After 10 tries, the power has still not settled")    
        time.sleep(5)
        power_settings[j] = p.get_power_setting()
        time_axis_coords[j] = time.time()
        run_scans(nScans,j+1,DNP_data)
        if j == dB_settings[-1]:
            this_log=p.stop_log()
#log_array = this_log.total_log
#print("log array",repr(log_array))
#print("log array shape",log_array.shape)
#log_dict = this_log.log_dict
acq_params = {j:eval(j) for j in dir() if j in ['adcOffset', 'carrierFreq_MHz', 'amplitude',
    'nScans', 'nEchoes', 'p90_us', 'deadtime_us', 'repetition_us', 'SW_kHz',
    'nPoints', 'tau_adjust_us', 'deblank_us', 'tau_us', 'nPhaseSteps', 'MWfreq', 'power_settings']}
DNP_data.set_prop('acq_params',acq_params)
myfilename = date+'_'+output_name+'.h5'
DNP_data.chunk('t',['ph1','t2'],[4,-1])
DNP_data.setaxis('ph1',r_[0,1,2,3]/4)
time_list.append(time.time())
time_array = array(time_list)
while save_file:
    try:
        print("SAVING FILE...")
        DNP_data.hdf5_write(myfilename)
        print("FILE SAVED")
        print("Name of saved enhancement data", DNP_data.name())
        print("shape of saved enhancement data", ndshape(DNP_data))
        save_file=False
        with h5py.File(myfilename, 'a') as f:
            log_grp = f.create_group('log')
            hdf_save_dict_to_group(log_grp,this_log.__getstate__())    
    except Exception as e:
        print(e)
        print("EXCEPTION ERROR - FILE MAY ALREADY EXIST.")
        save_file = False

