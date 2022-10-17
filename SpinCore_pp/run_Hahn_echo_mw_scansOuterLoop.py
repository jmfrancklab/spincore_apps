from pyspecdata import *
import h5py
from Instruments import power_control
from numpy import *
import os,sys,time
import SpinCore_pp
from datetime import datetime
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
from SpinCore_pp.power_helper import gen_powerlist
raise RuntimeError("This pulse program has not been updated.  Before running again, it should be possible to replace a lot of the code below with a call to the function provided by the 'generic' pulse program inside the ppg directory!")
fl = figlist_var()
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/ODNP")
# {{{ import acquisition parameters
config_dict = SpinCore_pp.configuration('active.ini')
nPoints = int(config_dict['acq_time_ms']*config_dict['SW_kHz']+0.5)
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config_dict['type'] = 'old_DNP'
config_dict['date'] = date
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
filename_out = filename + ".h5"
#}}}
#{{{ Power settings
dB_settings = gen_powerlist(config_dict['max_power'],config_dict['power_steps']+1)
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)
phase_cycling = True
if phase_cycling:
    ph1 = r_[0,1,2,3]
    ph2 = r_[0,2]
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
    ph1 = r_[0]
    ph2 = r_[0]
total_pts = nPoints * nPhaseSteps
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"
    % total_pts
)
#}}}    
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
#{{{ run ppg
with power_control() as p:
    # JF points out it should be possible to save time by removing this (b/c we
    # shut off microwave right away), but AG notes that doing so causes an
    # error.  Therefore, debug the root cause of the error and remove it!
    retval_thermal = p.dip_lock(
        config_dict["uw_dip_center_GHz"] - config_dict["uw_dip_width_GHz"] / 2,
        config_dict["uw_dip_center_GHz"] + config_dict["uw_dip_width_GHz"] / 2,
    )
    p.mw_off()
    time.sleep(16.0) #allow B12 to settle
    DNP_data = run_spin_echo(
        nScans= config_dict["nScans"],
        indirect_idx=0,
        indirect_len=len(powers) + 1,
        ph1_cyc=ph1,
        ph2_cyc = ph2,
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        nEchoes=config_dict["nEchoes"],
        p90_us=config_dict["p90_us"],
        repetition=config_dict["repetition_us"],
        tau_us=config_dict["tau_us"],
        SW_kHz=config_dict["SW_kHz"],
        ret_data=None,
    )  # assume that the power axis is 1 longer than the
    #                         "powers" array, so that we can also store the
    #                         thermally polarized signal in this array (note
    #                         that powers and other parameters are defined
    #                         globally w/in the script, as this function is not
    #                         designed to be moved outside the module
    power_settings_dBm = np.zeros_like(dB_settings)
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    DNP_data_powers = DNP_data.getaxis('indirect')
    DNP_data_powers[0] = powers[0]
    for j, this_dB in enumerate(dB_settings):
        logger.debug(
            "SETTING THIS POWER", this_dB, "(", dB_settings[j - 1], powers[j], "W)"
        )
        if j == 0:
            retval = p.dip_lock(
                config_dict["uw_dip_center_GHz"] - config_dict["uw_dip_width_GHz"] / 2,
                config_dict["uw_dip_center_GHz"] + config_dict["uw_dip_width_GHz"] / 2,
            )
        p.set_power(this_dB)
        for k in range(10):
            time.sleep(0.5)
            if p.get_power_setting() >= this_dB:
                break
        if p.get_power_setting() < this_dB:
            raise ValueError("After 10 tries, the power has still not settled")
        time.sleep(5)
        power_settings_dBm[j] = p.get_power_setting()
        run_spin_echo(
            nScans=config_dict["nScans"],
            indirect_idx=j + 1,
            indirect_len=len(powers) + 1,
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            p90_us=config_dict["p90_us"],
            repetition=config_dict["repetition_us"],
            tau_us=config_dict["tau_us"],
            SW_kHz=config_dict["SW_kHz"],
            ret_data=DNP_data,
        )
        DNP_data_powers[j+1] = powers[j+1]
DNP_data.set_prop("postproc_type", "spincore_ODNP_v3")
DNP_data.set_prop("acq_params", config_dict.asdict())
DNP_data.set_prop("stop_time", time.time())
DNP_data.set_prop("postproc_type", "spincore_ODNP_v4")
DNP_data.set_prop("acq_params", config_dict.asdict())
DNP_data.chunk("t", ["ph1", 'ph2',"t2"], [len(ph1),len(ph2), -1])
DNP_data.setaxis("ph1", ph1 / 4)
DNP_data.setaxis('ph2', ph2/ 4)
DNP_data.setaxis('nScans',r_[0:config_dict['nScans']])
DNP_data.reorder(['ph1','ph2','nScans','t2'])
DNP_data.name(config_dict["type"])
#}}}
#{{{ save data
nodename = DNP_data.name()
try:
    DNP_data.hdf5_write(f"{filename_out}",directory = target_directory)
except:
    print(f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp.h5 in the current directory"
        )
    if os.path.exists("temp.h5"):
        print("There is already a temp.h5 -- I'm removing it")
        os.remove("temp.h5")
        DNP_data.hdf5_write("temp.h5", directory=target_directory)
        filename_out = "temp.h5"
        input("change the name accordingly once this is done running!")
logger.info("FILE SAVED")
logger.debug(strm("Name of saved enhancement data", DNP_data.name()))
logger.debug("shape of saved enhancement data", ndshape(DNP_data))
config_dict().write()
#}}}        
#{{{ image data
fl.next('raw data')
DNP_data.rename('indirect','power')
fl.image(DNP_data.setaxis('power','#'))
fl.next('abs raw data')
fl.image(abs(DNP_data).setaxis('power','#'))
DNP_data.ft('t',shift=True)
DNP_data.ft(['ph1','ph2'])
fl.next('raw data - ft')
fl.image(DNP_data.setaxis('power','#'))
fl.next('abs raw data - ft')
fl.image(abs(DNP_data).setaxis('power','#'))
fl.show()
#}}}
