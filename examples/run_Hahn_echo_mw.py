'''Run an Enhancement Experiment
================================
Uses power control server so this will need to be running in sync. To do so:
    1. Open Xepr on the EPR computer, connect to spectrometer, and enable XEPR_API.
    2. In a separate terminal on the EPR computer, run the program XEPR_API_server.py and wait for it to tell you 'I am listening'.
    3. On the NMR computer, open a separate terminal in git/inst_notebooks/Instruments and run winpty power_control_server(). When ready to go it will say 'I am listening'.
    4. run this program to collect data
'''    
from pyspecdata import *
from numpy import *
import os
import sys
import SpinCore_pp
from Instruments import Bridge12,prologix_connection,gigatronics
from serial import Serial
import time
from datetime import datetime
from SpinCore_pp.power_helper import gen_powerlist

fl = figlist_var()
# {{{ experimental parameters
#{{{power settings
max_power = 4 #W
power_steps = 18
dB_settings = gen_powerlist(max_power,power_steps)
append_dB = [dB_settings[abs(10**(dB_settings/10.-3)-max_power*frac).argmin()]
        for frac in [0.75,0.5,0.25]]
dB_settings = append(dB_settings,append_dB)
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)
#}}}
date = datetime.now().strftime('%y%m%d')
output_name = 'TEMPOL_289uM_heat_exch_0C'
node_name = 'enhancement'
adcOffset = 28
carrierFreq_MHz = 14.549013
nScans = 1
nEchoes = 1
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 4
    Ep_ph1_cyc = r_[0, 1, 2, 3]

if not phase_cycling:
    nPhaseSteps = 1
    Ep_ph1_cyc = r_[0]
p90_us = 1.781
repetition_us = 10e6
SW_kHz = 3.9
acq_ms = 1024.
nPoints = int(acq_ms*SW_kHz+0.5)
tau = 3500
Ep_postproc = "spincore_ODNP_v3"
uw_dip_center_GHz = 9.82
uw_dip_width_GHz = 0.02
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#}}}
#{{{check for file
myfilename = date + '_'+output_name+'.h5'
if os.path.exists(myfilename):
    raise ValueError(
            "the file %s already exists, change your output name!"%myfilename)
#}}}    
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
with power_control() as p:
    retval_thermal = p.dip_lock(
        uw_dip_center_GHz - uw_dip_width_GHz / 2,
        uw_dip_center_GHz + uw_dip_width_GHz / 2,
    )
    p.mw_off()
    DNP_data = run_spin_echo(
        nScans=nScans,
        indirect_idx=0,
        indirect_len=len(powers) + 1,
        ph1_cyc=Ep_ph1_cyc,
        adcOffset=adcOffset,
        carrierFreq_MHz=carrierFreq_MHz,
        nPoints=nPoints,
        nEchoes=nEchoes,
        p90_us=p90_us,
        repetition=repetition_us,
        tau_us=tau_us,
        SW_kHz=SW_kHz,
        output_name=output_name,
        ret_data=None,
    )  # assume that the power axis is 1 longer than the
    #                         "powers" array, so that we can also store the
    #                         thermally polarized signal in this array (note
    #                         that powers and other parameters are defined
    #                         globally w/in the script, as this function is not
    #                         designed to be moved outside the module
    power_settings_dBm = np.zeros_like(dB_settings)
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    for j, this_dB in enumerate(dB_settings):
        logger.debug(
            "SETTING THIS POWER", this_dB, "(", dB_settings[j - 1], powers[j], "W)"
        )
        if j == 0:
            retval = p.dip_lock(
                uw_dip_center_GHz - uw_dip_width_GHz / 2,
                uw_dip_center_GHz + uw_dip_width_GHz / 2,
            )
        logger.debug("done with dip lock 1")
        p.set_power(this_dB)
        logger.debug("power was set")
        for k in range(10):
            time.sleep(0.5)
            if p.get_power_setting() >= this_dB:
                break
        if p.get_power_setting() < this_dB:
            raise ValueError("After 10 tries, the power has still not settled")
        time.sleep(5)
        power_settings_dBm[j] = p.get_power_setting()
        logger.debug("gonna run the Ep for this power")
        run_spin_echo(
            nScans=nScans,
            indirect_idx=j + 1,
            indirect_len=len(powers) + 1,
            adcOffset=adcOffset,
            carrierFreq_MHz=carrierFreq_MHz,
            nPoints=nPoints,
            nEchoes=nEchoes,
            p90_us=p90_us,
            repetition=repetition_us,
            tau_us=tau_us,
            SW_kHz=SW_kHz,
            output_name=output_name,
            ret_data=DNP_data,
        )
DNP_data.set_prop("postproc_type", Ep_postproc)
acq_params = {
    j: eval(j)
    for j in dir()
    if j
    in [
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
        "MWfreq",
        "power_settings_dBm",
    ]
}
DNP_data.set_prop("acq_params", acq_params)
DNP_data.name("enhancement")
DNP_data.chunk("t", ["ph1", "t2"], [4, -1])
DNP_data.setaxis("ph1", Ep_ph1_cyc / 4)
logger.info("SAVING FILE... %s" % myfilename)
DNP_data.hdf5_write(myfilename)
logger.info("FILE SAVED")
logger.debug(strm("Name of saved enhancement data", DNP_data.name()))
logger.debug("shape of saved enhancement data", psp.ndshape(DNP_data))
# }}}
fl.next('raw data_array')
fl.image(DNP_data.C.setaxis('power',
    '#').set_units('power','scan #'))
fl.next('abs raw data_array')
fl.image(abs(DNP_data).C.setaxis('power',
    '#').set_units('power','scan #'))
DNP_data.ft('t',shift=True)
DNP_data.ft(['ph1'])
fl.next('raw data_array - ft')
fl.image(DNP_data.C.setaxis('power','#'))
fl.next('abs raw data_array - ft')
fl.image(abs(DNP_data.C.setaxis('power','#')))
fl.show();quit()
