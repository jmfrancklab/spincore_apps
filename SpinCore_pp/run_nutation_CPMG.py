from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
import h5py
from Instruments.XEPR_eth import xepr
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime

fl = figlist_var()
p90_range = linspace(3.,15.,25,endpoint=False)
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "nutation"
config_dict["date"] = f"{date}"
config_dict["echo_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
#{{{ make tqu and phase cycling
tx_phases = r_[0.0,90.0,180.0,270.0]
marker = 1.0
ph1 = r_[0,2]
ph2 = 1
nPhaseSteps = 2
data_length = 2*nPoints*config_dict['nEchoes']*nPhaseSteps
# these are unique to the nutation aspect of it
pad_start = config_dict["tau_extra_us"] - config_dict["deadtime_us"]
pad_end = (
    config_dict["tau_extra_us"] - config_dict["deblank_us"] - marker
)  # marker + deblank
assert (
    pad_start > 0
), "tau_extra_us must be set to more than deadtime and more than deblank!"
assert (
    pad_end > 0
), "tau_extra_us must be set to more than deadtime and more than deblank!"
twice_tau_range = config_dict['deblank_us'] + 2*p90_range + config_dict['deadtime_us'] + pad_start + config_dict['acq_time_ms']*1e3 + pad_end + marker
tau1_range = twice_tau_range/2.0

assert (len(p90_range) == len(twice_tau_range) == len(tau1_range)), "Your axis of 90 times must be the same length as the twice tau and tau1 axes"
#}}}
#{{{ run ppg
nutation_data = run_cpmg(
    nScans=config_dict["nScans"],
    indirect_idx=0,
    indirect_len=len(p90_range_us),
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    nEchoes=config_dict["nEchoes"],
    p90_us=p90_range_us[0],
    repetition=config_dict["repetition_us"],
    pad_start_us = pad_start,
    pad_end_us = pad_end,
    tau_us=tau1_range[0],
    SW_kHz=config_dict["SW_kHz"],
    indirect_fields = ('p90','tau'),
    ph1_cyc = ph1,
    ph2_cyc=ph2,
    ret_data=None,
)
nutation_axis = nutation_data.getaxis('indirect')
nutation_axis[0]['p90'] = p90_range_us[0]
nutation_axis[0]['tau'] = twice_tau_range[0]
for index,val in enumerate(p90_range[1:]):
    p90 = val # us
    tau1 = tau1_range[index+1]
    nutation_axis[index+1]['p90'] = p90
    nutation_axis[index+1]['tau'] = tau1
    nutation_data = run_cpmg(
            nScans=config_dict["nScans"],
            indirect_idx=0,
            ph1_cyc=ph1_cyc,
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            p90_us=p90_range_us[index]],
            repetition=config_dict["repetition_us"],
            tau_us=tau1_range[index+1],
            SW_kHz=config_dict["SW_kHz"],
            pad_start_us=pad_start,
            pad_end_us=pad_end,
            indirect_fields = ('p90','tau'),
            ph1_cyc = ph1,
            ph2_cyc=ph2,
            ret_data=nutation_data,
        )
nutation_data.setprop('acq_params',config_dict.asdict())
#{{{ save
save_file = True
while save_file:
    try:
        nutation_data.name('nutation')
        nutation_data.hdf5_write(filename+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/nutation'))
        print("Name of saved data",nutation_data.name())
        print("Units of saved data",nutation_data.get_units('t'))
        print("Shape of saved data",ndshape(nutation_data))
        save_file = False
    except Exception as e:
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        filename = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(filename) is not 0:
            nutation_data.hdf5_write(filename+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
        save_file = False
#}}}
#{{{ image data
fl.next('raw data')
fl.image(nutation_data)
nutation_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(nutation_data)
fl.show()
#}}}

