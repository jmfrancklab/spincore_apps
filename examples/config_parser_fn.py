from pyspecdata import *
import configparser
def parser_function(parser_filename):
    #open parser
    config = configparser.ConfigParser()
    config.sections()
    config.read('active.ini')
    acq_params = config['acq_params']
    file_names = config['file_names']
    odnp_params = config['odnp_params']
    retval = {}
    retval['nScans'] = int(acq_params['nScans'])
    retval['p90_us'] = float(acq_params['p90_us'])
    retval['deadtime_us'] = float(acq_params['deadtime_us'])
    retval['adc_offset'] = int(acq_params['adc_offset'])
    retval['amplitude'] = float(acq_params['amplitude'])
    retval['deblank_us'] = float(acq_params['deblank_us'])
    retval['tau_us'] = float(acq_params['tau_us'])
    retval['repetition_us'] = float(acq_params['repetition_us'])
    retval['SW_kHz'] = float(acq_params['sw_khz'])
    retval['acq_time_ms'] = float(acq_params['acq_time_ms'])
    retval['carrierFreq_MHz']=float(acq_params['carrierFreq_MHz'])
    retval['Field'] = float(acq_params['field'])
    retval['nEchoes'] = int(acq_params['nEchoes'])
    
    retval['date'] = file_names['date']
    retval['chemical'] = file_names['chemical']
    retval['type'] = file_names['type']
    retval['odnp_counter'] = file_names['odnp_counter']
    retval['echo_counter'] = file_names['echo_counter']
    retval['IR_counter'] = file_names['IR_counter']

    retval['max_power'] = int(odnp_params['max_power'])
    retval['power_steps'] = int(odnp_params['power_steps'])
    retval['num_T1s'] = int(odnp_params['num_T1s'])
    retval['uw_dip_center_GHz'] = float(odnp_params['uw_dip_center_GHz'])
    retval['uw_dip_width_GHz'] = float(odnp_params['uw_dip_width_GHz'])
    retval['FIR_rep'] = float(odnp_params['FIR_rep'])
    return retval, config #return dictionary and also the config file itself 
