.. Spincore_applications documentation master file, created by
   sphinx-quickstart on Wed Jul 12 09:02:06 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Spincore_applications's documentation!
+++++++++++++++++++++++++++++++++++++++++++++++++

.. toctree::
   :maxdepth: 1

   intro

This is the documentation for a set of programs to run various experiments such as Inversion recover, ODNP, and CPMG based on the `pyspecdata <https://jmfrancklab.github.io/pyspecdata>`_ module and the SpinCore RadioProcessor-G transceiver board.

The configuration file - "config file"
--------------------------------------
The configuration file (called "active.ini" in our examples directory) is central to all pulse programming presented here. In this file all parameters needed for an experiment (aside from the actual pulse program) are included. For example, the repetition delay, spectral width, dwell times, the desired maximum power, and number of scans. A parser then uses this configuration file to communicate the settings to the pulse program experiment. 

The pulse programs and phase cycling
------------------------------------
Phase cycling is an important part of our labs data acquisition and so of course, we have phase cycling can be implemented and automated for pulse programming! In order to automate phase cycling in the pule sequence, provide both a phase cycle label (e.g., 'ph1', or 'ph2') as a str and an array containing the indices (i.e. registers) of the phases you wish to use that are specified in the numpy array 'tx_phases'.Note that specifying the same phase cycle label will loop the corresponding phase steps together, regardless of whether the indices are the same or not.
e.g.,
The following::
    ('pulse',2.0,'ph1',r_[0,1]),
    ('delay',1.5),
    ('pulse',2.0,'ph1',r_[2,3])

will provide two transients with phases of the two pulses (p1,p2):
    (0,2)
    (1,3)
whereas the following::
    ('pulse',2.0,'ph1',r_[0,1]),
    ('delay',1.5),
    ('pulse',2.0,'ph2',r_[2,3])

will provide four transients with phases of the two pulses (p1,p2):
    (0,2)
    (0.3)
    (1,2)
    (1,3)
The total number of transients that will be collected are determined by both nScans (from your configuration file) and the number of steps calculated in the phase cycle as shown above. Thus for nScans = 1, the SpinCore will trigger 2 times in the first case and 4 times in the second case. For nScans = 2, the SpinCore will trigger 4 times in the first case and 8 times in the second case.

There are four ppg options available: a standard echo, an inversion recovery, a typical CPMG echo train and a generic option that allows the user to create their own. All ppg functions take parameters drawn from the configuration file, including number of scans, spectral width, acquisition time, delays etc. The generic option takes an extra kwarg as a list of tuples which describes the element types of the desired experiment (e.g., pulses, markers, delays, etc.). 
For example a DQF COSY would call the function like this::
    COSY_DQF_data = generic(ppg_list = [('marker','start',1),
                                ('phase_reset',1),
                                ('delay_TTL',config_dict['deblank_us']),
                                ('pulse_TTL',config_dict['p90_us'],'ph1',r_[0,1,2,3]),
                                ('delay',t1),
                                ('delay_TTL',config_dict['deblank_us']),
                                ('pulse_TTL',config_dict['p90_us'],0),
                                ('delay',delta),
                                ('delay_TTL',config_dict['deblank_us']),
                                ('pulse_TTL',config_dict'p90_us'],'ph3',r_[0,1,2,3]),
                                ('delay',config_dict['deadtime_us']),
                                ('acquire',config_dict['acq_time_ms']),
                                ('delay',config_dict['repetition_us']),
                                ('jumpto','start')
                                ],
                            nScans = config_dict['nScans'],
                            indirect_idx = 0,
                            indirect_len = len(t1_list),
                            adcOffset = config_dict['adc_offset'],
                            carrierFreq_MHz = config_dict['carrierFreq_MHz'],
                            SW_kHz = config_dict['SW_kHz'],
                            ret_data = None)
                            

Example of how the Franck lab collects ODNP data
------------------------------------------------
#. Tune the NMR probe to the desired RF frequency using ``gds_for_tune.py``
#. Get on NMR resonance with ``run_Hahn_echo.py`` - this is actually pretty neat - because we tuned to a specific NMR carrier frequency (specified in the config file) we don't want to change the carrier frequency to get on resonance - rather we adjust the "gamma_eff_mhz_g" parameter in the configuration file which is then used to shift the *field* instead to get us on resonance. As the name implies this is our ratio of the carrier frequency in MHz to the field in G.
#. We run a field sweep to identify the ratio of resonance frequencies for NMR and ESR using ``run_field_dep_just_mw.py``
#. We then get on resonance to that ratio of the resonant frequency of the cavity again using ``run_Hahn_echo.py``
#. Finally a fully automated ODNP experiment is performed that logs the power output by the microwaves throughout the experiment. It collects the progressive saturation to capture the enhancement as a function of power as well as inversion recovery datasets collected at evenly spaced powers along the power axis used in the progressive saturation. This is all done using ``combined_ODNP.py``.   

To **jump into examples**, click
:ref:`here <sphx_glr_auto_examples>`.

To understand the structure of the experiments and code,
start on the :doc:`intro <./intro>` page, or browse the documentation to the left.
