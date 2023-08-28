The configuration file - "config file"
######################################
The configuration file (called "active.ini" in our examples directory) is added feature to all pulse programming presented here. In the config file all parameters needed for an experiment (aside from the actual pulse program) are included. For example, the repetition delay, spectral width, dwell times, the desired maximum power, and number of scans.

Sections of the Config file
===========================
acq_params
----------
These are acquisition parameters needed for an experiment.

+-------------------+-------+-------------------------------------+---------+
| Name of Parameter | Type  | Description                         | Example |
+===================+=======+=====================================+=========+
| amplitude         | float | amplitude of pulse                  | 1.0     |
+-------------------+-------+-------------------------------------+---------+
| deadtime_us       | float | mandatory delay after the pulse --  | 10.0    |
|                   |       | allows receivers to recover.        |         |
|                   |       | Units = microseconds                |         |
+-------------------+-------+-------------------------------------+---------+
| tau_us            | float | extra delat added between the 90°   | 3500    |
|                   |       | and 180° pulse -- note this is not  |         |
|                   |       | the same as τ_echo!                 |         |
|                   |       | Units = microseconds                |         |
+-------------------+-------+-------------------------------------+---------+
| deblank_us        | float | type between the deblank TTL pulse  | 1.0     |
|                   |       | and the actual pulse itself.        |         |
|                   |       | Units = microseconds                |         |
+-------------------+-------+-------------------------------------+---------+
| SW_kHz            | float | spectral width of data acquisition  | 3.9     |
|                   |       | in kHz.                             |         |
+-------------------+-------+-------------------------------------+---------+
| acq_time_ms       | float | acquisition time in milliseconds.   | 1024.0  |
+-------------------+-------+-------------------------------------+---------+
| carrierFreq_MHz   | float | carrier frequency in MHz            | 14.8948 |
+-------------------+-------+-------------------------------------+---------+
| startconstant     | float | Fraction of T₁ min bounds to start  | 0.2     |
|                   |       | vdlist at (0.15 recommended).       |         |
|                   |       | (from Weiss, where T₁ determination |         |
|                   |       | problem is treated as determining   |         |
|                   |       | the T₁,\nwhich is known to be       |         |
|                   |       | between some min and max bounds)    |         |
+-------------------+-------+-------------------------------------+---------+
| stopconstant      | float | Fraction of max T₁ bounds to stop   | 2.0     |
|                   |       | vdlist at. Weiss recommends 0.75,   |         |
|                   |       | which only gives 5% recovery -- we  |         |
|                   |       | choose 2.0,\n since it gives 73%    |         |
|                   |       | recovery.                           |         | 
+-------------------+-------+-------------------------------------+---------+
| p90_us            | float | 90 time of the probe in microseconds| 4.35    |
|                   |       | Used to determine 90° 180°, etc     |         | 
|                   |       | pulses.                             |         |
+-------------------+-------+-------------------------------------+---------+
| gamma_eff_MHz_G   | float | the ratio of the NMR resonance      | 0.004256|
|                   |       | frequency to the field              |         |
+-------------------+-------+-------------------------------------+---------+
| field width       | float | number of points collected in a     | 10.0    |
|                   |       | field sweep, for a finer data       |         |
|                   |       | acquisition, increase this number   |         |
+-------------------+-------+-------------------------------------+---------+
| tau_extra_us      | float | amount of extra time both before and| 1000.0  |
|                   |       | after the acquisition during a      |         |
|                   |       | symmetric echo sequence             |         |
+-------------------+-------+-------------------------------------+---------+
| adc_offset        | int   | SpinCore-specific ADC offset        | 45      |
|                   |       | correction.                         |         |
+-------------------+-------+-------------------------------------+---------+
| nScans            | int   | number of scans                     | 1       |
+-------------------+-------+-------------------------------------+---------+
| thermal_nScans    | int   | number of scans taken at no power.  | 10      |
|                   |       | useful for no power datasets with   |         |
|                   |       | low signal                          |         |
+-------------------+-------+-------------------------------------+---------+
| nEchoes           | int   | Number of echoes - 1, aside from    | 1       |
|                   |       | CPMG, where it can be any desired   |         |
|                   |       | number                              |         |
+-------------------+-------+-------------------------------------+---------+

sample_params
-------------
This section defines parameters that are specific to the sample being test. For example, the concentration of the sample.

+-------------------+-------+-------------------------------------+---------+
| Name of Parameter | Type  | Description                         | Example |
+===================+=======+=====================================+=========+
| concentration     | float | concentration of spin label in the  | 0.027   |
|                   |       | sample in M                         |         |
+-------------------+-------+-------------------------------------+---------+
| krho_cold         | float | the self relaxivity constant of the | 380     |
|                   |       | specific sample with the power off  |         |
|                   |       | (i.e., when it is coldest)          |         |
+-------------------+-------+-------------------------------------+---------+
| krho_hot          | float | the self relaxivity constant of the | 260     |
|                   |       | specific sample at the highest      |         |
|                   |       | temperature/power.                  |         |
+-------------------+-------+-------------------------------------+---------+
| T1water_cold      | float | T₁ of ultra pure water with the     | 2.17    |
|                   |       | microwave power off - this really   |         |
|                   |       | should not change unless a new      |         |
|                   |       | measurement is made.                |         |
+-------------------+-------+-------------------------------------+---------+
| T1water_hot       | float | T₁ of ultra pure water at the       | 2.98    |
|                   |       | highest power - this really should  |         |
|                   |       | not change unless a new measurement |         |
|                   |       | is made.                            |         |
+-------------------+-------+-------------------------------------+---------+
| repetition_us     | float | repetition delay in microseconds    | 1000000 |
+-------------------+-------+-------------------------------------+---------+
| guessed_MHz_to_GHz| float | the ratio of the NMR resonance      | 1.5167  |
|                   |       | frequency and microwave frequency   |         |
+-------------------+-------+-------------------------------------+---------+
| guessed_phalf     | float | estimated power for half saturation | 0.2     |
+-------------------+-------+-------------------------------------+---------+

ODNP params
-----------
These are parameters specific to the combined ODNP experiment in which a progressive saturation experiment is performed and followed by a series of incremented IR experiments at increasing power.

+-------------------+-------+-------------------------------------+---------+
| Name of Parameter | Type  | Description                         | Example |
+===================+=======+=====================================+=========+
| max_power         | float | The highest power you plan on       | 3.16    |
|                   |       | acquiring data with - in W.         |         |
+-------------------+-------+-------------------------------------+---------+
| uw_dip_center_GHz | float | ESR frequency found by minimizing   | 9.81937 |
|                   |       | the Bridge12 dip at increasing power|         |
+-------------------+-------+-------------------------------------+---------+
| uw_dip_width_GHz  | float | The range over which the dip lock   | 0.02    |
|                   |       | will be performed                   |         |
+-------------------+-------+-------------------------------------+---------+
| min_dBm_step      | float | dBm increment for making the power  | 0.5     |
|                   |       | list in ODNP and for T1(p).         |         |
|                   |       | Depending on the power source this  |         |
|                   |       | can be 0.1,0.5, or 1.0.             |         |
+-------------------+-------+-------------------------------------+---------+
| power_steps       | int   | number of points collected in an    | 14      |
|                   |       | enhancement experiment              |         |
+-------------------+-------+-------------------------------------+---------+
| num_T1s           | int   | number of IR experiments collected  | 6       |
|                   |       | in the ODNP experiment              |         |
+-------------------+-------+-------------------------------------+---------+

File names
----------
These parameters allow you to precisely name the data set

+-------------------+-------+-------------------------------------+------------+
| Name of Parameter | Type  | Description                         | Example    |
+===================+=======+=====================================+============+
| odnp_counter      | int   | Number of ODNP experiments that     | 1          |
|                   |       | have been performed so far for that |            |
|                   |       | particular sample on that day       |            |
+-------------------+-------+-------------------------------------+------------+
| echo_counter      | int   | Number of echo experiments that     | 1          |
|                   |       | have been performed for a particular|            |
|                   |       | sample that day - usually           |            |
|                   |       | incremented when getting on         |            |
|                   |       | resonance                           |            |
+-------------------+-------+-------------------------------------+------------+
| cpmg_counter      | int   | Number of cpmg experiments that     | 1          |
|                   |       | have been performed so fat for that |            |
|                   |       | particular sample on that day       |            |
+-------------------+-------+-------------------------------------+------------+
| IR_counter        | int   | Number of IR experiments that       | 1          |
|                   |       | have been performed so far for that |            |
|                   |       | particular sample on that day       |            |
+-------------------+-------+-------------------------------------+------------+
| field_counter     | int   | Number of field sweeps that         | 1          |
|                   |       | have been performed so far for that |            |
|                   |       | particular sample on that day       |            |
+-------------------+-------+-------------------------------------+------------+
| date              | int   | Today's date in year/month/day      | 230524     |
+-------------------+-------+-------------------------------------+------------+
| chemical          | str   | name specific to the sample - your  | 70mM_TEMPOL|
|                   |       | have been performed so far for that |            |
|                   |       | particular sample on that day       |            |
+-------------------+-------+-------------------------------------+------------+
| type              | str   | type of experiment that was         | echo       |
|                   |       | performed.                          |            |
+-------------------+-------+-------------------------------------+------------+
