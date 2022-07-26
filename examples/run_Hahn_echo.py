"""
Spin Echo
=========

To run this experiment, please open Xepr on the EPR computer, connect to
spectrometer, load the experiment 'set_field' and enable XEPR API. Then, in a
separate terminal, run the program XEPR_API_server.py, and wait for it to
tell you 'I am listening' - then, you should be able to run this program from
the NMR computer to set the field etc. 
"""

from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
from Instruments.XEPR_eth import xepr
fl = figlist_var()
#{{{importing acquisition parameters
config_dict = SpinCore_pp.configuration('active.ini')
nPoints = int(config_dict['acq_time_ms']*config_dict['SW_kHz']+0.5)
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config_dict['type'] = 'echo'
config_dict['date'] = date
config_dict['echo_counter'] += 1
filename = str(config_dict['date'])+'_'+config_dict['chemical']+'_'+config_dict['type'])
#}}}
#{{{let computer set field
print("I'm assuming that you've tuned your probe to",
        config_dict['carrierFreq_MHz'],
        "since that's what's in your .ini file")
config_dict["Field"] = config_dict['carrierFreq_MHz']/config_dict['gamma_eff_MHz_G']
print("Based on that, and the gamma_eff_MHz_G you have in your .ini file, I'm setting the field to %f"%config_dict['Field'])
with xepr() as x:
    field = config_dict["Field"]
    assert field < 3700, "are you crazy??? field is too high!"
    assert field > 3300, "are you crazy?? field is too low!"
    field = x.set_field(field)
    print("field set to ",field)
#}}}
#{{{set phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0,1,2,3]
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
#}}}    
#{{{check total points
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#}}}
#{{{acquire echo
echo_data = run_spin_echo(
        nScans=config_dict['nScans'],
        indirect_idx = 0,
        indirect_len = 1,
        ph1_cyc = ph1_cyc,
        adcOffset = config_dict['adc_offset'],
        carrierFreq_MHz = config_dict['carrierFreq_MHz'],
        nPoints = nPoints,
        nEchoes = config_dict['nEchoes'],
        p90_us = config_dict['p90_us'],
        repetition = config_dict['repetition_us'],
        tau_us = config_dict['tau_us'],
        SW_kHz = config_dict['SW_kHz'],
        output_name = filename,
        ret_data = None)
SpinCore_pp.stopBoard()
#}}}
#{{{setting acq_params
echo_data.set_prop("postproc_type","proc_Hahn_echoph")
echo_data.set_prop("acq_params",config_dict.asdict())
echo_data.name(config_dict['type']+'_'+config_dict['echo_counter'])
#}}}
#{{{Look at raw data
if phase_cycling:
    echo_data.chunk('t',['ph1','t2'],[4,-1])
    echo_data.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    if config_dict['nScans'] > 1:
        echo_data.setaxis('nScans',r_[0:config_dict['nScans']])
    fl.next('image')
    echo_data.mean('nScans')
    fl.image(echo_data)
    echo_data.ft('t2',shift=True)
    fl.next('image - ft')
    fl.image(echo_data)
    fl.next('image - ft, coherence')
    echo_data.ft(['ph1'])
    fl.image(echo_data)
    fl.next('data plot')
    data_slice = echo_data['ph1',1]
    fl.plot(data_slice, alpha=0.5)
    fl.plot(data_slice.imag, alpha=0.5)
    fl.plot(abs(data_slice), color='k', alpha=0.5)
else:
    fl.next('raw data')
    fl.plot(echo_data)
    echo_data.ft('t',shift=True)
    fl.next('ft')
    fl.plot(echo_data.real)
    fl.plot(echo_data.imag)
    fl.plot(abs(echo_data),color='k',alpha=0.5)
#}}}    
target_directory = getDATADIR(exp_type='ODNP_NMR_comp/Echoes')
filename_out = filename + '.h5'
nodename = echo_data.name()
if os.path.exists(filename+'.h5'):
    print('this file already exists so we will add a node to it!')
    with h5py.File(os.path.normpath(os.path.join(target_directory,
        f"{filename_out}"))) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, lets delete it to overwrite")
            del fp[nodename]
    echo_data.hdf5_write(f'{filename_out}/{nodename}', directory = target_directory)
else:
    try:
        echo_data.hdf5_write(filename+'.h5',
                directory=target_directory)
    except:
        print(f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp.h5 in the current directory")
        if os.path.exists("temp.h5"):
            print("there is a temp.h5 -- I'm removing it")
            os.remove('temp.h5')
        echo_data.hdf5_write('temp.h5')
        print("if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!")
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data",echo_data.name()))
print(("Shape of saved data",ndshape(echo_data)))
config_dict.write()
print("Your *current* γ_eff (MHz/G) should be ",
        config_dict['carrierFreq_MHz']/config_dict['Field'],
        ' - (Δν*1e-6/',config_dict['Field'],
        '), where Δν is your resonance offset')
print("So, look at the resonance offset where your signal shows up, and enter the new value for gamma_eff_MHz_G into your .ini file, and run me again!")
fl.show()
