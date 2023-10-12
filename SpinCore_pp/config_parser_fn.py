from pyspecdata import *
import configparser


class configuration(object):
    # this registers the type, the pretty case we want, the section, and
    # whether or not we can assume a default value
    registered_params = {
        "amplitude": (float, "acq_params", None, "amplitude of the pulse"),
        "deadtime_us": (float, "acq_params", None, "mandatory delay after the pulse -- allows receivers to recover"),
        "tau_us": (
            float,
            "acq_params",
            None,
            "extra delay added between 90° and 180° pulse -- note this is not the same as τ_echo!\nsee eq 6 of coherence paper",
        ),
        "deblank_us": (float, "acq_params", None, "type between the deblank TTL pulse and the actual pulse itself"),
        "SW_kHz": (
            float,
            "acq_params",
            None,
            "spectral width of data acquisition in kHz",
        ),
        "acq_time_ms": (
            float,
            "acq_params",
            None,
            "acquisition time in milliseconds - we've found 1024.0 to work well",
        ),
        "echo_acq_ms": (
            float,
            "acq_params",
            None,
            "Length of acquisition during stroboscopic echo acquisition, in milliseconds.  Keep this separate from acq_time_ms to avoid confusion, because there are many echo_acq_ms per transient, but only one acq_time_ms per transient.",
        ),
        "carrierFreq_MHz": (
            float,
            "acq_params",
            None,
            "carrierfrequency in MHz - usually around 14.89 MHz",
        ),
        "startconstant": (
            float,
            "acq_params",
            None,
            "Fraction of T₁ min bounds to start vdlist at (0.15 recommended).\n(from Weiss, where T₁ determination problem is treated as determining the T₁,\nwhich is known to be between some min and max bounds)",
        ),
        "stopconstant": (
            float,
            "acq_params",
            None,
            "Fraction of max T₁ bounds to stop vdlist at.\n \n Weiss recommends 0.75, which only gives 5% recovery -- we choose 2.0,\n since it gives 73% recovery, and that makes us feel better",
        ),
        "p90_us": (float, "acq_params", None, "90 time of the probe in microseconds.\nUsed to determine 90° 180°, etc pulses"),
        "gamma_eff_MHz_G": (
            float,
            "acq_params",
            0.00425,
            "the ratio of the NMR resonance frequency to the field",
        ),
        "field_width": (
            float,
            "acq_params",
            6,
            "number of points collected in a field sweep, for a finer data acquisition increase this number",
        ),
        "tau_extra_us": (
            float,
            "acq_params",
            1000.0,
            "amount of extra time both before and after the acquisition during a symmetric echo sequence",
        ),
        "concentration": (
            float,
            "sample_params",
            None,
            "concentration of spin label in the sample in M",
        ),
        "FIR_rep":(
                float,
                "odnp_params",
                None,
                "Repetition delay for fast inversion recovery as defined by Weiss-this is calculated in the combined ODNP ppg"
        ),
        "krho_cold": (
            float,
            "sample_params",
            None,
            "the self relaxivity constant of the specific sample with the power off (i.e. when it is coldest)",
        ),
        "krho_hot": (
            float,
            "sample_params",
            None,
            "the self relaxivity constant of the specific sample at the highest temperature/power",
        ),
        "T1water_hot": (
            float,
            "sample_params",
            None,
            "T₁ of ultra pure water at the highest power - this really should not change unless a new measurement is made",
        ),
        "T1water_cold": (
            float,
            "sample_params",
            None,
            "T₁ of ultra pure water with the microwave power off - this really should not change unless a new measurement is made",
        ),
        "repetition_us": (
            float,
            "sample_params",
            None,
            "repetition delay in microseconds",
        ),
        "guessed_MHz_to_GHz": (
            float,
            "sample_params",
            1.51671,
            "the ppt value we use to determine our rf carrier frequency based on our microwave",
        ),
        "max_power": (
            float,
            "odnp_params",
            None,
            "the highest power you plan on acquiring data at - in W",
        ),
        "uw_dip_center_GHz": (
            float,
            "odnp_params",
            None,
            "ESR resonance frequency found by minimizing the B12 dip at increasing powers",
        ),
        "uw_dip_width_GHz": (
            float,
            "odnp_params",
            None,
            "the range over which the dip lock will be performed",
        ),
        "min_dBm_step": (
            float,
            "odnp_params",
            1.0,
            "dBm increment for making the power list in ODNP and for T1(p). Depending on the power source this can be 0.1, 0.5, or 1.0",
        ),
        "guessed_phalf": (
            float,
            "sample_params",
            0.2,
            "estimated power for half saturation"
        ),
        "adc_offset": (int, "acq_params", None, "SpinCore-specific ADC offset correction\nwe believe this is a DC offset, but are not positive"),
        "nScans": (int, "acq_params", 1, "number of scans"),
        "thermal_nScans": (
            int,
            "acq_params",
            1,
            "number of thermal scans - useful for no power datasets with low signal",
        ),
        "nEchoes": (int, "acq_params", None, "number of echoes - 1, aside from CPMG, where it can be any desired number"),
        "IR_steps": (
            int,
            "acq_params",
            None,
            "number of points collected in an IR experiment between the min and max time points",
        ),
        "power_steps": (
            int,
            "odnp_params",
            14,
            "number of points collected in an enhancement experiment",
        ),
        "num_T1s": (
            int,
            "odnp_params",
            None,
            "number of IR experiments collected in the ODNP experiment",
        ),
        # reviewed to here
        "odnp_counter": (
            int,
            "file_names",
            0,
            "number of ODNP experiments that have been performed so far for that particular sample on that day",
        ),
        "echo_counter": (
            int,
            "file_names",
            0,
            "number of echo experiments performed for a particular sample that day- usually incremented when getting on resonance",
        ),
        "generic_echo_counter": (
            int,
            "file_names",
            0,
            "number of echo experiments performed for a particular sample that day- usually incremented when getting on resonance",
        ),
        "cpmg_counter": (
            int,
            "file_names",
            0,
            "number of cpmg experiments performed for a particular sample that day",
        ),
        "IR_counter": (
            int,
            "file_names",
            0,
            "number of inversion recovery experiments performed for a particular sample that day",
        ),
        "field_counter": (
            int,
            "file_names",
            0,
            "number of field sweeps performed for a particular sample that day",
        ),
        "date": (int, "file_names", None, "today's date"),
        "chemical": (
            str,
            "file_names",
            None,
            "name specific to the sample - your data set will be named: date_chemical_type",
        ),
        "type": (str, "file_names", None, "type of experiment being performed"),
    }

    def __init__(self, filename):
        self.filename = filename
        self.configobj = configparser.ConfigParser()
        self.configobj.read(self.filename)
        self._params = {}
        for j in ["acq_params", "odnp_params", "file_names"]:
            if j not in self.configobj.sections():
                self.configobj.add_section(j)
        for (
            paramname,
            (converter, section, default, _),
        ) in self.registered_params.items():
            try:
                temp = self.configobj.get(section, paramname.lower())
            except:
                continue
            self._params[paramname] = converter(temp)
        self._case_insensitive_keys = {
            j.lower(): j for j in self.registered_params.keys()
        }

    def __getitem__(self, key):
        key = self._case_insensitive_keys[key.lower()]
        if key not in self._params.keys():
            converter, section, default, _ = self.registered_params[key]
            if default is None:
                raise KeyError(
                    f"You're asking for the '{key}' parameter, and it's not set in the .ini file!\nFirst, ask yourself if you should have run some type of set-up program (tuning, adc offset, resonance finder, etc.) that would set this parameter.\nThen, try setting the parameter in the appropriate section of your .ini file by editing the file with gvim or notepad++!"
                )
            else:
                return default
        return self._params[key]

    def __setitem__(self, key, value):
        if key.lower() not in self._case_insensitive_keys.keys():
            raise ValueError(
                f"I don't know what section to put the {key} setting in, or what type it's supposed to be!!  You should register it's existence in the config_parser_fn subpackage before trying to use it!! (Also -- do you really need another setting??)"
            )
        else:
            key = self._case_insensitive_keys[key.lower()]
            converter, section, default, _ = self.registered_params[key]
            self._params[key] = converter(value)  # check that it's the right type
            self.configobj.set(section, key.lower(), str(self._params[key]))
    def __str__(self):
        retval = ['-'*50]
        allkeys = [j for j in self._params.keys()]
        idx = sorted(range(len(allkeys)), key=lambda x: allkeys.__getitem__(x).lower())
        allkeys_sorted = [allkeys[j] for j in idx]
        for key in allkeys_sorted:
            converter, section, default, description = self.registered_params[key]
            description = description.split('\n')
            description = ['\t'+j for j in description]
            description = '\n'.join(description)
            value = self.__getitem__(key)
            retval.append(f"{key} {value} (in [{section}])\n{description}")
        retval.append('-'*50)
        return '\n'.join(retval)

    def keys(self):
        return self._params.keys()

    def write(self):
        for (
            paramname,
            (converter, section, default, _),
        ) in self.registered_params.items():
            if paramname in self._params.keys():
                self.configobj.set(
                    section, paramname.lower(), str(self._params[paramname])
                )
            self.configobj.write(open(self.filename, "w"))

    def asdict(self):
        return self._params
