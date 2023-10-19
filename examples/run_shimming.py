"""ppg for obtaining performing shimming calibration
=====================================================
The following is used when the shims are replaced or moved in any way. When moved the calibration or settings for the z and y shims need to be recalculated for certainty. Here, the user can calculate the appropriate voltage setting for each shim for optimal signal. Note: The XEPR_API server must be running for this script. Normally this script is run with 4 scans 
"""
from pylab import *
from pyspecdata import *
import os, sys
import SpinCore_pp
from datetime import datetime
import numpy as np
from Instruments.XEPR_eth import xepr
from Instruments import HP6623A, prologix_connection
#{{{ Verify arguments compatible with board
def verifyParams():
    if (nPoints > 16*1024 or nPoints < 1):
        print("ERROR: MAXIMUM NUMBER OF POINTS IS 16384.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED NUMBER OF POINTS.")
    if (config_dict['nScans'] < 1):
        print("ERROR: THERE MUST BE AT LEAST 1 SCAN.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED NUMBER OF SCANS.")
    if (config_dict['p90_us'] < 0.065):
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
target_directory = getDATADIR(exp_type"ODNP_NMR_comp/test_equipment")
#{{{ importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict['acq_time_ms']*config_dict['SW_kHz']+0.5)
#}}}
#{{{filename
date = datetime.now().strftime('%y%m%d')
config_dict['date'] = date
filename = f"{config_dict['date']}_{config_dict['chemical']}_shimming" + ".h5"
#}}}
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
config_dict['tau_us'] = 2500. + config_dict['deadtime_us']
#{{{set up voltage info for the test 
data_length = 2*nPoints*config_dict['nEchoes']*nPhaseSteps
voltage_array = r_[0.0:0.15:0.01]
current_readings = ones_like(voltage_array)
voltage_readings = ones_like(voltage_array)
# channel that is currently being investigated
test_ch = 3
# channel that was previously investigated/has predetermined value that you want to set 
# set_ch : (ch #, voltage setting)
set_ch = [(2,0.1)]
#}}}
#}}}
#{{{set field
print("I'm assuming that you've tuned your probe to",
        config_dict['carrierFreq_MHz'],
        "since that's what's in your .ini file",
        )
Field = config_dict['carrierFreq_MHz']/config_dict['gamma_eff_MHz_G']
print(
        "Based on that, and the gamma_eff_MHz_G you have in your .ini file, I'm setting the field to %f"
        %Field
        )
with xepr() as x:
    assert Field < 3700, "are you crazy??? field is too high!"
    assert Field > 3300, "are you crazy?? field is too low!"
    Field = x.set_field(Field)
    print("field set to ",Field)
#}}}
#{{{phase cycling steps
ph1_cyc = r_[0,1,2,3]
ph2_cyc = r_[0,2]
nPhaseSteps = 8
#}}}    
#{{{ Check total points
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#}}}
#{{{ Run actual ppg
with prologix_connection() as p:
    with HP6623A(prologix_instance=p, address=5) as HP:
        for index,this_val in enumerate(voltage_array):
            if index == 0:
                HP.set_voltage(set_ch[0][0],set_ch[0][1])
                HP.set_voltage(test_ch,0.0)
                HP.set_current(test_ch,0.0)
                this_curr = HP.get_current(test_ch)
                this_volt = HP.get_voltage(test_ch)
                current_readings[0] = this_curr
                voltage_readings[0] = this_volt
                HP.output(test_ch,False)
                HP.output(set_ch[0][0],True)
            else:
                HP.set_voltage(test_ch,this_val)
                this_curr = HP.get_current(test_ch)
                this_volt = HP.get_voltage(test_ch)
                current_readings[index] = this_curr
                voltage_readings[index] = this_volt
                HP.output(test_ch,True)
                get_volt_ch1 = HP.get_voltage(1)
                get_volt_ch2 = HP.get_voltage(2)
                get_volt_ch3 = HP.get_voltage(3)
                get_volt = [('ch1',get_volt_ch1),
                        ('ch2',get_volt_ch2),
                        ('ch3',get_volt_ch3)]
                acq_params['shim_readings'] = get_volt
            print("CURRENT READING IS: %f"%this_curr)
            for x in range(config_dict['nScans']):
                SpinCore_pp.configureTX(config_dict['adc_offset'], config_dict['carrierFreq_MHz'], tx_phases, amplitude, nPoints)
                config_dict['acq_time_ms'] = SpinCore_pp.configureRX(config_dict['SW_kHz'], nPoints, 1, config_dict['nEchoes'], nPhaseSteps)
                verifyParams()
                SpinCore_pp.init_ppg();
                if phase_cycling:
                    SpinCore_pp.load([
                        ('marker','start',1),
                        ('phase_reset',1),
                        ('delay_TTL',config_dict['deblank_us']),
                        ('pulse_TTL',config_dict['p90_us'],'ph1',r_[0,1,2,3]),
                        ('delay',tau),
                        ('delay_TTL',config_dict['deblank_us']),
                        ('pulse_TTL',2.0*config_dict['p90_us'],'ph2',r_[0,2]),
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
                        ('delay',tau),
                        ('delay_TTL',config_dict['deblank_us']),
                        ('pulse_TTL',2.0*config_dict['p90_us'],0),
                        ('delay',config_dict['deadtime_us']),
                        ('acquire',config_dict['acq_time_ms']),
                        ('delay',config_dict['repetition_us']),
                        ('jumpto','start')
                        ])
                SpinCore_pp.stop_ppg();
                SpinCore_pp.runBoard();
                raw_data = SpinCore_pp.getData(data_length, nPoints, config_dict['nEchoes'], nPhaseSteps, output_name)
                raw_data.astype(float)
                data_array = []
                data_array[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
                dataPoints = float(np.shape(data_array)[0])
                if index == 0 and x == 0:
                    time_axis = np.linspace(0,config_dict['nEchoes']*nPhaseSteps*config_dict['acq_time_ms']*1e-3,int(dataPoints))
                    shim_data = ndshape([len(data_array),config_dict['nScans'],len(current_readings)],['t','nScans','I']).alloc(dtype=complex128)
                    shim_data.setaxis('t',time_axis).set_units('t','s')
                    shim_data.setaxis('nScans',r_[0:config_dict['nScans']])
                    shim_data.setaxis('I',current_readings).set_units('I','A')
                    shim_data.name("shims_addr5_Z_yOpt")
                    acq_params['voltage_setting'] = voltage_array
                    acq_params['voltage_reading'] = voltage_readings
                    acq_params['current_reading'] = current_readings
                    acq_params['shim_settings'] = set_ch
                    shim_data.set_prop('acq_params',acq_params)
                shim_data['nScans',x]['I',index] = data_array
                SpinCore_pp.stopBoard();
        print("Turning shim power off")
        HP.output(test_ch,False)
print("EXITING...")
print("\n*** *** ***\n")
#}}}
#{{{save acquisition parameters
shim_data.set_prop("postproc_type","proc_Hahn_echoph")
shim_data.set_prop("acq_params",config_dict.asdict())
shim_data.name('shimming'+'_'+str(config_dict['echo_counter']))
#}}}
#{{{saving file
nodename = shim_data.name()
if os.path.exists(filename):
    print('this file already exists so we will add a node to it!')
    with h5py.File(os.path.normpath(os.path.join(target_directory,
        f"{filename}"))) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, lets delete it to overwrite")
            del fp[nodename]
    shim_data.hdf5_write(f'{filename}/{nodename}', directory = target_directory)
else:
    try:
        shim_data.hdf5_write(filename,
                directory=target_directory)
    except:
        print(f"I had problems writing to the correct file {filename}, so I'm going to try to save your file to temp.h5 in the current directory")
        if os.path.exists("temp.h5"):
            print("there is a temp.h5 -- I'm removing it")
            os.remove('temp.h5')
        shim_data.hdf5_write('temp.h5')
        print("if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!")
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data",shim_data.name()))
config_dict.write()
#}}}
#{{{Plotting
shim_data.set_units('t','data')
with figlist_var() as fl:
    shim_data.chunk('t',['ph2','ph1','t2'],[len(ph2_cyc),len(ph1_cyc),-1])
    shim_data.setaxis('ph2',ph2_cyc/4)
    shim_data.setaxis('ph1',ph1_cyc/4)
    if config_dict['nScans'] > 1:
        shim_data.setaxis('nScans',r_[0:config_dict['nScans']])
    fl.next('image')
    shim_data.mean('nScans')
    fl.image(shim_data.C.setaxis('I','#'))
    t2_max = shim_data.getaxis('t2')[-1]
    shim_data -= shim_data['t2':(0.75*t2_max,None)].C.mean('t2')
    shim_data.ft('t2',shift=True)
    fl.next('image - ft')
    fl.image(shim_data.C.setaxis('I','#'))
    fl.next('image - ft, coherence')
    shim_data.ft(['ph1','ph2'])
    fl.image(shim_data.C.setaxis('I','#'))
    fl.next('data plot')
    data_slice = shim_data['ph1',1]['ph2',-2]
    fl.plot(data_slice, alpha=0.5)
    fl.plot(abs(data_slice), color='k', alpha=0.5)
fl.show()
#}}}
