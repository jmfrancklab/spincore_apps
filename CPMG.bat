
SET outputFilename=181121_CPMG_5_4

REM ==================
REM Acquisition
REM ==================
SET nPoints=128
SET nScans=64
SET nEchoes=128
SET SW_kHz=128.0
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
SET tauDelay_us=3000.0
SET repetitionDelay_s=1.0

SET tx_phase=0.0

SET adcOffset=44

COPY CPMG.bat %outputFilename%_params.txt

REM Specify C program then call variables
CPMG %nPoints% %nScans% %nEchoes% %SW_kHz% %carrierFreq_MHz% %amplitude% %p90Time_us% %transTime_us% %tauDelay_us% %repetitionDelay_s% %tx_phase% %adcOffset% %outputFilename%
