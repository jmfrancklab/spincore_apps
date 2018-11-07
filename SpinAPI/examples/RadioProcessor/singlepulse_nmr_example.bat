@echo off

REM *********************************************************
REM 	singlepulse_nmr_example.bat 
REM 	This file is intended as an example of using the singlepulse_nmr.exe executable with a batch file.

REM 	SpinCore Technologies, Inc.
REM 	2017/07/07 11:00:00
REM *********************************************************


FOR /F "TOKENS=1* DELIMS= " %%A IN ('DATE/T') DO SET CDATE=%%B
FOR /F "TOKENS=1,2 eol=/ DELIMS=/ " %%A IN ('DATE/T') DO SET mm=%%B
FOR /F "TOKENS=1,2 DELIMS=/ eol=/" %%A IN ('echo %CDATE%') DO SET dd=%%B
FOR /F "TOKENS=2,3 DELIMS=/ " %%A IN ('echo %CDATE%') DO SET yyyy=%%B
SET date=%yyyy%%mm%%dd% 

TITLE SpinCore RadioProcessor Singlepulse NMR Example

REM ------------------------------------BOARD SETTINGS------------------------------------


REM FILE_NAME is the name of the output file the data will be acquired data will be stored in. File extensions will be appended automatically.
SET FILE_NAME=spnmr



REM Board Parameters

REM BOARD_NUMBER is the number of the board in your system to be used by spinnmr. If you have multiple boards attached to your system, please make sure this value is correct.
SET BOARD_NUMBER=0

REM BLANK_BIT specifies which TTL Flag to use for the power amplifier blanking signal.
REM Refer to your products Owner's Manual for additional information
SET BLANK_BIT=2

REM DEBUG Enables the debug output log.
SET DEBUG=0



REM Frequency Parameters

REM ADC_FREQUENCY (MHz) is the analog to digital converter frequency of the RadioProcessor board selected.
SET ADC_FREQUENCY=75.0

REM SPECTROMETER_FREQUENCY (MHz) must be between 0 and 100.
SET SPECTROMETER_FREQUENCY=22.428

REM SPECTRAL_WIDTH (kHz) must be between 0.150 and 10000
SET SPECTRAL_WIDTH=200



REM Pulse Parameters

REM If ENABLE_TX is set to 0, the transmitter is disabled. If it is set to 1, the transmitter is enabled.
SET ENABLE_TX=1

REM USE_SHAPE will control the shaped pulse feature of the RadioProcessor. Setting SHAPED_PULSE to 1 will enable this feature. 0 will disabled this feature.
SET USE_SHAPE=0

REM AMPLITUDE of the excitation signal. Must be between 0.0 and 1.0.
SET AMPLITUDE=1.0

REM PULSE90_TIME (microseconds) must be atleast 0.065.
SET PULSE90_TIME=2

REM PULSE_PHASE (degrees) must be greater than or equal to zero.
SET PULSE90_PHASE=0



REM Acquisition Parameters

REM If ENABLE_RX is set to 0, the receiver is disabled. If it is set to 1, the receiver is enabled.
SET ENABLE_RX=1

REM BYPASS_FIR will disabled the FIR filter if set to 1. Setting BYPASS_FIR to 0 will enable the FIR filter.
SET BYPASS_FIR=1

REM NUMBER_POINTS is the number of NMR data points the board will acquire during the scan. It must be between 0 and 16384. If it is not a power of 2, it will be rounded up to the nearest power of 2.
SET NUMBER_POINTS=1024

REM NUMBER_OF_SCANS is the number of consecutive scans to run. There must be at least one scan. Due to latencies, scan count may not be consecutive.
SET NUMBER_OF_SCANS=2



REM Delay Parameters

REM TTL Blanking Delay (in milliseconds) must be atleast 0.000065.
SET BLANKING_DELAY=3.00

REM TRANS_DELAY (microseconds) must be atleast 0.065.
SET TRANS_DELAY=150

REM REPETITION_DELAY (s)  is the time between each consecutive scan. It must be greater than 0.
SET REPETITION_DELAY=1.0



REM ------------------------------------END BOARD SETTINGS---------------------------------

singlepulse_nmr %FILE_NAME% %BOARD_NUMBER% %BLANK_BIT% %DEBUG% %ADC_FREQUENCY% %SPECTROMETER_FREQUENCY% %SPECTRAL_WIDTH% %ENABLE_TX% %USE_SHAPE% %AMPLITUDE% %PULSE90_TIME% %PULSE90_PHASE% %ENABLE_RX% %BYPASS_FIR% %NUMBER_POINTS% %NUMBER_OF_SCANS% %BLANKING_DELAY% %TRANS_DELAY% %REPETITION_DELAY%
PAUSE


