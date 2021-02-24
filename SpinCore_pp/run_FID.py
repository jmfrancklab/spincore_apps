# Just capturing FID, not echo detection
# 4-step phase cycle
from pylab import *
from pyspecdata import *
import os
import sys
import SpinCore_pp
from datetime import datetime
import numpy as np
fl = figlist_var()
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
    return
#}}}

output_name = '4AT_cap_probe_FID_r1_1'
adcOffset = 37
carrierFreq_MHz = 14.893494
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
phase_cycling = True
#coherence_pathway = [('ph1',1),('ph2',-2)]
date = datetime.now().strftime('%y%m%d')
if phase_cycling:
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
p90 = 4.69
deadtime = 10.0
repetition = 5e6

SW_kHz = 48
nPoints = 1024*2

acq_time = nPoints/SW_kHz # ms
deblank = 1.0
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
acq_params['deblank_us'] = deblank
if phase_cycling:
    acq_params['nPhaseSteps'] = nPhaseSteps
#}}}
print(("ACQUISITION TIME:",acq_time,"ms"))
data_length = 2*nPoints*nEchoes*nPhaseSteps
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
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',repetition),
            ('jumpto','start')
            ])
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank),
            ('pulse_TTL',p90,0),
            ('delay',deadtime),
            ('acquire',acq_time),
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
    data_array[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
    print(("COMPLEX DATA ARRAY LENGTH:",np.shape(data_array)[0]))
    print(("RAW DATA ARRAY LENGTH:",np.shape(raw_data)[0]))
    dataPoints = float(np.shape(data_array)[0])
    if x == 0:
        time_axis = np.linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
        data = ndshape([len(data_array),nScans],['t','nScans']).alloc(dtype=np.complex128)
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
        print("SAVING FILE IN TARGET DIRECTORY...")
        data.hdf5_write(date+'_'+output_name+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/FID'))
        print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
        print(("Name of saved data",data.name()))
        print(("Units of saved data",data.get_units('t')))
        print(("Shape of saved data",ndshape(data)))
        save_file = False
    except Exception as e:
        print(e)
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            data.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break

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
    data.chunk('t',['ph1','t2'],[4,-1])
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
    data.ft(['ph1'])
    fl.image(data)
    fl.next('data plot')
    fl.plot(data['ph1',-1])
    fl.plot(data.imag['ph1',-1])
fl.show();quit()

if phase_cycling:
    data.chunk('t',['ph1','t2'],[4,-1])
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
#if 'ph1' in data.dimlabels:
#    for phlabel,phidx in coherence_pathway:
#        data = data[phlabel,phidx]
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

