from pyspecdata import *
import os, sys, time
import SpinCore_pp
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
import h5py
from datetime import datetime
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/COSY")
raise RuntimeError("This pulse proram has not been updated.  Before running again, it should be possible to replace a lot of the code below with a call to the function provided by the 'generic' pulse program inside the ppg directory!")
fl = figlist_var()
 {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "COSY_DQF"
config_dict["date"] = date
config_dict["cosy_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}_{config_dict['cosy_counter'}"
# }}}
#{{{ phase cycling, tx phases
tx_phases = r_[0.0,90.0,180.0,270.0]
tau_adjust = 0.0
delta = 2.
ph1 = r_[0,1,2,3]
ph3 = r_[0,1,2,3]
nPhaseSteps = 16
#}}}
data_length = 2*nPoints*config_dict['nEchoes']*nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
# cannot have a delay of 0, so set to minimum SpinCore can take
#{{{make t1_list
min_t1 = 0.065 # us (lower limit of SpinCore)
max_t1 = 200*1e3
t1_step = 1.25*1e3
t1_list = r_[min_t1:max_t1:t1_step]
#}}}
#{{{run ppg
for index,val in enumerate(t1_list):
    t1 = val
    for x in range(config_dict['nScans']): 
        SpinCore_pp.configureTX(config_dict['adcOffset'], config_dict['carrierFreq_MHz'], 
            tx_phases, config_dict['amplitude'], nPoints)
        acq_time = SpinCore_pp.configureRX(config_dict['SW_kHz'], nPoints, 
            config_dict['nScans'], config_dict['nEchoes'], nPhaseSteps) #ms
        SpinCore_pp.init_ppg();
        if phase_cycling:
            SpinCore_pp.load([
                ('marker','start',1),
                ('phase_reset',1),
                ('delay_TTL',config_dict['deblank_us']),
                ('pulse_TTL',config_dict['p90_us'],'ph1',r_[0,1,2,3]),
                ('delay',t1),
                ('delay_TTL',config_dict['deblank_us']),
                ('pulse_TTL',config_dict['p90_us'],0),
                ('delay',delta),
                ('delay_TTL',config_dict['deblank_us']),
                ('pulse_TTL',config_dict'p90_us'],'ph3',r_[0,1,2,3]),
                ('delay',config_dict['deadtime_us']),
                ('acquire',config_dict['acq_time_ms']),
                ('delay',config_dict['repetition_us']),
                ('jumpto','start')
                ])
        if not phase_cycling:
            SpinCore_pp.load([
                ('marker','start',config_dict['nScans']),
                ('phase_reset',1),
                ('delay_TTL',config_dict['deblank_us']),
                ('pulse_TTL',config_dict['p90_us'],0),
                ('delay',t1),
                ('delay_TTL',config_dict['deblank_us']),
                ('pulse_TTL',config_dict['p90_us'],0),
                ('delay',config_dict['deadtime_us']),
                ('acquire',config_dict['acq_time_ms']),
                ('delay',config_dict['repetition']),
                ('jumpto','start')
                ])
        SpinCore_pp.stop_ppg();
        SpinCore_pp.runBoard();
        raw_data = SpinCore_pp.getData(data_length, nPoints, config_data['nEchoes'], nPhaseSteps)
        raw_data.astype(float)
        data = []
        data[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
        dataPoints = float(np.shape(data)[0])
        time_axis = np.linspace(0.0,config_dict['nEchoes']*nPhaseSteps*config_dict['acq_time_ms']
                *1e-3,dataPoints)
        data = nddata(np.array(data),'t')
        data.setaxis('t',time_axis).set_units('t','s')
        data.name('signal')
        data.set_prop('acq_params',config_dict.asdict())
        if index == 0 and x == 0:
            COSY_data = ndshape([len(t1_list),config_dict['nScans'],len(time_axis)],
                    ['t1','nScans','t']).alloc(dtype=np.complex128)
            COSY_data.setaxis('t1',t1_list*1e-6).set_units('t1','s')
            COSY_data.setaxis('nScans',r_[0:config_dict['nScans']])
            COSY_data.setaxis('t',time_axis).set_units('t','s')
        COSY_data['t1',index]['nScans',x] = data
        COSY_data.set_prop('acq_params',config_dict.asdict())
SpinCore_pp.stopBoard();
config_dict.write()
#}}}
#{{{ save data
nodename = config_dict['type']+'_'+congi_dict['cpmg_counter']
filename_out = filename+'.h5'
if phase_cycling:
    COSY_data.chunk('t',['ph3','ph1','t2'],[4,4,-1])
    COSY_data.setaxis('ph1',r_[0,1,2,3]/4.)
    COSY_data.setaxis('ph3',r_[0,1,2,3]/4.)
else:
    COSY_data.rename('t','t2')
with h5py.File(
        os.path.normpath(os.path.join(target_directory,f"{filename_out}")
    )) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_COSY_DQF_%d"%config_dict['cpmg_counter'])
            COSY_data.name("temp_CPMG_DQF_%d"%config_dict['cpmg_counter'])
            nodename = "temp_CPMG_DQF_%d"%config_dict['cpmg_counter']
            COSY_data.hdf5_write(f"{filename_out}",directory = target_directory)
        else:
            COSYd_data.hdf5_write(f"{filename_out}", directory=target_directory)
    print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
    print(("Name of saved data", COSY_data.name()))
    print(("Shape of saved data", ndshape(COSY_data)))
#}}}        

