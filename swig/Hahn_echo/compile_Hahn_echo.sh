#!/usr/bin/bash
swig -python -o Hahn_echo_wrap.c Hahn_echo.i 
# need defined in .bashrc
# export conda_headers='C:\ProgramData\Anaconda2\include'
# export conda_libs='C:\ProgramData\Anaconda2\libs'
if [ -z "$conda_headers" ]; then
    echo "conda_headers isn't defined -- see comments here and define in .bashrc"
    exit
fi
if [ -z "$conda_libs" ]; then
    echo "conda_libs isn't defined -- see comments here and define in .bashrc"
    exit
fi
gcc -shared -DMS_WIN64 -I$conda_headers -I$spincore -I$numpy -L$conda_libs -L$spincore Hahn_echo.c Hahn_echo_wrap.c -lpython27 -lmrispinapi64 -o _Hahn_echo.pyd
