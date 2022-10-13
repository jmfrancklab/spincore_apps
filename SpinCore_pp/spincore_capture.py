from pyspecdata import *
import SpinCore_pp
from datetime import datetime
fl = figlist_var()
raise RuntimeError("This pulse program has not been updated.  Before running again, it should be possible to replace a lot of the code below with a call to the function provided by the 'generic' pulse program inside the ppg directory!")
#{{{importing acquisition parameters
config_dict = SpinCore_pp.configuration('active.ini')
nPoints = int(config_dict['acq_time_ms']*config_dict['SW_kHz']+0.5)
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config_dict['type'] = 'spincore_capture'
config_dict['date'] = date
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
#}}}
tx_phases = r_[0.0,90.0,180.0,270.0]
phase_cycling = False
coherence_pathway = [('ph1',1),('ph2',-2)]
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
data_length = 2*nPoints*config_dict['nEchoes']*nPhaseSteps
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
            ('delay',config_dict['tau_us']),
            ('delay',config_dict['deadtime']),
            ('acquire',config_dict['acq_time_ms']),
            ('delay',config_dict['repetition_us']),
            ('jumpto','start')
            ])
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay',config_dict['tau_us']),
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
    data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
    dataPoints = float(shape(data_array)[0])
    if x == 0:
        time_axis = linspace(0.0,config_dict['nEchoes']*nPhaseSteps
                *config_dict['acq_time_ms']*1e-3,dataPoints)
        data = ndshape([len(data_array),config_dict['nScans']],['t','nScans']).alloc(dtype=complex128)
        data.setaxis('t',time_axis).set_units('t','s')
        data.setaxis('nScans',r_[0:config_dict['nScans']])
        data.name('signal')
        data.set_prop('acq_params',config_dict.asdict())
    data['nScans',x] = data_array
    SpinCore_pp.stopBoard();
save_file = True
while save_file:
    try:
        print("SAVING FILE...")
        data.hdf5_write(filename+'.h5')
        print(("Name of saved data",data.name()))
        print(("Units of saved data",data.get_units('t')))
        print(("Shape of saved data",ndshape(data)))
        save_file = False
    except Exception as e:
        print(e)
        print("EXCEPTION ERROR - FILE MAY ALREADY EXIST.")
        save_file = False

data.set_units('t','data')
# {{{ once files are saved correctly, the following become obsolete
if not phase_cycling:
    fl.next('raw data')
    fl.plot(data)
    data.ft('t',shift=True)
    fl.next('ft')
    fl.plot(data.real)
    fl.plot(data.imag)
if phase_cycling:
    data.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    data.setaxis('ph2',r_[0.,2.]/4)
    data.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    if nScans > 1:
        data.setaxis('nScans',r_[0:config_dict['nScans']])
    fl.next('image')
    data.mean('nScans')
    fl.image(data)
    data.ft('t2',shift=True)
    fl.next('image - ft')
    fl.image(data)
    fl.next('image - ft, coherence')
    data.ft(['ph1','ph2'])
    fl.image(data)
    fl.next('data plot')
    fl.plot(data['ph1',1]['ph2',0])
    fl.plot(data.imag['ph1',1]['ph2',0])
fl.show()
