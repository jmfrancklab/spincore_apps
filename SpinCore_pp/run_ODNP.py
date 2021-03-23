from pyspecdata import *
import os
import sys
import SpinCore_pp
from datetime import datetime
#{{{ Verify arguments compatible with board
def verifyParams():
    if (nPoints > 16*1024 or nPoints < 1):
        print("ERROR: MAXIMUM NUMBER OF POINTS IS 16384.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED NUMBER OF POINTS.")
    if (nScans < 1):
        print("ERROR: THERE MUST BE AT LEAST 1 SCAN.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED NUMBER OF SCANS.")
    if (p90 < 0.065):
        print("ERROR: PULSE TIME TOO SMALL.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED PULSE TIME.")
    if (tau < 0.065):
        print("ERROR: DELAY TIME TOO SMALL.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED DELAY TIME.")
    return
#}}}
# {{{ from run_Hahn_echo_mw.py
fl = figlist_var()
# {{{ experimental parameters
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
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
p90 = 3.8
deadtime = 10.0
repetition = 10e6

SW_kHz = 1
nPoints = 1024*2

acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
deblank = 1.0
#tau = deadtime + acq_time*1e3*(1./8.) + tau_adjust
# Fixed tau for comparison
tau = 3280
pad = 0
#pad = 2.0*tau - deadtime - acq_time*1e3 - deblank
# }}}
#{{{ setting acq_params dictionary
acq_params = {}
acq_params.update({
    'adcOffset':adcOffset,
    'carrierFreq_MHz':carrierFreq_MHz,
    'amplitude':amplitude,
    'nScans':nScans,
    'nEchoes':nEchoes,
    'p90_us':p90,
    'deadtime_us':deadtime,
    'repetition_us':repetition,
    'SW_kHz':SW_kHz,
    'nPoints':nPoints,
    'tau_adjust_us':tau_adjust,
    'deblank_us':deblank,
    'tau_us':tau,
    'pad_us':pad, 
    })
if phase_cycling:
    acq_params['nPhaseSteps'] = nPhaseSteps
#}}}
print(("ACQUISITION TIME:",acq_time,"ms"))
print(("TAU DELAY:",tau,"us"))
print(("PAD DELAY:",pad,"us"))
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
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, 1, nEchoes, nPhaseSteps)
    acq_params['acq_time_ms'] = acq_time
    # acq_time is in msec!
    print(("ACQUISITION TIME IS",acq_time,"ms"))
    verifyParams()
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
            ('delay_TTL',deblank),
            ('pulse_TTL',p90,'ph1',r_[0,1,2,3]),
            ('delay',tau),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,'ph2',r_[0,2]),
            ('delay',deadtime),
            ('acquire',acq_time),
            #('delay',pad),
            ('delay',repetition),
            ('jumpto','start')
            ])
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank),
            ('pulse_TTL',p90,0),
            ('delay',tau),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,0),
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
    raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
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
p90 = 3.8
deadtime = 10.0
repetition = 10e6
SW_kHz = 24.0
nPoints = 1024*2
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
deblank = 1.0
tau = deadtime + acq_time*1e3*0.5 + tau_adjust
print("ACQUISITION TIME:",acq_time,"ms")
print("TAU DELAY:",tau,"us")
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
acq_params['p90_us'] = p90
acq_params['deadtime_us'] = deadtime
acq_params['repetition_us'] = repetition
acq_params['SW_kHz'] = SW_kHz
acq_params['nPoints'] = nPoints
acq_params['tau_adjust_us'] = tau_adjust
acq_params['deblank_us'] = deblank
acq_params['tau_us'] = tau
acq_params['pad_us'] = pad 
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
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    acq_params['acq_time_ms'] = acq_time
    SpinCore_pp.init_ppg();
    if phase_cycling:
        phase_cycles = dict(ph1 = r_[0,2],
                ph2 = r_[0,1,2,3])
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90,'ph1',phase_cycles['ph1']),
            ('delay',vd),
            ('delay_TTL',1.0),
            ('pulse_TTL',p90,'ph2',phase_cycles['ph2']),
            ('delay',tau),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90,0),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',repetition),
            ('jumpto','start')
            ])
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',nScans),
            ('phase_reset',1),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',vd),
            ('delay_TTL',1.0),
            ('pulse_TTL',p90,0.0),
            ('delay',tau),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',repetition),
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
    time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
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
