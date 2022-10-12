from pyspecdata import *
import configparser

class configuration(object):
    # this registers the type, the pretty case we want, the section, and
    # whether or not we can assume a default value
    registered_params = {
        "amplitude":(float, "acq_params", None,
            "amplitude of the pulse"),
        "deadtime_us":(float, "acq_params", None,
            "delay between the pulse and tau"),
        "tau_us":(float, "acq_params", None,
            "extra delay added between 90° and 180° pulse -- note this is not the same as τ_echo!\nsee eq 6 of coherence paper"),
        "deblank_us":(float, "acq_params", None,
            "time for the TTL to deblank"),
        "SW_kHz":(float, "acq_params", None,
            "spectral width of data acquisition in kHz"),
        "acq_time_ms":(float, "acq_params", None,
            "acquisition time in milliseconds - we've found 1024.0 to work well"),
        "carrierFreq_MHz":(float, "acq_params", None,
            "carrierfrequency in MHz - usually around 14.89 MHz"),
        "startconstant":(float, "acq_params", None,
            "fraction of the repetition delay (0.15) that starts our vd list composition in FIR"),
        "stopconstant":(float, "acq_params", None,
            "fraction of the repetition delay, that is the upper limit of our FIR vd list"),
        "p90_us":(float, "acq_params", None,
            "90 time of the probe in microseconds"),
        "gamma_eff_MHz_G":(float, "acq_params", 0.00425,
            "the ratio of the NMR resonance frequency to the resonance frequency of the B12"),
        "field_width":(float,"acq_params",6,
            "number of points collected in a field sweep, for a finer data acquisition increase this number"),
        "tau_extra_us":(float, "acq_params", 1000.0,
            "amount of extra time both before and after the acquisition during a symmetric echo sequence"),
        "concentration":(float, "sample_params", None,
            "concentration of spin label in the sample in M"),
        "krho_cold":(float, "sample_params", None,
            "the self relaxivity constant of the specific sample at low temperatures/low power"),
        "krho_hot":(float, "sample_params", None,
            "the self relaxivity constant of the specific sample at high temperature/high power"),
        "T1water_hot":(float, "sample_params", None,
            "T1 of ultra pure water at high powers - this really should not change unless a new measurement is made"),
        "T1water_cold":(float, "sample_params", None,
            "T1 of ultra pure water at low powers - this really should not change unless a new measurement is made"),
        "repetition_us":(float, "sample_params", None,
            "repetition delay in microseconds"),
        "guessed_MHz_to_GHz":(float,"sample_params", 1.51671,
            "the ppt value we use to determine our rf carrier frequency based on our microwave"),
        "max_power":(float, "odnp_params", None,
            "the highest power you plan on acquiring data at - in W"),
        "uw_dip_center_GHz":(float, "odnp_params", None,
            "ESR resonance frequency found by minimizing the B12 dip at increasing powers"),
        "uw_dip_width_GHz":(float, "odnp_params", None,
            "the range over which the dip lock will be performed"),
        "FIR_rep":(float, "odnp_params", None,
            "fast inversion recovery repetition delay (should be around 2 x T1"),
        "adc_offset":(int, "acq_params", None,
            "analog to DC conversion factor"),
        "nScans":(int, "acq_params", 1,
                "number of scans"),
        "thermal_nScans":(int, "acq_params",1,
                "number of thermal scans - useful for no power datasets with low signal"),
        "nEchoes":(int, "acq_params", None,
                "number of echoes - usually kept at 1"),
        "IR_steps":(int, "acq_params", None,
                "number of points collected in an IR experiment between the min and max time points"),
        "power_steps":(int, "odnp_params", None,
                "number of points collected in an enhancement experiment"),
        "num_T1s":(int, "odnp_params", None,
                "number of IR experiments collected in the ODNP experiment"),
        "odnp_counter":(int, "file_names", 0,
                "number of ODNP experiments that have been performed so far for that particular sample on that day"),
        "echo_counter":(int, "file_names", 0,
                "number of echo experiments performed for a particular sample that day- usually incremented when getting on resonance"),
        "cpmg_counter":(int, "file_names", 0,
                "number of cpmg experiments performed for a particular sample that day"),
        "IR_counter":(int, "file_names", 0,
                "number of inversion recovery experiments performed for a particular sample that day"),
        "field_counter":(int,"file_names",0,
                "number of field sweeps performed for a particular sample that day"),
        "date":(int, "file_names", None,"today's date"),
        "chemical":(str, "file_names", None, "name specific to the sample - your data set will be named: date_chemical_type"),
        "type":(str, "file_names", None,
                "type of experiment being performed"),
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
                converter, section, default,_) in self.registered_params.items():
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
            converter, section, default,_ = self.registered_params[key]
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
            converter, section, default,_ = self.registered_params[key]
            self._params[key] = converter(value) # check that it's the right type
            self.configobj.set(section,key.lower(),
                    str(self._params[key]))
    def keys(self):
        return self._params.keys()
    def write(self):
        for paramname,(converter, section, default,_) in self.registered_params.items():
            if paramname in self._params.keys():
                self.configobj.set(section,paramname.lower(),
                        str(self._params[paramname]))
            self.configobj.write(open(self.filename,'w'))
    def asdict(self):
        return self._params
