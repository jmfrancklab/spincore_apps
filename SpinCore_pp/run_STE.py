from pylab import *
from pyspecdata import *
import os,sys
import SpinCore_pp
from datetime import datetime
import numpy as np
from Instruments.XEPR_eth import xepr
fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "echo"
config_dict["date"] = date
config_dict["echo_counter"] += 1
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
#{{{ phase cycling
tx_phases = r_[0.0,90.0,180.0,270.0]
phase_cycling = True
coherence_pathway = [('ph1',1),('ph2',-2)]
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
#}}}    
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
#{{{ run ppg
tau1 = 2
tau2 = 80000
print(("TAU 1 DELAY:",tau1,"us"))
print(("TAU 2 DELAY:",tau2,"us"))
data_length = 2*nPoints*nEchoes*nPhaseSteps
for x in range(config_dict['nScans']):
    SpinCore_pp.configureTX(config_dict['adcOffset'], config_dict['carrierFreq_MHz'], 
            tx_phases, config_dict['amplitude'], nPoints)
    SpinCore_pp.init_ppg();
    if phase_cycling:
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
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',config_dict['deblank_us']),
            ('pulse_TTL',config_dict['p90_us'],0),
            ('delay',config_dict['tau_us']),
            ('delay_TTL',config_dict['deblank_us']),
            ('pulse_TTL',2.0*config_dict['p90_us'],0),
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
    if x == 0:
        time_axis = np.linspace(0.0,config_dict['nEchoes']*nPhaseSteps
                *config_dict['acq_time_ms']*1e-3,dataPoints)
        data = ndshape([len(data_array),config_dict['nScans']],
                ['t','nScans']).alloc(dtype=np.complex128)
        data.setaxis('t',time_axis).set_units('t','s')
        data.setaxis('nScans',r_[0:config_dict['nScans']])
        data.name(config_dict['type']+'_'+config_dict['echo_counter'])
        data.set_prop('acq_params',config_dict.asdict())
    data['nScans',x] = data_array
    SpinCore_pp.stopBoard();
#}}}
#{{{ save data
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
config_dict.write()
#}}}
#{{{image data
data.set_units('t','data')
if phase_cycling:
    data.chunk('t',['ph3','ph2','ph1','t2'],[2,2,2,-1])
    data.setaxis('ph2',r_[0.,2.]/4)
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
