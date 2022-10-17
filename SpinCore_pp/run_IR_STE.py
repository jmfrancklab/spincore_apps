from pylab import *
from pyspecdata import *
import os,sys
import SpinCore_pp
from datetime import datetime
import numpy as np
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
from Instruments.XEPR_eth import xepr
import h5py
fl = figlist_var()
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/inv_rec")
raise RuntimeError("This pulse program has not been updated.  Before running again, it should be possible to replace a lot of the code below with a call to the function provided by the 'generic' pulse program inside the ppg directory!")
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "IR_STE"
config_dict["date"] = date
config_dict["IR_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
#{{{let computer set field
print("I'm assuming that you've tuned your probe to",
        config_dict['carrierFreq_MHz'],
        "since that's what's in your .ini file")
Field = config_dict['carrierFreq_MHz']/config_dict['gamma_eff_MHz_G']
print("Based on that, and the gamma_eff_MHz_G you have in your .ini file, I'm setting the field to %f"%Field)
with xepr() as x:
    assert Field < 3700, "are you crazy??? field is too high!"
    assert Field > 3300, "are you crazy?? field is too low!"
    Field = x.set_field(Field)
    print("field set to ",Field)
#}}}
#{{{phase cycling
tx_phases = r_[0.0,90.0,180.0,270.0]
nPhaseSteps = 8
#}}}
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
#{{{tau and vd list
tau1 = 2
tau2 = 80000
# {{{make vd list
vd_kwargs = {
    j: config_dict[j]
    for j in ["krho_cold", "krho_hot", "T1water_cold", "T1water_hot"]
    if j in config_dict.keys()
}
vd_list_us = (
    SpinCore_pp.vdlist_from_relaxivities(config_dict["concentration"], **vd_kwargs)
    * 1e6
)  # put vd list into microseconds
# }}}
#}}}
#{{{ run ppg
print(("TAU 1 DELAY:",tau1,"us"))
print(("TAU 2 DELAY:",tau2,"us"))
data_length = 2*nPoints*nEchoes*nPhaseSteps
for vd_index,vd_val in enumerate(vd_list):
    for x in range(nScans):
        vd = vd_val
        SpinCore_pp.configureTX(config_dict['adcOffset'], config_dict['carrierFreq_MHz'], 
                tx_phases, config_dict['amplitude'], nPoints)
        SpinCore_pp.init_ppg();
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',config_dict['deblank_us']),
            ('pulse_TTL',2.0*config_dict['p90_us'],0),
            ('delay',vd),
            ('delay_TTL',config_dict['deblank_us']),
            ('pulse_TTL',config_dict['p90_us'],'ph1',r_[0,2]),
            ('delay',tau1),
            ('delay_TTL',config_dict['deblank_us']),
            ('pulse_TTL',config_dict['p90_us'],'ph2',r_[0,2]),
            ('delay',tau2),
            ('delay_TTL',config_dict['deblank_us']),
            ('pulse_TTL',config_dict['p90_us'],'ph3',r_[0,2]),
            ('delay',config_dict['deadtime_us']),
            ('acquire',config_dict['acq_time_ms']),
            ('delay',config_dict['repetition_us']),
            ('jumpto','start')
            ])
        SpinCore_pp.stop_ppg();
        SpinCore_pp.runBoard();
        raw_data = SpinCore_pp.getData(data_length, nPoints, config_dict['nEchoes'], nPhaseSteps)
        raw_data.astype(float)
        data_array = []
        data_array[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
        dataPoints = float(np.shape(data_array)[0])
        if x == 0 and vd_index == 0:
            time_axis = np.linspace(0.0,config_dict['nEchoes']*nPhaseSteps
                    *config_dict['acq_time_ms']*1e-3,dataPoints)
            data = ndshape([len(vd_list),len(data_array),nScans],['vd','t','nScans']).alloc(dtype=np.complex128)
            data.setaxis('t',time_axis).set_units('t','s')
            data.setaxis('nScans',r_[0:config_dict['nScans']])
            data.setaxis('vd',vd_list)
            data.name(config_dict['type'])
            data.set_prop('acq_params',config_dict.asdict())
        data['nScans',x]['vd',vd_index] = data_array
SpinCore_pp.stopBoard();
data.name(config_dict['type'])        
#}}}
#{{{ save data
config_dict.write()
nodename = data.name()
filename_out = filename+'.h5'
with h5py.File(
    os.path.normpath(os.path.join(target_directory,f"{filename_out}")
)) as fp:
    if nodename in fp.keys():
        print("this nodename already exists, so I will call it temp_IR_STE_%d"%config_dict['ir_counter'])
        data.name("temp_IR_STE_%d"%config_dict['ir_counter'])
        nodename = "temp_IR_STE_%d"%config_dict['ir_counter']
        data.hdf5_write(f"{filename_out}",directory = target_directory)
    else:
        data.hdf5_write(f"{filename_out}", directory=target_directory)
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", data.name()))
print(("Shape of saved data", ndshape(data)))
#}}}
#{{{ image data
data.set_units('t','data')
data.chunk('t',['ph3','ph2','ph1','t2'],[2,2,2,-1])
data.setaxis('ph3',r_[0.,2.]/4)
data.setaxis('ph2',r_[0.,2.]/4)
data.setaxis('ph1',r_[0.,2.]/4)
if nScans > 1:
    data.setaxis('nScans',r_[0:config_dict['nScans']])
fl.next('image')
data.mean('nScans')
fl.image(data)
data.ft('t2',shift=True)
fl.next('image - ft')
fl.image(data)
fl.next('image - ft, coherence')
data.ft(['ph1','ph2','ph3'])
fl.image(data)
fl.next('image - ft, coherence, exclude FID')
fl.image(data['ph1',1]['ph3',-1])
fl.show()
#}}}
