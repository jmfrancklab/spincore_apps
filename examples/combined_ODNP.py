from numpy import *
from pyspecdata import *
import os
import sys
import SpinCore_pp
import time
from Instruments import power_control
from datetime import datetime
from SpinCore_pp.verifyParams import verifyParams
from SpinCore_pp.ppg import run_spin_echo
# do the same with the inversion recovery
from SpinCore_pp.power_helper import gen_powerlist
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
import h5py
# {{{ Combined ODNP
# {{{ experimental parameters
# {{{ these need to change for each sample
output_name = '150mM_TEMPOL_DNP'
IR_postproc = 'spincore_IR_v1'
Ep_postproc = 'ODNP_v3'
adcOffset = 26
carrierFreq_MHz = 14.897196
nScans = 1
nEchoes = 1
# all times in microseconds
# note that acq_time_ms is always milliseconds
p90_us = 4.464
repetition_us = 0.5e6
FIR_rd = 0.5e6
vd_list =r_[2.1e3,1.12e4,2.23e4,3.3e4,4.4e4,5.6e4,6.7e4,7.8e4,8.9e4,1e5] 
max_power = 4 #W
power_steps = 14
threedown = True
# }}}
#{{{Power settings
dB_settings = gen_powerlist(max_power,power_steps+1, three_down=threedown)
T1_powers_dB = gen_powerlist(max_power, 5, three_down=False)
T1_node_names = ['FIR_%ddBm'%j for j in T1_powers_dB]
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
print("T1_powers_dB",T1_powers_dB)
print("correspond to powers in Watts",10**(T1_powers_dB/10.-3))
myinput = input("Look ok?")
if myinput.lower().startswith('n'):
    raise ValueError("you said no!!!")
#}}}
powers = 1e-3*10**(dB_settings/10.)
fl = figlist_var()
save_file=True
SW_kHz = 3.9 #AAB and FS have found the min SW without loss to be 1.9 kHz 
acq_time_ms = 1024. # ms
nPoints = int(acq_time_ms*SW_kHz+0.5)
acq_time_ms = nPoints/SW_kHz
deblank_us = 1.0
tau_us = 3500
pad_us = 0
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
deadtime_us = 10.0
Ep_ph1_cyc = r_[0,1,2,3]
Ep_ph2_cyc = r_[0]
IR_ph1_cyc = r_[0,2]
IR_ph2_cyc = r_[0,2]
date = datetime.now().strftime('%y%m%d')
#{{{run enhancement
DNP_ini_time = time.time()
with power_control() as p:
    retval_thermal = p.dip_lock(9.81,9.83)
    p.start_log()
    p.mw_off()
    DNP_data = run_spin_echo(nScans,0,len(powers)+1) # assume that the power
    #                                                  axis is 1 longer than
    #                                                  the "powers" array, so
    #                                                  that we can also store
    #                                                  the thermally polarized
    #                                                  signal in this array
    #                                                  (note that powers and
    #                                                  other parameters are
    #                                                  defined globally w/in
    #                                                  the script, as this
    #                                                  function is not designed
    #                                                  to be moved outside the
    #                                                  module
    DNP_thermal_done = time.time()
    time_axis_coords = DNP_data.getaxis('indirect')
    time_axis_coords[0]['start_times'] = DNP_ini_time
    # w/ struct array, this becomes time_axis_coords[0]['start_time']
    DNP_data.set_prop('Ep_start_time', DNP_ini_time)
    DNP_data.set_prop('Ep_thermal_done_time', DNP_thermal_done)
    time_axis_coords[0]['stop_times'] = DNP_thermal_done
    # w/ struct array, we can add time_axis_coords[0]['stop_time'], and the above becomes obsolete
    power_settings = zeros_like(dB_settings)
    time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    with power_control() as p:
        for j, this_dB in enumerate(dB_settings):
            print("SETTING THIS POWER",this_dB,"(",dB_settings[j-1],powers[j],"W)")
            if j == 0:
                retval = p.dip_lock(9.81,9.83)
            p.set_power(this_dB)
            for k in range(10):
                time.sleep(0.5)
                if p.get_power_setting() >= this_dB: break
            if p.get_power_setting() < this_dB: raise ValueError("After 10 tries, the power has still not settled")    
            time.sleep(5)
            power_settings[j] = p.get_power_setting()
            time_axis_coords[j+1]['start_times'] = time.time()
            run_spin_echo(nScans,j+1,DNP_data)
            time_axis_coords[j+1]['stop_times'] = time.time()
DNP_data.set_prop('stop_time', time.time())
DNP_data.set_prop('postproc_type',Ep_postproc)
# the following line needs to be done separately for the IR and the E(p)
acq_params = {j:eval(j) for j in dir() if j in ['adcOffset', 'carrierFreq_MHz', 'amplitude',
    'nScans', 'nEchoes', 'p90_us', 'deadtime_us', 'repetition_us', 'SW_kHz',
    'nPoints', 'deblank_us', 'tau_us', 'nPhaseSteps', 'MWfreq', 'power_settings']}
DNP_data.set_prop('acq_params',acq_params)
myfilename = date+'_'+output_name+'.h5'
DNP_data.chunk('t',['ph1','t2'],[4,-1])
DNP_data.setaxis('ph1',Ep_ph1_cyc/4)
while save_file:
    try:
        print("SAVING FILE...")
        DNP_data.name('enhancement')
        DNP_data.hdf5_write(myfilename)        
        print("FILE SAVED")
        print("Name of saved enhancement data", DNP_data.name())
        print("shape of saved enhancement data", ndshape(DNP_data))
        save_file=False
    except Exception as e:
        print(e)
        print("EXCEPTION ERROR - FILE MAY ALREADY EXIST. LOOPING TO ALLOW YOU TO CHANGE NAME OF PREEXISTING FILE")
        save_file = False
        time.sleep(3)
#}}}
#{{{run IR
ini_time = time.time() # needed b/c data object doesn't exist yet
with power_control() as p:
    retval_IR = p.dip_lock(9.81,9.83)
    p.mw_off()
    vd_data = run_scans_IR(vd_list,'FIR_noPower',indirect_idx=0,
            nScans=nScans, rd = FIR_rd)
    time_axis_coords_IR = vd_data.getaxis('indirect')
    time_axis_coords_IR[0]=ini_time
    vd_data.set_prop('start_time',ini_time)
    meter_power=0
    acq_params = {j:eval(j) for j in dir() if j in ['adcOffset', 'carrierFreq_MHz', 'amplitude','nScans', 'nEchoes', 'p90_us', 'deadtime_us', 'repetition_us', 'SW_kHz', 'nPoints', 'deblank_us', 'tau_us', 'MWfreq', 'acq_time_ms', 'meter_power']}
    vd_data.set_prop('acq_params',acq_params)
    myfilename = date+'_'+output_name+'.h5'
    vd_data.chunk('t',['ph2','ph1','t2'],[2,2,-1])
    vd_data.setaxis('ph1',IR_ph1_cyc/4)
    vd_data.setaxis('ph2',IR_ph2_cyc/4)
    # Need error handling (JF has posted something on this..)
    vd_data.hdf5_write(myfilename)
    print("\n*** FILE SAVED ***\n")
    print(("Name of saved data",vd_data.name()))
    time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    for j,this_dB in enumerate(T1_powers_dB):
        if j==0:
            MWfreq = p.dip_lock(9.81,9.83)
        p.set_power(this_dB)
        for k in range(10):
            time.sleep(0.5)
            if p.get_power_setting()>= this_dB: break
        if p.get_power_setting() < this_dB: raise ValueError("After 10 tries, the power has still not settled")
        time.sleep(5)
        meter_power = p.get_power_setting()
        vd_data.set_prop('start_time', time.time())
        run_scans_IR(vd_list,T1_node_names[j],indirect_idx=j+1,
                 nScans=nScans, rd = FIR_rd, power_on=True, vd_data=vd_data)
        vd_data.set_prop('stop_time', time.time())
        acq_params = {j:eval(j) for j in dir() if j in ['adcOffset', 'carrierFreq_MHz', 'amplitude',
            'nScans', 'nEchoes', 'p90_us', 'deadtime_us', 'repetition_us', 'SW_kHz',
            'nPoints', 'deblank_us', 'tau_us', 'MWfreq', 'acq_time_ms', 'meter_power']}
        vd_data.set_prop('acq_params',acq_params)
        vd_data.set_prop('postproc_type',IR_postproc)
        vd_data.name(T1_node_names[j])
        myfilename = date+'_'+output_name+'.h5'
        vd_data.setaxis('ph1',IR_ph1_cyc/4)
        vd_data.setaxis('ph2',IR_ph2_cyc/4)
        vd_data.hdf5_write(myfilename)
    final_frq = p.dip_lock(9.81,9.83)
    this_log = p.stop_log()
SpinCore_pp.stopBoard()    
#}}}
with h5py.File(myfilename, 'a') as f:
    log_grp = f.create_group('log')
    hdf_save_dict_to_group(log_grp,this_log.__getstate__())


