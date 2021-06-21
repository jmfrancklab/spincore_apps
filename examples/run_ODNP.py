from pyspecdata import *
import os
import sys
import SpinCore_pp
from datetime import datetime
from SpinCore_pp.verifyParams import verifyParams
#{{{ Verify arguments compatible with board
#}}}
# {{{ from run_Hahn_echo_mw.py
fl = figlist_var()
# {{{ experimental parameters
ph1_cyc = r_[0,1,2,3]
ph2_cyc = r_[0,2]
output_name = 'TEMPOL_capillary_probe_1kHz'
adcOffset = 39
carrierFreq_MHz = 14.894573
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
phase_cycling = True
coherence_pathway = [('ph1',1),('ph2',-2)]
date = datetime.now().strftime('%y%m%d')
nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time_ms is always milliseconds
#}}}
p90_us = 3.8
deadtime_us = 10.0
repetition_us = 10e6

SW_kHz = 1
nPoints = 1024*2

acq_time_ms = nPoints/SW_kHz # ms
tau_adjust_us = 0.0
deblank_us = 1.0
#tau_us = deadtime_us + acq_time_ms*1e3*(1./8.) + tau_adjust_us
# Fixed tau_us for comparison
tau_us = 3280
pad_us = 0
#pad_us = 2.0*tau_us - deadtime_us - acq_time_ms*1e3 - deblank_us
# }}}
print(("ACQUISITION TIME:",acq_time_ms,"ms"))
print(("TAU DELAY:",tau_us,"us"))
print(("PAD DELAY:",pad_us,"us"))
data_length = 2*nPoints*nEchoes*nPhaseSteps
# JF to here
for x in range(nScans):
    print(("*** *** *** SCAN NO. %d *** *** ***"%(x+1)))
    print("\n*** *** ***\n")
    print("CONFIGURING TRANSMITTER...")
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    print("\nTRANSMITTER CONFIGURED.")
    print("***")
    print("CONFIGURING RECEIVER...")
    acq_time_ms = SpinCore_pp.configureRX(SW_kHz, nPoints, 1, nEchoes, nPhaseSteps)
    acq_params['acq_time_ms'] = acq_time_ms
    # acq_time_ms is in msec!
    print(("ACQUISITION TIME IS",acq_time_ms,"ms"))
    verifyParams(nPoints=nPoints, nScans=nScans, p90_us=p90_us, tau_us=tau_us)
    print("\nRECEIVER CONFIGURED.")
    print("***")
    print("\nINITIALIZING PROG BOARD...\n")
    SpinCore_pp.init_ppg();
    print("PROGRAMMING BOARD...")
    print("\nLOADING PULSE PROG...\n")
    if phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',p90_us,'ph1',ph1_cyc),
            ('delay',tau_us),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',2.0*p90_us,'ph2',ph2_cyc),
            ('delay',deadtime_us),
            ('acquire',acq_time_ms),
            #('delay',pad_us),
            ('delay',repetition_us),
            ('jumpto','start')
            ])
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',p90_us,0),
            ('delay',tau_us),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',2.0*p90_us,0),
            ('delay',deadtime_us),
            ('acquire',acq_time_ms),
            #('delay',pad_us),
            ('delay',repetition_us),
            ('jumpto','start')
            ])
    print("\nSTOPPING PROG BOARD...\n")
    SpinCore_pp.stop_ppg();
    print("\nRUNNING BOARD...\n")
    SpinCore_pp.runBoard();
    raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
    raw_data.astype(float)
    data_array = []
    data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
    print(("COMPLEX DATA ARRAY LENGTH:",shape(data_array)[0]))
    print(("RAW DATA ARRAY LENGTH:",shape(raw_data)[0]))
    dataPoints = float(shape(data_array)[0])
    if x == 0:
        time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time_ms*1e-3,dataPoints)
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
# }}}
# {{{ from run_IR.py
import socket
import sys
import time
from datetime import datetime
init_logging(level='debug')
fl = figlist_var()
#{{{ Verify arguments compatible with board
#}}}
date = datetime.now().strftime('%y%m%d')
clock_correction = 0
output_name = '4AT100uM_cap_probe_IR_32dBm'
adcOffset = 43
carrierFreq_MHz = 14.894477

tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
p90_us = 3.8
deadtime_us = 10.0
repetition_us = 10e6
SW_kHz = 24.0
nPoints = 1024*2
acq_time_ms = nPoints/SW_kHz # ms
tau_adjust_us = 0.0
deblank_us = 1.0
tau_us = deadtime_us + acq_time_ms*1e3*0.5 + tau_adjust_us
print("ACQUISITION TIME:",acq_time_ms,"ms")
print("TAU DELAY:",tau_us,"us")
phase_cycling = True
ph1 = r_[0,2]
ph2 = r_[0,1,2,3]
if phase_cycling:
    nPhaseSteps = 8 
if not phase_cycling:
    nPhaseSteps = 1 
#{{{ setting acq_params dictionary
acq_params = {}
acq_params['adcOffset'] = adcOffset
acq_params['carrierFreq_MHz'] = carrierFreq_MHz
acq_params['amplitude'] = amplitude
acq_params['nScans'] = nScans
acq_params['nEchoes'] = nEchoes
acq_params['p90_us'] = p90_us
acq_params['deadtime_us'] = deadtime_us
acq_params['repetition_us'] = repetition_us
acq_params['SW_kHz'] = SW_kHz
acq_params['nPoints'] = nPoints
acq_params['tau_adjust_us'] = tau_adjust_us
acq_params['deblank_us'] = deblank_us
acq_params['tau_us'] = tau_us
acq_params['pad_us'] = pad_us 
if phase_cycling:
    acq_params['nPhaseSteps'] = nPhaseSteps
#}}}
data_length = 2*nPoints*nEchoes*nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
vd_list = r_[5e1,5.8e5,9e5,1.8e6,2.7e6,
        3.6e6,4.5e6,5.4e6,6.4e6,7.2e6,10e6]
for index,val in enumerate(vd_list):
    vd = val
    print("***")
    print("INDEX %d - VARIABLE DELAY %f"%(index,val))
    print("***")
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    acq_time_ms = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    acq_params['acq_time_ms'] = acq_time_ms
    SpinCore_pp.init_ppg();
    if phase_cycling:
        phase_cycles = dict(ph1 = r_[0,2],
                ph2 = r_[0,1,2,3])
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90_us,'ph1',phase_cycles['ph1']),
            ('delay',vd),
            ('delay_TTL',1.0),
            ('pulse_TTL',p90_us,'ph2',phase_cycles['ph2']),
            ('delay',tau_us),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90_us,0),
            ('delay',deadtime_us),
            ('acquire',acq_time_ms),
            ('delay',repetition_us),
            ('jumpto','start')
            ])
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',nScans),
            ('phase_reset',1),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90_us,0.0),
            ('delay',vd),
            ('delay_TTL',1.0),
            ('pulse_TTL',p90_us,0.0),
            ('delay',tau_us),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90_us,0.0),
            ('delay',deadtime_us),
            ('acquire',acq_time_ms),
            ('delay',repetition_us),
            ('jumpto','start')
            ])
    SpinCore_pp.stop_ppg();
    print("\nRUNNING BOARD...\n")
    if phase_cycling:
        for x in range(nScans):
            print("SCAN NO. %d"%(x+1))
            SpinCore_pp.runBoard();
    if not phase_cycling:
        start = time.time()
        SpinCore_pp.runBoard(); 
        runtime = time.time()-start
        logger.debug(strm("for vd",vd/1e6," s run time is",runtime))
    raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
    raw_data.astype(float)
    data = []
    data[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
    print("COMPLEX DATA ARRAY LENGTH:",shape(data)[0])
    print("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
    dataPoints = float(shape(data)[0])
    time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time_ms*1e-3,dataPoints)
    data = nddata(array(data),'t')
    data.setaxis('t',time_axis).set_units('t','s')
    data.name('signal')
    data.set_prop('acq_params',acq_params)
    if index == 0:
        vd_data = ndshape([len(vd_list),len(time_axis)],['vd','t']).alloc(dtype=complex128)
        vd_data.setaxis('vd',vd_list*1e-6).set_units('vd','s')
        vd_data.setaxis('t',time_axis).set_units('t','s')
    vd_data['vd',index] = data
SpinCore_pp.stopBoard();
print("EXITING...\n")
print("\n*** *** ***\n")
save_file = True
if phase_cycling:
    phcyc_names = list(phase_cycles.keys())
    phcyc_names.sort(reverse=True)
    phcyc_dims = [len(phase_cycles[j]) for j in phcyc_names]
    vd_data.chunk('t',phcyc_names+['t2'],phcyc_dims+[-1])
    vd_data.setaxis('ph1',ph1/4.)
    vd_data.setaxis('ph2',ph2/4.)
else:
    vd_data.rename('t','t2')
acq_params = {j:eval(j) in dir() if j in ['adcOffset', 'carrierFreq_MHz', 'amplitude',
    'nScans', 'nEchoes', 'p90_us', 'deadtime_us', 'repetition_us', 'SW_kHz',
    'nPoints', 'tau_adjust_us', 'deblank_us', 'tau_us', 'nPhaseSteps']}
acq_params['pulprog'] = 'spincore_full_odnp_v1'
while save_file:
    try:
        print("SAVING FILE...")
        vd_data.name('signal')
        vd_data.hdf5_write(date+'_'+output_name+'.h5')
        print("Name of saved data",vd_data.name())
        print("Units of saved data",vd_data.get_units('t'))
        print("Shape of saved data",ndshape(vd_data))
        save_file = False
    except Exception as e:
        print(e)
        print("FILE ALREADY EXISTS.")
        save_file = False
fl.next('raw data')
fl.image(vd_data)
fl.next('abs raw data')
fl.image(abs(vd_data))
vd_data.ft('t2',shift=True)
fl.next('FT raw data')
fl.image(vd_data)
fl.next('FT abs raw data')
fl.image(abs(vd_data))
fl.show()

# }}}
