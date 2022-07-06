from pyspecdata import *
import configparser
def parser_function(parser_filename):
    #open parser
    config = configparser.ConfigParser()
    config.sections()
    config.read('active.ini')
    acq_params = config['acq_params']
    file_names = config['file_names']
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
    retval['date'] = file_names['date']
    retval['chemical'] = file_names['chemical']
    retval['type'] = file_names['type']
    retval['odnp_counter'] = float(file_names['odnp_counter'])
    retval['echo_counter'] = float(file_names['echo_counter'])
    return retval, config #return dictionary and also the config file itself 
