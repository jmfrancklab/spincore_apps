from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
import socket
import sys
import time
from datetime import datetime
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
    if (tau_us < 0.065):
        print("ERROR: DELAY TIME TOO SMALL.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED DELAY TIME.")
    return
#}}}
#{{{Parameters that change for new samples
output_name = 'TEMPOL_capillary_probe_nutation_1'
adcOffset = 39
carrierFreq_MHz = 14.896010
nScans = 1
nEchoes = 1
phase_cycling = True
repetition = 12e6
p90_range = linspace(1.,15.,40,endpoint=False)
#}}}
#{{{These should stay the same regardless of sample
date = datetime.now().strftime('%y%m%d')
ph1_cyc = r_[0,2]
ph2_cyc = r_[0,2]
# NOTE: Number of segments is nEchoes * nPhaseSteps
SW_kHz = 24.0
nPoints = 1024
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
tau = deadtime_us + acq_time_ms*1e3*0.5 + tau_adjust_us
print("ACQUISITION TIME:",acq_times,"ms")
print("TAU DELAY:",tau,"us")
#}}}
for index,val in enumerate(p90_range):
    p90 = val # us
    print("***")
    print("INDEX %d - 90 TIME %f"%(index,val))
    print("***")
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    SpinCore_pp.init_ppg();
    if phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',p90,'ph1',ph1_cyc),
            ('delay',tau),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',2.0*p90,'ph2',ph2_cyc),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',repetition),
            ('jumpto','start')
            ])
    if not phase_cycling: 
        SpinCore_pp.load([
            ('marker','start',nScans),
            ('phase_reset',1),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',p90,0.0),
            ('delay',tau),
            ('delay_TTL',deblank_us),
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',repetition),
            ('jumpto','start')
            ])
    SpinCore_pp.stop_ppg();
    if phase_cycling:
        for x in range(nScans):
            print("SCAN NO. %d"%(x+1))
            SpinCore_pp.runBoard();
    if not phase_cycling:
        SpinCore_pp.runBoard();
    raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
    raw_data.astype(float)
    data = []
    # according to JF, this commented out line
    # should work same as line below and be more effic
    #data = raw_data.view(complex128)
    data[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
    print("COMPLEX DATA ARRAY LENGTH:",shape(data)[0])
    print("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
    dataPoints = float(shape(data)[0])
    time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
    data = nddata(array(data),'t')
    data.setaxis('t',time_axis).set_units('t','s')
    data.name('signal')
    if index == 0:
        nutation_data = ndshape([len(p90_range),len(time_axis)],['p_90','t']).alloc(dtype=complex128)
        nutation_data.setaxis('p_90',p90_range*1e-6).set_units('p_90','s')
        nutation_data.setaxis('t',time_axis).set_units('t','s')
    nutation_data['p_90',index] = data
SpinCore_pp.stopBoard();
print("EXITING...\n")
print("\n*** *** ***\n")
save_file = True
nutation_data.chunk('t',
        ['ph2','ph1','t2'],[len(ph1_cyc),len(ph2_cyc),-1]).setaxis(
                'ph2',ph2_cyc/4).setaxis('ph1',ph1_cyc/4)

nutation_data.reorder('t2',first=False)

acq_params = {j:eval(j) in dir() if j in ['adcOffset', 'carrierFreq_MHz', 'amplitude',
    'nScans', 'nEchoes', 'p90_range', 'deadtime', 'repetition', 'SW_kHz',
    'nPoints', 'tau_adjust', 'deblank_us', 'tau', 'nPhaseSteps']}
acq_params['pulprog'] = 'spincore_nutation_v3'
while save_file:
    try:
        print("SAVING FILE...")
        nutation_data.set_prop('acq_params',acq_params)
        nutation_data.name('nutation')
        nutation_data.hdf5_write(date+'_'+output_name+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/nutation'))
        print("Name of saved data",nutation_data.name())
        print("Units of saved data",nutation_data.get_units('t'))
        print("Shape of saved data",ndshape(nutation_data))
        save_file = False
    except Exception as e:
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            nutation_data.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
        save_file = False
fl.next('raw data')
fl.image(nutation_data)
nutation_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(nutation_data)
fl.show()

