#!/usr/bin/bash
echo "about to compile..."
swig -python -o Hahn_echo_wrap.c Hahn_echo.i
gcc -shared -DMS_WIN64 -I$conda_headers -I$spincore -I$numpy -L$conda_libs -L$spincore Hahn_echo.c Hahn_echo_wrap.c -lpython27 -lmrispinapi64 -o _Hahn_echo.pyd
echo "compiled."
