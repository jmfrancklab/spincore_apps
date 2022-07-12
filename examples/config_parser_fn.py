from pyspecdata import *
import configparser
def parser_function(parser_filename):
    #open parser
    config = configparser.ConfigParser()
    config.sections()
    config.read('active.ini')
    acq_params = config['acq_params']
    file_names = config['file_names']
    DNP_params = config['DNP_params']
    retval = {}
    retval['nScans'] = float(acq_params['nScans'])
    retval['p90_us'] = float(acq_params['p90_us'])
    retval['deadtime_us'] = float(acq_params['deadtime_us'])
    retval['adc_offset'] = float(acq_params['adc_offset'])
    retval['amplitude'] = float(acq_params['amplitude'])
    retval['deblank_us'] = float(acq_params['deblank_us'])
    retval['tau_us'] = float(acq_params['tau_us'])
    retval['repetition_us'] = float(acq_params['repetition_us'])
    retval['SW_kHz'] = float(acq_params['sw_khz'])
    retval['acq_time_ms'] = float(acq_params['acq_time_ms'])
    retval['nEchoes'] = float(acq_params['nEchoes'])
    retval['date'] = file_names['date']
    retval['chemical'] = file_names['chemical']
    retval['type'] = file_names['type']
    retval['odnp_counter'] = float(file_names['odnp_counter'])
    retval['echo_counter'] = float(file_names['echo_counter'])
    retval['FIR_rep'] = float(DNP_params['FIR_rep'])
    retval['max_power'] = float(DNP_params['max_power'])
    retval['power_steps'] = int(DNP_params['power_steps'])
    retval['uw_dip_center_GHz'] = float(DNP_params['uw_dip_center_GHz'])
    retval['us_dip_width_GHz'] = float(DNP_params['uw_dip_width_GHz'])
    retval['num_T1s'] = int(DNP_params['num_T1s'])
    return retval, config #return dictionary and also the config file itself 
