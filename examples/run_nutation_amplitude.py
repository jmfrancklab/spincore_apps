from pyspecdata import *
import os,sys,time
import SpinCore_pp
from datetime import datetime
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
import numpy as np
import h5py
from Instruments.XEPR_eth import xepr
from SpinCore_pp.ppg import run_spin_echo
fl = figlist_var()
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/nutation")
raise RuntimeError(
    "This pulse program has been updated to use active.ini, and the spin echo ppg function, but has not yet been tested!"
)
#{{{importing acquisition parameters
config_dict = SpinCore_pp.configuration('active.ini')
nPoints = int(config_dict['acq_time_ms']*config_dict['SW_kHz']+0.5)
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config_dict['type'] = 'nutation'
config_dict['date'] = date
config_dict['echo_counter'] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
#}}}
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
#{{{ phase cycling
tx_phases = r_[0.0,90.0,180.0,270.0]
phase_cycling = True
if phase_cycling:
    ph1 = r_[0,1,2,3]
    ph2 = r_[0,2]
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
data_length = 2*nPoints*nEchoes*nPhaseSteps
#}}}
#{{{ ppg
amp_range = np.linspace(0,0.5,200)[1:]#,endpoint=False)
datalist = []
for index,val in enumerate(amp_range):
    amplitude = val # pulse amp, set from 0.0 to 1.0
    echo_data = run_spin_echo(
        nScans=config_dict['nScans'],
        indirect_idx = 0,
        indirect_len = 1,
        adcOffset = config_dict['adc_offset'],
        carrierFreq_MHz = config_dict['carrierFreq_MHz'],
        nPoints = nPoints,
        nEchoes = config_dict['nEchoes'],
        p90_us = config_dict['p90_us'],
        repetition = config_dict['repetition_us'],
        tau_us = config_dict['tau_us'],
        SW_kHz = config_dict['SW_kHz'],
        ph1_cyc = ph1,
        ph2_cyc = ph2,
        ret_data = None)
        datalist=[]
        with GDS_scope() as g:
            g.acquire_mode('HIR')
            for j in range(amp_range):
                datalist.append(g.waveform(ch=1))
nutation_data = concat(datalist,'repeats').reorder('t')
nutation_data.chunk('t',['ph2','ph1','t2'],[2,4,-1])
nutation_data.setaxis('ph2',r_[0:2]/4).setaxis('ph1',r_[0:4]/4)
nutation_data.set_units('t2','s')
nutation_data.set_prop('postproc_type','spincore_nutation_v2')
nutation_data.name(config_dict['type']+config_dict['echo_counter'])
nutation_data.set_prop('acq_params',config_dict.asdict())
#}}}
#{{{save data
nodename = nutation_data.name()
filename_out =filename+'.h5'
with h5py.File(
    os.path.normpath(os.path.join(target_directory,f"{filename_out}")
)) as fp:
    if nodename in fp.keys():
        print("this nodename already exists, so I will call it temp_nutation_amp_%d"%config_dict['echo_counter'])
        nutation_data.name("temp__nutation_amp_%d"%config_dict['echo_counter'])
        nodename = "temp_nutation_amp_%d"%config_dict['echo_counter']
        nutation_data.hdf5_write(f"{filename_out}",directory = target_directory)
    else:
        nutation_data.hdf5_write(f"{filename_out}", directory=target_directory)
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", nutation_data.name()))
print(("Shape of saved data", ndshape(nutation_data)))
config_dict.write()
#}}}
#{{{image data
fl.next('raw data')
fl.image(nutation_data)
nutation_data.ft('t2',shift=True)
fl.next('FT raw data')
fl.image(nutation_data)
fl.show()
#}}}
