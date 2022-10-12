from pyspecdata import *
import configparser

class configuration(object):
    # this registers the type, the pretty case we want, the section, and
    # whether or not we can assume a default value
    registered_params = {
        "amplitude":(float, "acq_params", None,"amplitude of the ppg"),
        "deadtime_us":(float, "acq_params", None,"deadtime in microseconds used in the ppg"),
        "tau_us":(float, "acq_params", None,"echo time (microseconds) used in ppg"),
        "deblank_us":(float, "acq_params", None, "deblanking time used in ppg in microseconds"),
        "SW_kHz":(float, "acq_params", None, "Spectral width of acquisition in kHz"),
        "acq_time_ms":(float, "acq_params", None, "acquisition time in milliseconds - used in ppg"),
        "carrierFreq_MHz":(float, "acq_params", None,"Carrier Frequency ppg is carried out at in MHz"),
        "startconstant":(float, "acq_params", None,"fraction of repetition delay that is used to start the low end of the vd list"),
        "stopconstant":(float, "acq_params", None,"fraction of the repetition delat used as the las vd in the vd list"),
        "p90_us":(float, "acq_params", None, "90 time specific to the probe - microseconds"),
        "gamma_eff_MHz_G":(float, "acq_params", 0.00425, "gamma effective - ratio between the carrier frequency and the ESR frequency"),
        "field_width":(float,"acq_params",6, "number of points collected in field sweep"),
        "concentration":(float, "sample_params", None, "Concentration of spin label in sample - Molar"),
        "krho_cold":(float, "sample_params", None, "k_rho value acquired at low temperatures"),
        "krho_hot":(float, "sample_params", None, "k_rho values acquired at high temperature"),
        "T1water_hot":(float, "sample_params", None, "T1 time of pure water at high power/temperature"),
        "T1water_cold":(float, "sample_params", None "T1 time of pure water at low power/temperature"),
        "guessed_MHz_to_GHz":(float,"sample_params", 1.51671, "the ppt value we use to determine our rf carrier frequency based on our microwave")
        "max_power":(float, "odnp_params", None,"maximum power you plan on acquiring data for - upper end of your power list for ODNP"),
        "uw_dip_center_GHz":(float, "odnp_params", None, "ESR frequency - GHz"),
        "uw_dip_width_GHz":(float, "odnp_params", None, "width over which our dip lock will span"),
        "FIR_rep":(float, "odnp_params", None, "Fast inversion recovery repetition delay (2 X T1)"),
        "adc_offset":(int, "acq_params", None, "analog to DC offset"),
        "nScans":(int, "acq_params", 1, "number of scans"),
        "thermal_nScans":(int, "acq_params",1, "number of scans acquired in the control echo in odnp as well as the number of scans used to acquire the FIR at no power"),
        "nEchoes":(int, "acq_params", None,"number of echoes"),
        "IR_steps":(int, "acq_params", None, "number of steps when performing a single IR experiment"),
        "power_steps":(int, "odnp_params", None, "steps in the enhancement taken between no power and high power"),
        "num_T1s":(int, "odnp_params", None, "number of T1's acquired in the ODNP ppg"),
        "odnp_counter":(int, "file_names", 0, "number of times you've acquired odnp"),
        "echo_counter":(int, "file_names", 0, "number of times you've acquired an echo"),
        "cpmg_counter":(int, "file_names", 0, "number of times you've acquired a cpmg dataset"),
        "IR_counter":(int, "file_names", 0, "number of times you've acquired IR data"),
        "field_counter":(int,"file_names",0,"number of times you've performed a field sweep"),
        "date":(int, "file_names", None,"today's date"),
        "chemical":(str, "file_names", None,"the name of your sample - advised to include concentration"),
        "type":(str, "file_names", None, "type of experiment last performed"),
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
                raise KeyError(f"You're asking for the '{key}' parameter, and it's not set in the .ini file!\nFirst, ask yourself if you should have run some type of set-up program (tuning, adc offset, resonance finder, etc.) that would set this parameter.\nThen, try setting the parameter in the appropriate section of your .ini file by editing the file with gvim or notepad++!")
            else:
                return default
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
            self.configobj.write(open(self.filename,'w'))
    def asdict(self):
        return self._params
