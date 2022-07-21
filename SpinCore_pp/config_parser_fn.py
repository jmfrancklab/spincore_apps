from pyspecdata import *
import configparser

class configuration(object):
    # this registers the type, the pretty case we want, the section, and
    # whether or not we can assume a default value
    registered_params = {
        "p90_us":(float, "acq_params", None),
        "deadtime_us":(float, "acq_params", None),
        "amplitude":(float, "acq_params", None),
        "deblank_us":(float, "acq_params", None),
        "tau_us":(float, "acq_params", None),
        "repetition_us":(float, "acq_params", None),
        "SW_kHz":(float, "acq_params", None),
        "acq_time_ms":(float, "acq_params", None),
        "carrierFreq_MHz":(float, "acq_params", None),
        "gamma_eff_MHz_G":(float, "acq_params", 0.00425),
        "Field":(float, "odnp_params", None),
        "uw_dip_center_GHz":(float, "odnp_params", None),
        "uw_dip_width_GHz":(float, "odnp_params", None),
        "FIR_rep":(float, "odnp_params", None),
        "max_power":(float, "odnp_params", None),
        "nScans":(int, "acq_params", 1),
        "adc_offset":(int, "acq_params", None),
        "nEchoes":(int, "acq_params", None),
        "power_steps":(int, "odnp_params", None ),
        "num_T1s":(int, "odnp_params", None),
        "odnp_counter":(int, "file_names", 0),
        "echo_counter":(int, "file_names", 0),
        "cpmg_counter":(int, "file_names", 0),
        "IR_counter":(int, "file_names", 0),
        "chemical":(str, "file_names", None),
        "type":(str, "file_names", None),
        "date":(int, "file_names", None),
        "IR_steps":(int, "acq_params", None),
        "startconstant":(float, "acq_params", None),
        "stopconstant":(float, "acq_params", None),
        "krho_cold":(float, "sample_params", None),
        "krho_hot":(float, "sample_params", None),
        "T1water_cold":(float, "sample_params", None),
        "T1water_hot":(float, "sample_params", None),
        "concentration":(float, "sample_params", None),
        }
    def __init__(self,filename):
        self.filename = filename
        self.configobj = configparser.ConfigParser()
        self.configobj.read(self.filename)
        self._params = {}
        for j in ["acq_params", "odnp_params", "file_names"]:
            if j not in self.configobj.sections():
                self.configobj.add_section(j)
        for paramname, (
                converter, section, default) in self.registered_params.items():
            try:
                temp = self.configobj.get(section,paramname.lower())
            except:
                continue
            self._params[paramname] = converter(temp)
            self._case_insensitive_keys = {j.lower():j
                    for j in self.registered_params.keys()}
    def __getitem__(self,key):
        key = self._case_insensitive_keys[key.lower()]
        if key not in self._params.keys():
            converter, section, default = self.registered_params[key]
            if default is None:
                    raise ValueError(f"You're asking for the '{key}' parameter, and it's not set in the .ini file!\nFirst, ask yourself if you should have run some type of set-up program (tuning, adc offset, resonance finder, etc.) that would set this parameter.\nThen, try setting the parameter in the appropriate section of your .ini file by editing the file with gvim or notepad++!")

        return self._params[key]
    def __setitem__(self,key,value):
        if key.lower() not in self._case_insensitive_keys.keys():
            raise ValueError(f"I don't know what section to put the {key} setting in, or what type it's supposed to be!!  You should register it's existence in the config_parser_fn subpackage before trying to use it!! (Also -- do you really need another setting??)")
        else:
            key = self._case_insensitive_keys[key.lower()]
            converter, section, default = self.registered_params[key]
            self._params[key] = converter(value) # check that it's the right type
            self.configobj.set(section,key.lower(),
                    str(self._params[key]))
    def keys(self):
        return self._params.keys()
    def write(self):
        for paramname,(converter, section, default) in self.registered_params.items():
            if paramname in self._params.keys():
                self.configobj.set(section,paramname.lower(),
                        str(self._params[paramname]))
        self.configobj.write(open('active.ini','w'))
    def asdict(self):
        return self._params
