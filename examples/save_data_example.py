from numpy import *
from pyspecdata import *
import os
import sys
import SpinCore_pp
import time
from Instruments import power_control
from Instruments import Bridge12,prologix_connection,gigatronics
from Instruments.XEPR_eth import xepr
from SpinCore_pp.power_helper import gen_powerlist
#{{{ params for Bridge 12/power
dB_settings = gen_powerlist(max_power,power_steps)
powers = 1e-3*10**(dB_settings/10.)
#}}}
DNP_data = None
#{{{ simplified pulse prog
def run_scans(nScans, power_idx, field_idx, DNP_data=None):
    """run nScans and slot them into the power_idx index of DNP_data -- assume
    that the first time this is run, it will be run with DNP_data=None and that
    after that, you will pass in DNP_data
    
    assume that the power axis is 1 longer than the "powers" array
    (note that powers and other parameters are defined globally w/in the
    script, as this function is not designed to be moved outside the module
    """
    for x in range(nScans):
        run_scans_time_list = [time.time()]
        SpinCore_pp.configureTX(26, 14.894179, r_[0.0,90.0,180.0,270.0], 1.0, 2048)#adc_offset, carrierFreq_MHz, tx_phases, amplitude, nPoints
        acq_time_ms = SpinCore_pp.configureRX(24, 2048, 1, 1, 4)#SW_kHz, nPoints, 1, nEchoes, nPhaseSteps
        SpinCore_pp.init_ppg()
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',1.0),#deblank
            ('pulse_TTL',4.69,'ph1',r_[0,1,2,3]),#90 pulse
            ('delay',3500),#tau
            ('delay_TTL',1.0),#deblank
            ('pulse_TTL',9.38,'ph2',r_[0]),#180 pulse
            ('delay',10.0),#deadtime
            ('acquire',85.3),#acquisition time
            ('delay',15e6),#repetition delay
            ('jumpto','start')
            ])
        SpinCore_pp.stop_ppg()
        SpinCore_pp.runBoard()
        raw_data = SpinCore_pp.getData(16384, 2048, 1, 4, 'field_sweep')#data_length,nPoints,nEchoes, nPhaseSteps,output name
        data_array = complex128(raw_data[0::2]+1j*raw_data[1::2])
        dataPoints = int(shape(data_array)[0])
        if DNP_data is None and power_idx ==0 and field_idx == 0:
            time_axis = linspace(0.0,0.3412,2048)#nEchoes*nPhaseSteps*acq_time_ms*1e-3, nPoints
            DNP_data = ndshape([len(powers),len(r_[3503:3508:0.1]),1,dataPoints],['power','field','nScans','t']).alloc(dtype=complex128)
            DNP_data.setaxis('power',r_[powers]).set_units('W')
            DNP_data.setaxis('field',r_[3503:3508:0.1]).set_units('G')
            DNP_data.setaxis('t',time_axis).set_units('t','s')
            DNP_data.setaxis('nScans',r_[0:1])
            DNP_data.name('field_sweep_fine')
        DNP_data['power',power_idx]['field',field_idx]['nScans',x] = data_array
        SpinCore_pp.stopBoard()
        return DNP_data
#}}}
#{{{where error occurs
meter_powers = zeros_like(dB_settings)
carrierFreqs_MHz = zeros_like(r_[3503:3508:0.1], dtype=float)
fields_Set = zeros_like(r_[3503:3508:0.1],dtype=float)
with power_control() as p:
    for j,this_dB in enumerate(dB_settings):
        if j == 0:
            MWfreq = p.dip_lock(9.81,9.83)
            p.start_log()
        p.set_power(this_dB)
        for k in range(10):
            time.sleep(0.5)
            if p.get_power_setting() >= this_dB: break
        if p.get_power_setting() < this_dB: raise ValueError("After 10 tries, the power has still not settled")
        time.sleep(5)
        meter_powers[j] = p.get_power_setting()
        with xepr() as x_server:
            for B0_index,desired_B0 in enumerate(r_[3503:3508:0.1]):
                true_B0 = x_server.set_field(desired_B0)
                print("My field in G is %f"%true_B0)
                time.sleep(3.0)
                carrierFreq_MHz = 0.00425*true_B0
                carrierFreqs_MHz[B0_index] = carrierFreq_MHz
                fields_Set[B0_index] = true_B0
                print("My frequency in MHz is",carrierFreq_MHz)
                if DNP_data is None:
                    DNP_data = run_scans(1, j, B0_index, DNP_data = None)
                else:
                    DNP_data = run_scans(1, j, B0_index, DNP_data)
    log_array, log_dict = p.stop_log()# where error occurred originally!
    #}}}

