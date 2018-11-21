
SET outputFilename=181121_nutation_10_2scans

REM ==================
REM Acquisition
REM ==================
SET nPoints=256
SET nScans=2
REM You will collect one less than the following
SET nPoints_Nutation=64
SET SW_kHz=30.0
REM ==================
REM Excitation
REM ==================
SET carrierFreq_MHz=14.46
SET amplitude=1.0
SET p90Time_us=0.065
REM ==================
REM Delays
REM ==================
SET transTime_us=500.0
SET tauDelay_us=2500.0
SET repetitionDelay_s=1.0

SET tx_phase=0.0

SET adcOffset=44
SET nutation_step=1.0

COPY nutation.bat %outputFilename%_params.txt

REM Specify C prog executable then call variables
nutation %nPoints% %nScans% %nPoints_Nutation% %SW_kHz% %carrierFreq_MHz% %amplitude% %p90Time_us% %transTime_us% %tauDelay_us% %repetitionDelay_s% %tx_phase% %adcOffset% %outputFilename% %nutation_step%
