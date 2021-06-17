@echo off

SET outputFilename=2D_MRI

REM ======================
REM Acquisition Parameters
REM ======================
SET nPoints=128
SET nScans=1
SET nPhases=128
SET spectrometerFrequency_MHz=11.82
SET spectralWidth_kHz=64.0

SET linebroadening_value=0.0

REM ================
REM Gradient Enables
REM ================
SET slice_en=0
SET phase_en=1
SET readout_en=1

REM ===================
REM RF Pulse Parameters
REM ===================
SET RF_Shape=0
SET amplitude=1.0
SET pulseTime_us=3.0

REM ======
REM Delays
REM ======
SET blankingDelay_ms=3.0
SET transTime_us=120.0
SET phaseTime_us=1000.0
SET gradientEchoDelay_us=100.0
SET repetitionDelay_s=0.25

SET tx_phase=0.0

SET blankingBit=0

SET adcOffset=74

COPY 2D_MRI.bat %outputFilename%_params.txt

GradientEcho %nPoints% %nScans% %nPhases% %spectrometerFrequency_MHz% %spectralWidth_kHz% %pulseTime_us% %transTime_us% %phaseTime_us% %repetitionDelay_s% %tx_phase% %amplitude% %blankingBit% %blankingDelay_ms% %adcOffset% %outputFilename% %gradientEchoDelay_us% %linebroadening_value% %RF_Shape% %slice_en% %phase_en% %readout_en%

pause