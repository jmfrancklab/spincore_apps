from pyspecdata import *
from numpy import *
import os,sys,time
import SpinCore_pp
from Instruments import Bridge12,prologix_connection,gigatronics
from serial import Serial
import h5py
from datetime import datetime
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
from SpinCore_pp.power_helper import gen_powerlist
raise RuntimeError("This pulse program has been updated to use active.ini, but not the ppg functions..  Before running again, it should be possible to replace a lot of the code below with a call to the function provided by the 'generic' pulse program inside the ppg directory!")
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/ODNP")
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
#{{{ Parameters for Bridge12
dB_settings = gen_powerlist(config_dict['max_power'],config_dict['power_steps'])
append_dB = [dB_settings[abs(10**(dB_settings/10.-3)-config_dict['max_power']*frac).argmin()]
        for frac in [0.75,0.5,0.25]]
dB_settings = append(dB_settings,append_dB)
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
#}}}    
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
data_length = 2*nPoints*config_dict['nEchoes']*nPhaseSteps
#{{{ run ppg
for x in range(config_dict['nScans']):
    SpinCore_pp.configureTX(config_dict['adcOffset'], config_dict['carrierFreq_MHz'], 
            tx_phases, config_dict['amplitude'], nPoints)
    acq_time = SpinCore_pp.configureRX(config_dict['SW_kHz'], nPoints, 1, 
            config_dict['nEchoes'], nPhaseSteps)
    SpinCore_pp.init_ppg();
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
    SpinCore_pp.stop_ppg();
    SpinCore_pp.runBoard();
    raw_data = SpinCore_pp.getData(data_length, nPoints, config_dict['nEchoes'], nPhaseSteps)
    raw_data.astype(float)
    data = []
    data[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
    dataPoints = float(np.shape(data)[0])
    data = nddata(np.array(data),'t')
    if x == 0:
        time_axis = linspace(0.0,config_dict['nEchoes']*nPhaseSteps*config_dict['acq_time_ms']*1e-3,dataPoints)
        data.setaxis('t',time_axis).set_units('t','s')
        data.name('signal')
        data.set_prop('acq_params',config_dict.asdict())
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
    this_return = b.lock_on_dip(ini_range=
            config_dict['uw_dip_center_GHz']-config_dict['uw_dip_width_GHz'] / 2,
            config_dict['uw_dip_center_GHz']+config_dict['uw_dip_width_GHz']/2)
    dip_f = this_return[2]
    b.set_freq(dip_f)
    meter_powers = zeros_like(dB_settings)
    for j,this_power in enumerate(dB_settings):
        if j>0 and this_power > last_power + 3:
            last_power += 3
            b.set_power(last_power)
            time.sleep(3.0)
            while this_power > last_power+3:
                last_power += 3
                b.set_power(last_power)
                time.sleep(3.0)
            b.set_power(this_power)
        elif j == 0:
            threshold_power = 10
            if this_power > threshold_power:
                next_power = threshold_power + 3
                while next_power < this_power:
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
        for x in range(config_dict['nScans']):
            SpinCore_pp.configureTX(config_dict['adcOffset'], config_dict['carrierFreq_MHz'], 
                    tx_phases, config_dict['amplitude'], nPoints)
            acq_time = SpinCore_pp.configureRX(config_dict['SW_kHz'], nPoints, 
                    1, config_dict['nEchoes'], nPhaseSteps)
            SpinCore_pp.init_ppg();
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
            SpinCore_pp.stop_ppg();
            SpinCore_pp.runBoard();
            raw_data = SpinCore_pp.getData(data_length, nPoints, config_dict['nEchoes'], nPhaseSteps)
            raw_data.astype(float)
            data = []
            data[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
            dataPoints = float(np.shape(data)[0])
            data = nddata(np.array(data),'t')
            DNP_data['power',j+1]['nScans',x] = data
        last_power = this_power
data.name('signal')
data.set_prop('meter_powers',meter_powers)
SpinCore_pp.stopBoard();
#}}}
#{{{save
data.set_prop('acq_params',config_dict.asdict())
nodename = data.name()
filename_out = filename+'.h5'
with h5py.File(
    os.path.normpath(os.path.join(target_directory,f"{filename_out}")
)) as fp:
    if nodename in fp.keys():
        print("this nodename already exists, so I will call it temp_%d"%j)
        data.name("temp_FID_mw_%d"%config_dict['echo_counter'])
        nodename = "temp_FID_mw_%d"%config_dict['echo_counter']
        data.hdf5_write(f"{filename_out}",directory = target_directory)
    else:
        data.hdf5_write(f"{filename_out}", directory=target_directory)
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", data.name()))
print(("Shape of saved data", ndshape(data)))
#}}}
#{{{ image raw
fl.next('raw data')
fl.image(data.setaxis('power','#'))
fl.next('abs raw data')
fl.image(abs(data).setaxis('power','#'))
data.ft('t',shift=True)
fl.next('raw data - ft')
fl.image(data.setaxis('power','#'))
fl.next('abs raw data - ft')
fl.image(abs(data).setaxis('power','#'))
#}}}
fl.show()
