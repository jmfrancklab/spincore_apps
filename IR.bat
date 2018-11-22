
SET outputFilename=181121_IR_1

REM ==================
REM Acquisition
REM ==================
SET nPoints=1024
SET nScans=1
REM You will collect one less than the following
SET nPoints_vd=8
SET SW_kHz=30.0
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
SET varDelay_us=1.0
SET repetitionDelay_s=1.0

SET tx_phase=0.0

SET adcOffset=45
SET vd_step=5.0
SET nEchoes=1

COPY IR.bat %outputFilename%_params.txt

REM Specify C prog executable then call variables
IR %nPoints% %nScans% %nPoints_vd% %SW_kHz% %carrierFreq_MHz% %amplitude% %p90Time_us% %transTime_us% %varDelay_us% %repetitionDelay_s% %tx_phase% %adcOffset% %outputFilename% %vd_step% %nEchoes%
