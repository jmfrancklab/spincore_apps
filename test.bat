
SET outputFilename=181110_noise_1

REM ==================
REM Acquisition
REM ==================
SET nPoints=16384
SET nScans=1
SET nPhases=1
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
SET transTime_us=90.0
SET tauDelay_us=150.0
SET repetitionDelay_s=1.0

SET tx_phase=0.0

SET adcOffset=46

COPY test.bat %outputFilename%_params.txt

REM Specify C program then call variables
RPG_noise %nPoints% %nScans% %nPhases% %SW_kHz% %carrierFreq_MHz% %amplitude% %p90Time_us% %transTime_us% %tauDelay_us% %repetitionDelay_s% %tx_phase% %adcOffset% %outputFilename%
