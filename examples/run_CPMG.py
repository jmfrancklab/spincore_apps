from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp 
from datetime import datetime
fl = figlist_var()

date = datetime.now().strftime('%y%m%d')
output_name = 'TEMPOL_capProbe'
node_name = 'CPMG_4step_6'
adcOffset = 25
carrierFreq_MHz = 14.895548
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
p90_us = 4.477
deadtime_us = 10.0
repetition_us = 12e6
deblank_us = 1.0
marker = 1.0

SW_kHz = 2.0
nPoints = 64
acq_time_ms = nPoints/SW_kHz # ms

tau_extra = 1000.0 # us, must be more than deadtime and more than deblank
pad_start = tau_extra - deadtime_us
pad_end = tau_extra - deblank_us*2 # marker + deblank
twice_tau = deblank_us + 2*p90_us + deadtime_us + pad_start + acq_time_ms*1e3 + pad_end + marker
tau_us = twice_tau/2.0

nScans = 16
nEchoes = 64
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1 
data_length = 2*nPoints*nEchoes*nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
for x in range(nScans):
    print("*** *** *** SCAN NO. %d *** *** ***"%(x+1))
    print("\n*** *** ***\n")
    print("CONFIGURING TRANSMITTER...")
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    print("\nTRANSMITTER CONFIGURED.")
    print("***")
    print("CONFIGURING RECEIVER...")
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    acq_params['acq_time_ms'] = acq_time
    print("\nRECEIVER CONFIGURED.")
    print("***")
    print("\nINITIALIZING PROG BOARD...\n")
    SpinCore_pp.init_ppg();
    print("\nLOADING PULSE PROG...\n")
    if phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',p90_us,'ph1',r_[0,1,2,3]),
                ('delay',tau_us),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,0),
                ('delay',deadtime_us),
                ('delay',pad_start),
                ('acquire',acq_time),
                ('delay',pad_end),
                ('marker','echo_label',(nEchoes-1)), # 1 us delay
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,0),
                ('delay',deadtime_us),
                ('delay',pad_start),
                ('acquire',acq_time),
                ('delay',pad_end),
                ('jumpto','echo_label'), # 1 us delay
                ('delay',repetition_us),
                ('jumpto','start')
                ])
        if not phase_cycling:
            SpinCore_pp.load([
                ('marker','start',nScans),
                ('phase_reset',1),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',p90_us,0.0),
                ('delay',tau_us),
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,0.0),
                ('delay',deadtime_us),
                ('delay',pad_start),
                ('acquire',acq_time),
                ('delay',pad_end),
                ('marker','echo_label',(nEchoes-1)), # 1 us delay
                ('delay_TTL',deblank_us),
                ('pulse_TTL',2.0*p90_us,0.0),
                ('delay',deadtime_us),
                ('delay',pad_start),
                ('acquire',acq_time),
                ('delay',pad_end),
                ('jumpto','echo_label'), # 1 us delay
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
    print("COMPLEX DATA ARRAY LENGTH:",shape(data_array)[0])
    print("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
    dataPoints = float(shape(data_array)[0])
    if x == 0:
        time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time_ms*1e-3,dataPoints)
        data = ndshape([len(data_array),nScans],['t','nScans']).alloc(dtype=complex128)
        data.setaxis('t',time_axis).set_units('t','s')
        data.setaxis('nScans',r_[0:nScans])
        data.name(node_name)
    data['nScans',x] = data_array
    acq_params = {j: eval(j) for j in dir() if j in [
        "adcOffset",
        "carrierFreq_MHz",
        "amplitude",
        "nScans",
        "nEchoes",
        "p90_us",
        "deadtime_us",
        "repetition_us",
        "SW_kHz",
        "nPoints",
        "deblank_us",
        "tau_us",
        "nPhaseSteps",
        ]
        }
    data.set_prop("acq_params",acq_params)
    SpinCore_pp.stopBoard();
print("EXITING...")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        print("SAVING FILE IN TARGET DIRECTORY...")
        data.hdf5_write(date+'_'+output_name+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/CPMG'))
        print("*** FILE SAVED IN TARGET DIRECTORY ***")
        print("Name of saved data",data.name())
        print("Units of saved data",data.get_units('t'))
        print("Shape of saved data",ndshape(data))
        save_file = False
    except Exception as e:
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
        save_file = False
if not phase_cycling:
    if nScans == 1:
        print(ndshape(data))
        fl.next('raw data')
        fl.plot(data)
        fl.plot(abs(data),':',alpha=0.5)
        data.ft('t',shift=True)
        fl.next('raw data - FT')
        fl.plot(data)
        fl.plot(abs(data),':',alpha=0.5)
    else:
        print(ndshape(data))
        data.reorder('nScans',first=True)
        fl.next('raw data')
        fl.image(data)
        for x in range(len(data.getaxis('nScans'))):
            fl.next('scan %d'%x)
            fl.plot(data['nScans',x])
        data.ft('t',shift=True)
        for x in range(len(data.getaxis('nScans'))):
            fl.next('FT scan %d'%x)
            fl.plot(data['nScans',x])
        fl.next('FT raw data')
        fl.image(data)
if phase_cycling:
    print(ndshape(data))
    s = data.C
    s.set_units('t','s')
    orig_t = s.getaxis('t')
    acq_time_s = orig_t[nPoints]
    fl.next('time')
    fl.plot(abs(s))
    fl.plot(s.real,alpha=0.4)
    fl.plot(s.imag,alpha=0.4)
    s.ft('t',shift=True)
    fl.next('freq')
    fl.plot(abs(s))
    fl.plot(s.real,alpha=0.4)
    fl.plot(s.imag,alpha=0.4)
fl.show();quit()

