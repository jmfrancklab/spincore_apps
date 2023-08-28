Example of how the Franck lab collects ODNP data
------------------------------------------------
#. Tune the NMR probe to the desired RF frequency using ``gds_for_tune.py``
#. Get on NMR resonance with ``run_Hahn_echo.py`` - this is actually pretty neat - because we tuned to a specific NMR carrier frequency (specified in the config file) we don't want to change the carrier frequency to get on resonance - rather we adjust the "gamma_eff_mhz_g" parameter in the configuration file which is then used to shift the *field* instead to get us on resonance. As the name implies this is our ratio of the carrier frequency in MHz to the field in G.
#. We run a field sweep to identify the ratio of resonance frequencies for NMR and ESR using ``run_field_dep_just_mw.py``
#. We then get on resonance to that ratio of the resonant frequency of the cavity again using ``run_Hahn_echo.py``
#. Finally a fully automated ODNP experiment is performed that logs the power output by the microwaves throughout the experiment. It collects the progressive saturation to capture the enhancement as a function of power as well as inversion recovery datasets collected at evenly spaced powers along the power axis used in the progressive saturation. This is all done using ``combined_ODNP.py``.   

