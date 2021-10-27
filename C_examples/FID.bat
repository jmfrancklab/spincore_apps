@echo off

SET outputFilename=FID

REM ======================
REM Acquisition Parameters
REM ======================
SET nPoints=16384
SET nScans=1
SET nPhases=1
SET spectrometerFrequency_MHz=11.82
SET spectralWidth_kHz=500.0

SET linebroadening_value=0.0

REM ================
REM Gradient Enables
REM ================
SET slice_en=0
SET phase_en=0
SET readout_en=0

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
SET phaseTime_us=0.0
SET gradientEchoDelay_us=0.0
SET repetitionDelay_s=0.5

SET tx_phase=0.0

SET blankingBit=0

SET adcOffset=74



GradientEcho %nPoints% %nScans% %nPhases% %spectrometerFrequency_MHz% %spectralWidth_kHz% %pulseTime_us% %transTime_us% %phaseTime_us% %repetitionDelay_s% %tx_phase% %amplitude% %blankingBit% %blankingDelay_ms% %adcOffset% %outputFilename% %gradientEchoDelay_us% %linebroadening_value% %RF_Shape% %slice_en% %phase_en% %readout_en%


pause