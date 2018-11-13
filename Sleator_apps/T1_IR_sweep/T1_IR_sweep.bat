@echo off

REM *********************************************************
REM     T1_IR_sweep.bat
REM     This file is used to run the program T1_IR_sweep.exe.
REM     Derived from program 'Hahn_echo_sweep'
REM 	Details about the specific echo parameters are described below. 
REM
REM     Tycho Sleator
REM     2013/11/26 11:36:00
REM *********************************************************

REM FILENAME is the name of the output file the data will be acquired data will be stored in. File extensions will be appended automatically.
set FILENAME=T1_sweep

REM SPECTROMETER_FREQUENCY (MHz) must be between 0 and 100.
set SPECTROMETER_FREQUENCY=21.2008

REM SPECTRAL_WIDTH (kHz) must be between 0.150 and 10000.  Equals the number of points acquired per millisecond.
set SPECTRAL_WIDTH=100

REM P1_TIME (microseconds): 180 degree pulse time (must be at least 0.065). 
set P1_TIME=8.4

REM P2_TIME (microseconds): 90 degree pulse time (must be at least 0.065). 
set P2_TIME=4.2

REM RINGDOWN_TIME (microseconds) (must be atleast 0.065).
set RINGDOWN_TIME=50

REM P1_PHASE (degrees): Output (Tx) phase of 180 degree pulse.  
set P1_PHASE=15.0

REM P2_PHASE (degrees): Output (Tx) phase of 90 degree pulse.
set P2_PHASE=15.0

REM FID_TIME (microseconds): Time used to record FID after second (90 degree) pulse.  Should be longer then the decay time of the FID.
set FID_TIME=10000

REM TAU_MIN (microseconds): Minimum value of tau. Must be at least 0.065.  
set TAU_MIN=10000

REM DELTA_TAU (microseconds): Increment in tau.
set DELTA_TAU=10000

REM N_TAU (must be integer > 0): Number of values of TAU.  Tau_i = Tau_min + i*DELTA_TAU for i = 0 to N_TAU-1 
set N_TAU=20

REM NUMBER_OF_SCANS must be greater than or equal to 1.  Multiple scans are averaged.
set NUMBER_OF_SCANS=4

REM REPETITION_DELAY (s) is the time between each consecutive scan. It must be greater than 0.065.
SET REPETITION_DELAY=1.0

REM AMPLITUDE is the (non-linear) output scaling factor for the transmitter output.  Must be between 0.0 and 1.0.
SET AMPLITUDE=0.2

REM BLANKING_DELAY (ms) is the time before the excitation pulse necessary to blank the power amplifier. 3.0ms is a good number for the 10W PA.
SET BLANKING_DELAY=3.0

REM BYPASS_FIR will disable the FIR filter if set to 1. Setting BYPASS_FIR to 0 will enable the FIR filter.
set BYPASS_FIR=1

REM ADC_FREQUENCY (MHz) is the analog to digital converter frequency of the RadioProcessor board selected.
SET ADC_FREQUENCY=75.0

REM BLANKING_BIT is the number of the TTL bit to use for the power amplifier blanking signal.
SET BLANKING_BIT=2

REM DEBUG Enables the debug output log.
SET DEBUG=0

REM BOARD_NUMBER is the number of the board in your system to be used by CPMG. If you have multiple boards attached to your system, please make sure this value is correct.
SET BOARD_NUMBER=0

T1_IR_sweep %FILENAME% %SPECTROMETER_FREQUENCY% %SPECTRAL_WIDTH% %P1_TIME% %P2_TIME% %RINGDOWN_TIME% %P1_PHASE% %P2_PHASE% %FID_TIME% %TAU_MIN% %DELTA_TAU% %N_TAU% %NUMBER_OF_SCANS% %REPETITION_DELAY% %AMPLITUDE% %BLANKING_DELAY% %BYPASS_FIR% %ADC_FREQUENCY% %BLANKING_BIT% %DEBUG% %BOARD_NUMBER% 
pause
