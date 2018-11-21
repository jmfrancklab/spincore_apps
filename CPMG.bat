
SET outputFilename=181121_CPMG_3_2

REM ==================
REM Acquisition
REM ==================
SET nPoints=128
SET nScans=8
SET nEchoes=64
SET SW_kHz=60.0
REM ==================
REM Excitation
REM ==================
SET carrierFreq_MHz=14.46
SET amplitude=1.0
SET p90Time_us=0.78
REM ==================
REM Delays
REM ==================
SET transTime_us=500.0
SET tauDelay_us=2500.0
SET repetitionDelay_s=1.0

SET tx_phase=0.0

SET adcOffset=44

COPY CPMG.bat %outputFilename%_params.txt

REM Specify C program then call variables
CPMG %nPoints% %nScans% %nEchoes% %SW_kHz% %carrierFreq_MHz% %amplitude% %p90Time_us% %transTime_us% %tauDelay_us% %repetitionDelay_s% %tx_phase% %adcOffset% %outputFilename%
