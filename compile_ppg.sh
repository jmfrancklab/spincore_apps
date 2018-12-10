#!/usr/bin/bash
swig -python ppg.i
conda_headers='C:\ProgramData\Anaconda2\include'
conda_libs='C:\ProgramData\Anaconda2\libs\'
gcc -c -fpic -DMS_WIN64 -I$conda_headers -L$conda_libs ppg.c ppg_wrap.c
gcc -shared -DMS_WIN64 -I$conda_headers -L$conda_libs ppg.o ppg_wrap.o -lpython27 -o _ppg.pyd 
pycode=$(cat <<-END
import ppg
ppg.ppg_element('pulse',1.0,2.0)
ppg.ppg_element('delay',10.0)
ppg.load([('pulse',10.0,20.0)])
END
)
python -c "$pycode"
