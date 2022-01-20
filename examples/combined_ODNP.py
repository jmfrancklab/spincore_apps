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
SW_kHz = 3.9 
acq_time_ms = 1024. # ms
nPoints = int(acq_time_ms*SW_kHz+0.5)
acq_time_ms = nPoints/SW_kHz
deblank_us = 1.0
tau_us = 3500
pad_us = 0
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
deadtime_us = 10.0
date = datetime.now().strftime('%y%m%d')
#{{{ enhancement curve pulse prog
def run_scans(nScans, power_idx, DNP_data=None):
    """run nScans and slot them into the power_idx index of DNP_data -- assume
    that the first time this is run, it will be run with DNP_data=None and that
    after that, you will pass in DNP_data
    
    assume that the power axis is 1 longer than the "powers" array,
    so that we can also store the thermally polarized signal in this array
    (note that powers and other parameters are defined globally w/in the
    script, as this function is not designed to be moved outside the module

    this generates an "indirect" axis
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
        SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        run_scans_time_list.append(time.time())
        run_scans_names.append('configure Rx')
        print("***")
        print("CONFIGURING RECEIVER...")
        acq_time_ms = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps)
        # acq_time_ms is in msec!
        verifyParams(nPoints=nPoints, nScans=nScans, p90_us=p90_us, tau_us=tau_us)
        run_scans_time_list.append(time.time())
        run_scans_names.append('init')
        SpinCore_pp.init_ppg()
        run_scans_time_list.append(time.time())
        run_scans_names.append('prog')
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
        SpinCore_pp.stop_ppg()
        run_scans_time_list.append(time.time())
        run_scans_names.append('run')
        SpinCore_pp.runBoard()
        run_scans_time_list.append(time.time())
        run_scans_names.append('get data')
        raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
        run_scans_time_list.append(time.time())
        run_scans_names.append('shape data')
        data_array=[]
        data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
        dataPoints = float(shape(data_array)[0])
        if DNP_data is None:
            times_dtype = dtype([('start_times',double),('stop_times',double)])
            mytimes = zeros(len(powers)+1,dtype=times_dtype)
            if x == 0:
                time_axis = r_[0:dataPoints]/(SW_kHz*1e3) 
                DNP_data = ndshape([len(powers)+1,nScans,len(time_axis)],['indirect','nScans','t']).alloc(dtype=complex128)
                DNP_data.setaxis('indirect',mytimes)
                DNP_data.setaxis('t',time_axis).set_units('t','s')
                DNP_data.setaxis('nScans',r_[0:nScans])
            data_array = nddata(array(data_array),'t')
            data_array.setaxis('t',time_axis)
        # (delete on reading) JF edited -- there was an else block
        # w/ reference to "j", but j is not defined in the function!
        # If I assume that j+1 was intended to be power_idx, then
        # the following works for "if" as well as "else"
        DNP_data['indirect',power_idx]['nScans',x] = data_array
        run_scans_time_list.append(time.time())
        this_array = array(run_scans_time_list)
        print("stored scan",x,"for power_idx",power_idx)
        return DNP_data
#}}}
#{{{IR ppg
def run_scans_IR(vd_list, node_name, power_idx, nScans = 1, rd = FIR_rd, power_on = False, vd_data=None):
    # (JF delete on reading): convert this to a real docstring!!
    # nScans is number of scans you want
    # rd is the repetition delay
    # power_setting is what you want to run power at
    # vd list is a list of the vd's you want to use
    # node_name is the name of the node must specify power
    ph1_cyc = r_[0,2]
    ph2_cyc = r_[0,2]
    ph3_cyc = r_[0]
    nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)*len(ph3_cyc)
    data_length = 2*nPoints*nEchoes*nPhaseSteps
    for index,val in enumerate(vd_list):
        vd = val
        print("***")
        print("INDEX %d - VARIABLE DELAY %f"%(index,val))
        print("***")
        for x in range(nScans):
            run_scans_time_list = [time.time()]
            run_scans_names = ['configure']
            SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
            acq_time_ms = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
            run_scans_time_list.append(time.time())
            run_scans_names.append('configure Rx')
            verifyParams(nPoints=nPoints, nScans=nScans, p90_us=p90_us, tau_us=tau_us)
            run_scans_time_list.append(time.time())
            run_scans_names.append('init')
            SpinCore_pp.init_ppg()
            run_scans_time_list.append(time.time())
            run_scans_names.append('prog')
            SpinCore_pp.load([
                ('marker','start',1),
                ('phase_reset',1),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,'ph1',ph1_cyc),
                ('delay',vd),
                ('delay_TTL',1.0),
                ('pulse_TTL',p90_us,'ph2',ph2_cyc),
                ('delay',tau_us),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,ph3_cyc),
                ('delay',deadtime_us),
                ('acquire',acq_time_ms),
                ('delay',repetition_us),
                ('jumpto','start')
                ])
            run_scans_time_list.append(time.time())
            run_scans_names.append('prog')
            SpinCore_pp.stop_ppg()
            print("\nRUNNING BOARD...\n")
            run_scans_time_list.append(time.time())
            run_scans_names.append('run')
            SpinCore_pp.runBoard()
            run_scans_time_list.append(time.time())
            run_scans_names.append('get data')
            raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
            run_scans_time_list.append(time.time())
            run_scans_names.append('shape data')
            data_array=[]
            data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
            print("COMPLEX DATA ARRAY LENGTH:",np.shape(data_array)[0])
            print("RAW DATA ARRAY LENGTH:",np.shape(raw_data)[0])
            dataPoints = float(np.shape(data_array)[0])
            if vd_data is None:
                time_axis = r_[0:dataPoints]/(SW_kHz*1e3)
                vd_data = ndshape([len(vd_list),nScans,len(time_axis),len(vd_list)+1],['vd','nScans','t','indirect']).alloc(dtype=complex128)
                vd_data.setaxis('indirect',zeros(len(vd_list)+1)).set_units('s')
                vd_data.setaxis('vd',vd_list*1e-6).set_units('vd','s')
                vd_data.setaxis('nScans',r_[0:nScans])
                vd_data.setaxis('t',time_axis).set_units('t','s')
            vd_data['vd',index]['nScans',x]['indirect',power_idx] = data_array
            vd_data.name(node_name)
            SpinCore_pp.stopBoard();
            run_scans_time_list.append(time.time())
            this_array = array(run_scans_time_list)
            print("checkpoints:",this_array-this_array[0])
            print("time for each chunk",['%s %0.1f'%(run_scans_names[j],v) for j,v in enumerate(diff(this_array))])
            print("stored scan",x,"for power_idx",power_idx)
            if nScans > 1:
                vd_data.setaxis('nScans',r_[0:nScans])
    return vd_data
#}}}
#{{{run enhancement
DNP_ini_time = time.time()
with power_control() as p:
    retval_thermal = p.dip_lock(9.81,9.83)
    p.start_log()
    p.mw_off()
    DNP_data = run_scans(nScans,0)
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
            run_scans(nScans,j+1,DNP_data)
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
DNP_data.setaxis('ph1',r_[0,1,2,3]/4)
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
    vd_data = run_scans_IR(vd_list,'FIR_noPower',
            nScans=nScans, power_idx=0)
    time_axis_coords_IR = vd_data.getaxis('indirect')
    time_axis_coords_IR[0]=ini_time
    vd_data.set_prop('start_time',ini_time)
    meter_power=0
    acq_params = {j:eval(j) for j in dir() if j in ['adcOffset', 'carrierFreq_MHz', 'amplitude',
        'nScans', 'nEchoes', 'p90_us', 'deadtime_us', 'repetition_us', 'SW_kHz',
        'nPoints', 'deblank_us', 'tau_us', 'MWfreq', 'acq_time_ms', 'meter_power']}
    vd_data.set_prop('acq_params',acq_params)
    myfilename = date+'_'+output_name+'.h5'
    ph1ir_cyc = r_[0,2]
    ph2ir_cyc = r_[0,2]
    vd_data.chunk('t',['ph2','ph1','t2'],[2,2,-1])
    vd_data.setaxis('ph1',ph1ir_cyc/4)
    vd_data.setaxis('ph2',ph2ir_cyc/4)
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
        vd_data = run_scans_IR(vd_list,T1_node_names[j], nScans=nScans, power_idx=j+1,
                power_on=True,vd_data=vd_data)
        vd_data.set_prop('stop_time', time.time())
        acq_params = {j:eval(j) for j in dir() if j in ['adcOffset', 'carrierFreq_MHz', 'amplitude',
            'nScans', 'nEchoes', 'p90_us', 'deadtime_us', 'repetition_us', 'SW_kHz',
            'nPoints', 'deblank_us', 'tau_us', 'MWfreq', 'acq_time_ms', 'meter_power']}
        vd_data.set_prop('acq_params',acq_params)
        vd_data.set_prop('postproc_type',IR_postproc)
        vd_data.name(T1_node_names[j])
        myfilename = date+'_'+output_name+'.h5'
        ph1ir_cyc = r_[0,2]
        ph2ir_cyc = r_[0,2]
        vd_data.setaxis('ph1',ph1ir_cyc/4)
        vd_data.setaxis('ph2',ph2ir_cyc/4)
        vd_data.hdf5_write(myfilename)
    final_frq = p.dip_lock(9.81,9.83)
    this_log = p.stop_log()
SpinCore_pp.stopBoard()    
#}}}
with h5py.File(myfilename, 'a') as f:
    log_grp = f.create_group('log')
    hdf_save_dict_to_group(log_grp,this_log.__getstate__())


