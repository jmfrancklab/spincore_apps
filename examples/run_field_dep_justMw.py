import sys
import SpinCore_pp
from datetime import datetime
import numpy as np
from Instruments import Bridge12,prologix_connection,gigatronics
from serial import Serial
from Instruments.XEPR_eth import xepr
fl = figlist_var()
logger = init_logging(level='debug')
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

mw_freqs = []

field_axis = r_[3502:3508:.5]
print("Here is my field axis:",field_axis)

# Parameters for Bridge12
powers = r_[3.98]
min_dBm_step = 0.5
for x in range(len(powers)):
    print(powers)
    dB_settings = round(10*(log10(powers[x])+3.0)/min_dBm_step)*min_dBm_step # round to nearest min_dBm_step
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)
#}}}

output_name = '150uM_TEMPO_toluene_cap_probe_field_dep'
adcOffset = 25
gamma_eff = (14.892825/3505.43)
#{{{ acq params
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
coherence_pathway = [('ph1',1)]
date = datetime.now().strftime('%y%m%d')
nPhaseSteps = 4
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
p90 = 4.69
deadtime = 10.0
repetition = 12e6

SW_kHz = 10
acq_ms = 200.
nPoints = int(acq_ms*SW_kHz+0.5)
# rounding may need to be power of 2
tau_adjust = 0
deblank = 1.0
tau = 3500.
pad = 0
#}}}
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#{{{ppg
def run_scans(fieldaxis, nScans=1, B0_index, data = None):
    print("About to run run_scans for", power_idx)
    ph1_cyc = r_[0,1,2,3]
    ph2_cyc = r_[0]
    nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)
    total_pts = nPoints*nPhaseSteps
    data_length = 2*nPoints*nEchoes*nPhaseSteps
    for x in range(nScans):
            logger.debug("\n*** *** *** *** ***\n")
            logger.debug("\n*** *** ***\n")
            logger.debug("CONFIGURING TRANSMITTER...")
            SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
            logger.debug("\nTRANSMITTER CONFIGURED.")
            logger.debug("***")
            logger.debug("CONFIGURING RECEIVER...")
            acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
            logger.debug("\nRECEIVER CONFIGURED.")
            logger.debug("***")
            logger.debug("\nINITIALIZING PROG BOARD...\n")
            SpinCore_pp.init_ppg();
            logger.debug("\nLOADING PULSE PROG...\n")
            SpinCore_pp.load([
                ('marker','start',1),
                ('phase_reset',1),
                ('delay_TTL',deblank),
                ('pulse_TTL',p90,'ph1',ph1_cyc),
                ('delay',tau),
                ('delay_TTL',deblank),
                ('pulse_TTL',2.0*p90,'ph2',ph2_cyc),
                ('delay',deadtime),
                ('acquire',acq_time),
                ('delay',repetition),
                ('jumpto','start')
                ])
            logger.debug("\nSTOPPING PROG BOARD...\n")
            SpinCore_pp.stop_ppg();
            logger.debug("\nRUNNING BOARD...\n")
            SpinCore_pp.runBoard();
            raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
            raw_data.astype(float)
            data_array = []
            data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
            logger.debug("COMPLEX DATA ARRAY LENGTH:",shape(data_array)[0])
            logger.debug("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
            dataPoints = float(np.shape(data_array)[0])
            if data is None:
                time_axis = r_[0:dataPoints]/(SW_kHz*1e3)
                data = ndshape([len(data_array),nScans,len(field_axis),1],['t','nScans','Field','power']).alloc(dtype=np.complex128)
                data.setaxis('t',time_axis).set_units('t','s')
                data.setaxis('nScans',r_[0:nScans])
                data.setaxis('Field',field_axis)
                data.setaxis('power',r_[powers])
                data.name('Field_sweep')
                data.set_prop('acq_params',acq_params)
            data['nScans',x]['Field',B0_index]['power',0] = data_array
            logger.debug(strm("FINISHED B0 INDEX %d..."%B0_index))
            logger.debug("\n*** *** ***\n")
            SpinCore_pp.stopBoard();
            return data
with power_contro() as p:
    dip_f=p.dip_lock(9.81,9.83)
    mw_freqs.append(dip_f)
    with j, this_dB in enumerate(r_[dB_settings]):
        print("\n*** *** *** *** ***\n")
        p.set_power(this_dB)
        for k in range(10):
            time.sleep(0.5)
            if p.get_power_setting()>= this_dB: break
        if p.get_power_setting() < this_dB: raise ValueError("After 10 tries, the power has still not settled")    
        meter_powers = zeros_like(dB_settings)
with xepr() as x_server:
        for B0_index,desired_B0 in enumerate(field_axis):
            true_B0 = x_server.set_field(desired_B0)
            print("My field in G is %f"%true_B0)
            time.sleep(3.0)
            carrierFreq_MHz = gamma_eff*true_B0
            print("My frequency in MHz is",carrierFreq_MHz)
            carrier_Freq_MHz = carrierFreq_MHz
            data = run_scans(fieldaxis, nScans, B0_index) 
#}}}        
acq_params = {j:eval(j) for j in dir() if j in ['tx_phases', 'carrierFreq_MHz','amplitude',
    'nScans','nEchoes','p90','deadtime','repetition','SW_kHz','mw_freqs','nPoints','tau_adjust',
    'deblank','tau','nPhaseSteps']}
data.set_prop('acq_params',acq_params)
myfilename = date+'_'+output_name+'.h5'
save_file = True
while save_file:
    try:
        print("SAVING FILE IN TARGET DIRECTORY...")
        data.hdf5_write(myfilename,
                directory=getDATADIR(exp_type='ODNP_NMR_comp/field_dependent'))
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
fl.plot(data['ph1',1])
fl.plot(data.imag['ph1',1])
fl.show();quit()
