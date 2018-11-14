
SET outputFilename=181113_test

REM ==================
REM Acquisition
REM ==================
SET nPoints=4096
SET nScans=2
SET nEchoes=5
SET SW_kHz=200.0
REM ==================
REM Excitation
REM ==================
SET carrierFreq_MHz=14.46
SET amplitude=1.0
SET p90Time_us=1.0
REM ==================
REM Delays
REM ==================
SET transTime_us=500.0
SET tauDelay_us=1000000.0
SET repetitionDelay_s=1.0

SET tx_phase=0.0

SET adcOffset=47

COPY CPMG.bat %outputFilename%_params.txt

REM Specify C program then call variables
CPMG %nPoints% %nScans% %nEchoes% %SW_kHz% %carrierFreq_MHz% %amplitude% %p90Time_us% %transTime_us% %tauDelay_us% %repetitionDelay_s% %tx_phase% %adcOffset% %outputFilename%
