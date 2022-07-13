from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
import configparser
from config_parser_fn import parser_function
fl = figlist_var()
#{{{importing acquisition parameters
values, config = parser_function('active.ini')
nPoints = int(values['acq_time_ms']*values['SW_kHz']+0.5)
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config.set('file_names','type','nutation')
config.set('file_names','date',f'{date}')
echo_counter = values['echo_counter']
echo_counter += 1
config.set('file_names','echo_counter',str(echo_counter))
config.write(open('active.ini','w')) #write edits to config file
values, config = parser_function('active.ini') #translate changes in config file to our dict
filename = str(values['date'])+'_'+values['chemical']+'_'+values['type']+'_'+str(values['echo_counter'])
#}}}

#{{{ Edit here to set the actual field
set_field = False
if set_field:
    B0 = values['Field'] # Determine this from Field Sweep
    thisB0 = xepr().set_field(B0)
#}}}
#{{{phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0,1,2,3]
    ph2_cyc = r_[0,2]
    nPhaseSteps = 8
if not phase_cycling:
    ph1_cyc = r_[0]
    ph2_cyc = r_[0]
    nPhaseSteps = 1
#}}}    
# NOTE: Number of segments is nEchoes * nPhaseSteps
p90_range_us = linspace(1.,15.,5,endpoint=False)
for index,val in enumerate(p90_range_us):
    p90_us = val # us
    print("***")
    print("INDEX %d - 90 TIME %f"%(index,val))
    print("***")
    nutation_data = run_spin_echo(
            nScans = values['nScans'],
            indirect_idx=0,
            indirect_len = len(p90_range_us),
            adcOffset=values['adc_offset'],
            carrierFreq_MHz = values['carrierFreq_MHz'],
            nPoints = nPoints,
            nEchoes = values['nEchoes'],
            p90_us = values['p90_us'],
            repetition = values['repetition_us'],
            tau_us = values['tau_us'],
            SW_kHz = values['SW_kHz'],
            output_name = filename,
            ret_data = None)
SpinCore_pp.stopBoard();
nutation_data.set_prop('acq_params',values)
print("EXITING...\n")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        nutation_data.name(values['type'])
        nutation_data.chunk('t',['ph2','ph1','t2'],[len(ph2_cyc),len(ph1_cyc),-1])
        nutation_data.hdf5_write(myfilename,
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
            nutation_data.hdf5_write(myfilename)
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
