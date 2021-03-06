#!/usr/bin/bash
swig -python ppg.i
# define the following in .bashrc (modified for system)
# export conda_headers='C:\ProgramData\Anaconda2\include'
# export conda_libs='C:\ProgramData\Anaconda2\libs\'
if [ -z "$conda_headers" ]; then
    echo "conda_headers isn't defined!! see comments here and define in your .bashrc"
    exit
fi
if [ -z "$conda_libs" ]; then
    echo "conda_libs isn't defined!! see comments here and define in your .bashrc"
    exit
fi
gcc -c -fpic -DMS_WIN64 -I$conda_headers -I$spincore -I$numpy -L$conda_libs -L$spincore ppg.c ppg_wrap.c
gcc -shared -DMS_WIN64 -I$conda_headers -I$spincore -I$numpy -L$conda_libs -L$spincore ppg.o ppg_wrap.o -lpython27 -o _ppg.pyd 
pycode=$(cat <<-END
from numpy import *
import ppg
ppg.load([
    ('marker','start',4),
    ('pulse',10.0,pi/2),
    ('delay',10.0),
    ('marker','cpmg_start',20),
    ('pulse',20.0,-pi/2),
    ('delay',20.0),
    ('jumpto','cpmg_start'),
    ('jumpto','start'),
    ])
END
)
python -c "$pycode"
