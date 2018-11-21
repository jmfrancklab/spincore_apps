
SET outputFilename=181120_test

REM ==================
REM Acquisition
REM ==================
SET nPoints=256
SET nScans=4
REM You will collect one less than the following
SET nPoints_Nutation=5
SET SW_kHz=50
REM ==================
REM Excitation
REM ==================
SET carrierFreq_MHz=14.46
SET amplitude=1.0
SET p90Time_us=0.065
REM ==================
REM Delays
REM ==================
SET transTime_us=1000000.0
SET tauDelay_us=4000000.0
SET repetitionDelay_s=1.0

SET tx_phase=0.0

SET adcOffset=42
SET nutation_step=0.159

COPY nutation.bat %outputFilename%_params.txt

REM Specify C program then call variables
RPG_nutation %nPoints% %nScans% %nPoints_Nutation% %SW_kHz% %carrierFreq_MHz% %amplitude% %p90Time_us% %transTime_us% %tauDelay_us% %repetitionDelay_s% %tx_phase% %adcOffset% %outputFilename% %nutation_step%
