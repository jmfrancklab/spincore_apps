.. Spincore_applications documentation master file, created by
   sphinx-quickstart on Wed Jul 12 09:02:06 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Spincore_applications's documentation!
=================================================

.. toctree::
   :maxdepth: 1

   intro

This is the documentation for a set of programs to run various experiments such as Inversion recover, ODNP, and CPMG based on the `pyspecdata <https://jmfrancklab.github.io/pyspecdata>`_ module.

The programs are made to utilize a global configuration file that contains all necessary parameters for a given experiment such as the repetition delay, the dwell time, spectral width, the 90 time of the probe, even deblanking times and deadtimes, and much more. 

The generic pulse program works by taking a list of tuples as an argument (along with the other parameters you can specify by implementing the configuration file. These tuples include but are not limited to the pulses, markers, delay times, and deblanking times. 

Phase cycling is an important part of our labs data acquisition and so of course, we have this implemented for pulse programming! The pulses mentioned inside the tuple for pulse programming easily automates phase cycling by making a phase cycle label (e.g., 'ph1','ph2') as a str followed by an array that contains the indices (i.e., registers) of the phases you want to use. These indices are specified in the numpy array 'tx_phases'. Our example for 'run_CPMG_mw.py' gives an excellent example of how you can adjust the phase cycling.

Since ODNP is a central experiment to our lab we have the general outline of tuning our probe in the cavity using gds_for_tune.py which pulls the desired NMR frequency we wish to tune to from the configuration file. This is then followed by running a Hahn echo that calculates the proper field using the gamma_eff_mhz_g parameter in the configuration file. By adjusting this parameter we stay at the NMR frequency we tuned to but the field is shifted to get the signal on resonance. We then find the ESR frequency (GHz) of the hyperfine by running a general field sweep at a set power using 'run_field_dep_just_mw.py'. We find our desired frequency, retune and then run the one 'combined_ODNP.py' script that automates a log to collect powers at all times, runs a progressive saturation, and collects a specified number of IR at evenly spaced powers (all pulled from the configuration file). In total this ODNP experiment takes about an hour using these scripts.
To **jump into examples**, click
:ref:`here <sphx_glr_auto_examples>`.

To understand the structure of the experiments and code,
start on the :doc:`intro <./intro>` page, or browse the documentation to the left.
