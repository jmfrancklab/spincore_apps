from pyspecdata import *
import SpinCore_pp
from datetime import datetime
fl = figlist_var()
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
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',repetition),
            ('jumpto','start')
            ])
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            #('delay_TTL',deblank),
            #('pulse_TTL',p90,0),
            ('delay',tau),
            #('delay_TTL',deblank),
            #('pulse_TTL',2.0*p90,0),
            ('delay',deadtime),
            ('acquire',acq_time),
            #('delay',pad),
            ('delay',repetition),
            ('jumpto','start')
            ])
    print("\nSTOPPING PROG BOARD...\n")
    SpinCore_pp.stop_ppg();
    print("\nRUNNING BOARD...\n")
    SpinCore_pp.runBoard();
    raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps)
    raw_data.astype(float)
    data_array = []
    data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
    print(("COMPLEX DATA ARRAY LENGTH:",shape(data_array)[0]))
    print(("RAW DATA ARRAY LENGTH:",shape(raw_data)[0]))
    dataPoints = float(shape(data_array)[0])
    if x == 0:
        time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
        data = ndshape([len(data_array),nScans],['t','nScans']).alloc(dtype=complex128)
        data.setaxis('t',time_axis).set_units('t','s')
        data.setaxis('nScans',r_[0:nScans])
        data.name('signal')
        data.set_prop('acq_params',acq_params)
    data['nScans',x] = data_array
    SpinCore_pp.stopBoard();
print("EXITING...")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        print("SAVING FILE...")
        data.hdf5_write(date+'_'+output_name+'.h5')
        print("FILE SAVED!")
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
print(ndshape(data))
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
        data.setaxis('nScans',r_[0:nScans])
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
fl.show();quit()

if phase_cycling:
    data.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    data.setaxis('ph2',r_[0.,2.]/4)
    data.setaxis('ph1',r_[0.,1.,2.,3.]/4)
if nScans > 1:
    data.setaxis('nScans',r_[0:nScans])
# }}}
data.squeeze()
data.reorder('t2',first=False)
if len(data.dimlabels) > 1:
    fl.next('raw data - time|ph domain')
    fl.image(data)
else:
    if 't' in data.dimlabels:
        data.rename('t','t2')
has_phcyc_dims = False
for j in range(8):# up to 8 independently phase cycled pulses
    phstr = 'ph%d'%j
    if phstr in data.dimlabels:
        has_phcyc_dims = True
        print('phcyc along',phstr)
        data.ft(phstr)
if has_phcyc_dims:
    fl.next('raw data - time|coh domain')
    fl.image(data)
data.ft('t2',shift=True)
if len(data.dimlabels) > 1:
    fl.next('raw data - freq|coh domain')
    fl.image(data)
if 'ph1' in data.dimlabels:
    for phlabel,phidx in coherence_pathway:
        data = data[phlabel,phidx]
data.mean_all_but('t2')
fl.next('raw data - FT')
fl.plot(data,alpha=0.5)
fl.plot(data.imag, alpha=0.5)
fl.plot(abs(data),'k',alpha=0.1, linewidth=3)
data.ift('t2')
fl.next('avgd. and coh. ch. selected (where relevant) data -- time domain')
fl.plot(data,alpha=0.5)
fl.plot(data.imag, alpha=0.5)
fl.plot(abs(data),'k',alpha=0.2, linewidth=2)
fl.show();quit()

