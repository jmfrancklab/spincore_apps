@echo off

REM *********************************************************
REM 	CYCLOPS_nmr_example.bat 
REM 	This file is intended as an example of using the CYCLOPS_nmr.exe executable with a batch file.

REM 	SpinCore Technologies, Inc.
REM 	2010/07/01 12:56:00
REM *********************************************************


FOR /F "TOKENS=1* DELIMS= " %%A IN ('DATE/T') DO SET CDATE=%%B
FOR /F "TOKENS=1,2 eol=/ DELIMS=/ " %%A IN ('DATE/T') DO SET mm=%%B
FOR /F "TOKENS=1,2 DELIMS=/ eol=/" %%A IN ('echo %CDATE%') DO SET dd=%%B
FOR /F "TOKENS=2,3 DELIMS=/ " %%A IN ('echo %CDATE%') DO SET yyyy=%%B
SET date=%yyyy%%mm%%dd% 

TITLE SpinCore Radioprocessor Example SpinNMR Batch File

REM ------------------------------------BOARD SETTINGS------------------------------------

REM BOARD_NUMBER is the number of the board in your system to be used by spinnmr. If you have multiple boards attached to your system, please make sure this value is correct.
SET BOARD_NUMBER=0

REM ADC_FREQUENCY (MHz) is the analog to digital converter frequency of the RadioProcessor board selected.
SET ADC_FREQUENCY=75.0

REM If ENABLE_TX is set to 0, the transmitter is disabled. If it is set to 1, the transmitter is enabled.
SET ENABLE_TX=1

REM If ENABLE_RX is set to 0, the receiver is disabled. If it is set to 1, the receiver is enabled.
SET ENABLE_RX=1

REM REPETITION_DELAY (s)  is the time between each consecutive scan. It must be greater than 0.
SET REPETITION_DELAY=1.0

REM NUMBER_OF_SCANS is the number of consecutive scans to run. There must be atleast one scan.
SET NUMBER_OF_SCANS=16

REM NUMBER_POINTS is the number of NMR data points the board will acquire during the scan. It must be between 0 and 16384.
SET NUMBER_POINTS=16384

REM SPECTROMETER_FREQUENCY (MHz) must be between 0 and 100.
SET SPECTROMETER_FREQUENCY=10.8

REM SPECTRAL_WIDTH (kHz) must be between 0.150 and 10000
SET SPECTRAL_WIDTH=500

REM PULSE_TIME (microseconds) must be atleast 0.065.
SET PULSE_TIME=14.0

REM TRANS_TIME (microseconds) must be atleast 0.065.
SET TRANS_TIME=130

REM TX_PHASE (degrees) must be greater than or equal to zero.
REM this is the initial Tx Phase, successive scans will be offset by 90 degrees from the previous scan.
SET TX_PHASE=0

REM AMPLITUDE of the excitation signal. Must be between 0.0 and 1.0.
SET AMPLITUDE=1.0

REM SHAPED_PULSE will control the shaped pulse feature of the RadioProcessor. Setting SHAPED_PULSE to 1 will enable this feature. 0 will disabled this feature.
SET SHAPED_PULSE=0

REM BYPASS_FIR will disabled the FIR filter if set to 1. Setting BYPASS_FIR to 0 will enable the FIR filter.
SET BYPASSFIR=1

REM FNAME is the name of the output file the data will be acquired data will be stored in. File extensions will be appended automatically.
SET FNAME=cycnmr

REM DEBUG enables DEBUGGING output log.
SET DEBUG=0

REM
SET REAL_ADD_SUB_0=1
SET IMAG_ADD_SUB_0=1
SET SWAP_0=0

REM
SET REAL_ADD_SUB_1=1
SET IMAG_ADD_SUB_1=0
SET SWAP_1=1

REM
SET REAL_ADD_SUB_2=0
SET IMAG_ADD_SUB_2=0
SET SWAP_2=0

REM
SET REAL_ADD_SUB_3=0
SET IMAG_ADD_SUB_3=1
SET SWAP_3=1

REM If verbose mode is disabled, the program will output nothing.
SET VERBOSE=1

REM Use TTL Blanking
SET BLANKING_EN=1

REM BLANKING_BIT specifies which TTL Flag to use for the power amplifier blanking signal.
REM Refer to your products Owner's Manual for additional information
SET BLANKING_BITS=2

REM TTL Blanking Delay (in milliseconds)
SET BLANKING_DELAY=5.00

REM ------------------------------------END BOARD SETTINGS---------------------------------

ECHO Executing CYCLOPS spinnmr....

CYCLOPS_nmr %BOARD_NUMBER% %NUMBER_POINTS% %SPECTROMETER_FREQUENCY% %SPECTRAL_WIDTH% %PULSE_TIME% %TRANS_TIME% %REPETITION_DELAY% %NUMBER_OF_SCANS% %TX_PHASE% %FNAME% %BYPASSFIR% %ADC_FREQUENCY% %SHAPED_PULSE% %AMPLITUDE% %ENABLE_TX% %ENABLE_RX% %VERBOSE% %BLANKING_EN% %BLANKING_BITS% %BLANKING_DELAY% %REAL_ADD_SUB_0% %IMAG_ADD_SUB_0% %SWAP_0% %REAL_ADD_SUB_1% %IMAG_ADD_SUB_1% %SWAP_1% %REAL_ADD_SUB_2% %IMAG_ADD_SUB_2% %SWAP_2% %REAL_ADD_SUB_3% %IMAG_ADD_SUB_3% %SWAP_3% %DEBUG%
pause


