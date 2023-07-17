This repo gives examples of how we can interface with SpinCore to produce practical experiments to collect data for inversion recovery, ODNP, Hahn echoes, CPMG and more. The basic format of the scripts relies on 3 basic ppgs in SpinCore_pp: a standard echo, inversion recovery, and a generic ppg that allows the user to create a ppg of their own. All scripts utilize a central configuration file called active.ini. This script carries all the information any of the experiments will require! The configuration file contains parameters such as the dwell time, spectral width, power steps in dB, maximum set power, and repetition delays. So, when one goes to run an experiment, all that's needed is the configuration file and the example script to run the desired experiment. We supply several examples on how to apply these scripts.

.. toctree::

    auto_examples/index

