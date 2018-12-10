#!/usr/bin/bash
echo "about to compile wrapper with swig..."
swig -python -o Hahn_echo_wrap.c Hahn_echo.i 
# need defined in .bashrc
# export conda_headers='C:\ProgramData\Anaconda2\include'
# export conda_libs='C:\ProgramData\Anaconda2\libs'
# export spincore='C:\apps-su\spincore_apps'
# export numpy='C:\ProgramData\Anaconda2\lib\site-packages\numpy\core\include'
if [ -z "$conda_headers" ]; then
    echo "conda_headers environment variable is not defined"
    echo "define in .bashrc"
    exit
fi
if [ -z "$conda_libs" ]; then
    echo "conda_libs environment variable is not defined"
    echo "define in .bashrc"
    exit
fi
if [ -z "$spincore" ]; then
    echo "spincore environment variable is not defined"
    echo "define in .bashrc"
    exit
fi
if [ -z "$numpy" ]; then
    echo "numpy environment variable is not defined"
    echo "define in .bashrc"
    exit
fi
echo "wrapper compiled."
echo "about to compile module..."
gcc -shared -DMS_WIN64 -I$conda_headers -I$spincore -I$numpy -L$conda_libs -L$spincore Hahn_echo.c Hahn_echo_wrap.c -lpython27 -lmrispinapi64 -o _Hahn_echo.pyd
echo "module compiled."
