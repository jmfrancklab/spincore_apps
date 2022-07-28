'''Run Inversion Recovery at set power
======================================
You will need to manually set the power manually with Spyder and the B12. Once the power is set and the parameters are adjusted, you can run this program to collect the inversion recovery dataset at the set power.
'''
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import run_IR
from datetime import datetime
fl = figlist_var()
#{{{importing acquisition parameters
config_dict = SpinCore_pp.configuration('active.ini')
nPoints = int(config_dict['acq_time_ms']*config_dict['SW_kHz']+0.5)
#}}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config_dict['type'] = 'IR'
config_dict['date'] = date
config_dict['IR_counter'] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
#}}}
#{{{phase cycling
phase_cycling = True
if phase_cycling:
    ph1 = r_[0,2]
    ph2 = r_[0,2]
    nPhaseSteps = 4
if not phase_cycling:
    ph1 = r_[0]
    ph2 = r_[0]
    nPhaseSteps = 1 
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#}}}
#{{{make vd list
vd_kwargs = {
        j:config_dict[j]
        for j in ['krho_cold','krho_hot','T1water_cold','T1water_hot']
        if j in config_dict.keys()
        }
vd_list_us = SpinCore_pp.vdlist_from_relaxivities(config_dict['concentration'],**vd_kwargs) * 1e6 #put vd list into microseconds
#}}}
#{{{run IR
vd_data = run_IR(
        nPoints = nPoints,
        nEchoes=config_dict['nEchoes'],
        vd_list_us = vd_list_us,
        nScans=config_dict['nScans'],
        adcOffset = config_dict['adc_offset'],
        carrierFreq_MHz=config_dict['carrierFreq_MHz'],
        p90_us=config_dict['p90_us'],
        tau_us = config_dict['tau_us'],
        repetition=config_dict['repetition_us'],
        ph1_cyc = ph1,
        ph2_cyc = ph2,
        output_name= filename,
        SW_kHz=config_dict['SW_kHz'],
        ret_data = None)
SpinCore_pp.stopBoard();
vd_data.set_prop('acq_params',config_dict.asdict())
vd_data.set_prop("postproc", "spincore_IR_v1")
vd_data.name(config_dict['type']+'_'+str(config_dict['ir_counter']))
if phase_cycling:
    vd_data.chunk("t",['ph2','ph1','t2'],[len(ph1),len(ph2),-1])
    vd_data.setaxis("ph1", ph1 / 4)
    vd_data.setaxis("ph2", ph2 / 4)
    if config_dict['nScans'] > 1:
        vd_data.setaxis('nScans',r_[0:config_dict['nScans']])
else:
    vd_data.rename('t','t2')
vd_data.reorder(['ph1','ph2','vd','t2'])
vd_data.ft(['ph1','ph2'],unitary = True)
vd_data.ft('t2',shift=True)
#}}}
#{{{Save Data
target_directory = getDATADIR(exp_type='ODNP_NMR_comp/inv_rec')
filename_out = filename + '.h5'
nodename = vd_data.name()
if os.path.exists(filename+'.h5'):
    print('this file already exists so we will add a node to it!')
    with h5py.File(os.path.normpath(os.path.join(target_directory,
        f"{filename_out}"))) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp")
            vd_data.name('temp')
            nodename = 'temp'
    echo_data.hdf5_write(f'{filename_out}/{nodename}', directory = target_directory)
else:
    vd_data.hdf5_write(filename+'.h5',
            directory=target_directory)
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data",vd_data.name()))
print(("Shape of saved data",ndshape(vd_data)))
config_dict.write()
#}}}
#{{{visualize raw data
vd_data.ift('t2')
fl.next('raw data')
fl.image(vd_data.setaxis('vd','#'))
fl.next('abs raw data')
fl.image(abs(vd_data).setaxis('vd','#'))
vd_data.ft('t2')
fl.next('FT raw data')
fl.image(vd_data.setaxis('vd','#'))
fl.next('FT abs raw data')
fl.image(abs(vd_data).setaxis('vd','#')['t2':(-1e3,1e3)])
fl.show()
#}}}
