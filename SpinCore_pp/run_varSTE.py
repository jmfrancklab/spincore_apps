#{{{ Notes for use
# To run this experiment, please open Xepr on the EPR computer, connect to
# spectrometer, load the experiemnt 'set_field' and enable XEPR API. Then, in a
# separate terminal, run the program XEPR_API_server.py, and wait for it to
# tell you 'I am listening' - then, you should be able to run this program from
# the NMR computer to set the field etc. 

# Note the booleans user_sets_Freq and
# user_sets_Field allow you to run experiments as previously run in this lab.
# If both values are set to True, this is the way we used to run them. If both
# values are set to False, you specify what field you want, and the computer
# will do the rest.
#}}}

from pylab import *
from pyspecdata import *
import os,sys
import SpinCore_pp
from datetime import datetime
import numpy as np
from Instruments.XEPR_eth import xepr
raise RuntimeError("This pulse program has been updated to use active.ini, but not the ppg functions..  Before running again, it should be possible to replace a lot of the code below with a call to the function provided by the 'generic' pulse program inside the ppg directory!")fl = figlist_var()
#{{{importing acquisition parameters
config_dict = SpinCore_pp.configuration('active.ini')
nPoints = int(config_dict['acq_time_ms']*config_dict['SW_kHz']+0.5)
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config_dict['type'] = 'varied_echo'
config_dict['date'] = date
config_dict['echo_counter'] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
#}}}
tx_phases = r_[0.0,90.0,180.0,270.0]
phase_cycling = True
coherence_pathway = [('ph1',1),('ph2',-2)]
nPhaseSteps = 8
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
tau1 = 2
data_length = 2*nPoints*config_dict['nEchoes']*nPhaseSteps
tau2_range = linspace(6000.,100000.,15,endpoint=False)
for tau2_index,tau2_val in enumerate(tau2_range):
    for x in range(nScans):
        tau2 = tau2_val
        SpinCore_pp.configureTX(config_dict['adcOffset'], config_dict['carrierFreq_MHz'], 
                tx_phases, config_dict['amplitude'], nPoints)
        SpinCore_pp.init_ppg();
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
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
        if x == 0 and tau2_index == 0:
            time_axis = np.linspace(0.0,config_dict['nEchoes']*nPhaseSteps
                    *config_dict['acq_time_ms']*1e-3,dataPoints)
            data = ndshape([len(tau2_range),len(data_array),config_dict['nScans']],['tau2','t','nScans']).alloc(dtype=np.complex128)
            data.setaxis('t',time_axis).set_units('t','s')
            data.setaxis('nScans',r_[0:config_dict['nScans']])
            data.setaxis('tau2',tau2_range).set_units('tau2','s')
            data.name(config_dict['type']+'_'+config_dict['echo_counter'])
            data.set_prop('acq_params',config_dict.asdict())
        data['nScans',x]['tau2',tau2_index] = data_array
SpinCore_pp.stopBoard();
config_dict.write()
save_file = True
while save_file:
    try:
        data.hdf5_write(filename+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/STE'))
        print(("Name of saved data",data.name()))
        print(("Units of saved data",data.get_units('t')))
        print(("Shape of saved data",ndshape(data)))
        save_file = False
    except Exception as e:
        print(e)
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        filename = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(filename) is not 0:
            data.hdf5_write(filename+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
data.set_units('t','data')
data.chunk('t',['ph3','ph2','ph1','t2'],[2,2,2,-1])
data.setaxis('ph2',r_[0.,2.]/4)
data.setaxis('ph2',r_[0.,2.]/4)
data.setaxis('ph1',r_[0.,2.]/4)
if nScans > 1:
    data.setaxis('nScans',r_[0:config_Dict['nScans']])
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
