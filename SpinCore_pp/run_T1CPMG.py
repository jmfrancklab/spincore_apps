#{{{ note on phase cycling
'''
FOR PHASE CYCLING: Provide both a phase cycle label (e.g.,
'ph1', 'ph2') as str and an array containing the indices
(i.e., registers) of the phases you which to use that are
specified in the numpy array 'tx_phases'.  Note that
specifying the same phase cycle label will loop the
corresponding phase steps together, regardless of whether
the indices are the same or not.
    e.g.,
    The following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph1',r_[2,3]),
    will provide two transients with phases of the two pulses (p1,p2):
        (0,2)
        (1,3)
    whereas the following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph2',r_[2,3]),
    will provide four transients with phases of the two pulses (p1,p2):
        (0,2)
        (0,3)
        (1,2)
        (1,3)
FURTHER: The total number of transients that will be
collected are determined by both nScans (determined when
calling the appropriate marker) and the number of steps
calculated in the phase cycle as shown above.  Thus for
nScans = 1, the SpinCore will trigger 2 times in the first
case and 4 times in the second case.  for nScans = 2, the
SpinCore will trigger 4 times in the first case and 8 times
in the second case.
'''
#}}}
from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp 
import time
from datetime import datetime
fl = figlist_var()

date = datetime.now().strftime('%y%m%d')
output_name = 'TEMPOL_capillary_probe_T1CPMG'
#clock_correction = 1.0829/998.253
adcOffset = 39
carrierFreq_MHz = 14.896091
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
p90 = 4.901875
deadtime = 10.0
repetition = 10e6
deblank = 1.0
marker = 1.0

SW_kHz = 4.0
nPoints = 128
acq_time = nPoints/SW_kHz # ms
deblank = 1.0

tau_extra = 1500.0 # us, must be more than deadtime and more than deblank
pad_start = tau_extra - deadtime
pad_end = tau_extra - deblank*2 # marker + deblank
twice_tau = deblank + 2*p90 + deadtime + pad_start + acq_time*1e3 + pad_end + marker
tau1 = twice_tau/2.0

nScans = 4
nEchoes = 64
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 2
if not phase_cycling:
    nPhaseSteps = 1 
data_length = 2*nPoints*nEchoes*nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
vd_list = r_[5e1,5.8e5,9e5,1.8e6,2.7e6,
        3.6e6,4.5e6,5.4e6,6.4e6,7.2e6,10e6]
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
acq_params['deblank_us'] = deblank
acq_params['tau_extra_us'] = tau_extra
acq_params['pad_start_us'] = pad_start
acq_params['pad_end_us'] = pad_end
acq_params['marker_us'] = marker
acq_params['tau1_us'] = tau1
acq_params['SW_kHz'] = SW_kHz
acq_params['nPoints'] = nPoints
if phase_cycling:
    acq_params['nPhaseSteps'] = nPhaseSteps
#}}}
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
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,0),
            ('delay',vd),
            ('delay_TTL',deblank),
            ('pulse_TTL',p90,'ph1',r_[0,2]),
            ('delay',tau1),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,1),
            ('delay',deadtime),
            ('delay',pad_start),
            ('acquire',acq_time),
            ('delay',pad_end),
            ('marker','echo_label',(nEchoes-1)), # 1 us delay
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,1),
            ('delay',deadtime),
            ('delay',pad_start),
            ('acquire',acq_time),
            ('delay',pad_end),
            ('jumpto','echo_label'), # 1 us delay
            ('delay',repetition),
            ('jumpto','start')
            ])
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',nScans),
            ('phase_reset',1),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',vd),
            ('delay_TTL',deblank),
            ('pulse_TTL',p90,0.0),
            ('delay',tau1),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',pad),
            ('marker','echo_label',(nEchoes-1)),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',pad),
            ('jumpto','echo_label'),
            ('delay',repetition),
            ('jumpto','start')
            ])
    print("\nSTOPPING PROG BOARD...\n")
    SpinCore_pp.stop_ppg();
    print("\nRUNNING BOARD...\n")
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
        data_2d = ndshape([len(vd_list),len(time_axis)],['vd','t']).alloc(dtype=complex128)
        data_2d.setaxis('vd',vd_list*1e-6).set_units('vd','s')
        data_2d.setaxis('t',time_axis).set_units('t','s')
    data_2d['vd',index] = data
SpinCore_pp.stopBoard();
print("EXITING...")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        print("SAVING FILE...")
        data_2d.set_prop('acq_params',acq_params)
        data_2d.name('signal')
        data_2d.hdf5_write(date+'_'+output_name+'.h5')
        print("Name of saved data",data_2d.name())
        print("Units of saved data",data_2d.get_units('t'))
        print("Shape of saved data",ndshape(data_2d))
        save_file = False
    except Exception as e:
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            data_2d.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
        save_file = False
fl.next('raw data')
data_2d *= exp(-1j*data_2d.fromaxis('vd')*clock_correction)
manual_taxis_zero = acq_time*1e-3/2.0 #2.29e-3
data_2d.setaxis('t',lambda x: x-manual_taxis_zero)
fl.image(data_2d)
data_2d.ft('t',shift=True)
fl.next('FT raw data')
fl.image(data_2d)
fl.show()

