#!/usr/bin/bash
echo "about to construct wrapper..."
swig -python -o Hahn_echo_ph_wrap.c Hahn_echo_ph.i
echo "wrapper constructed."
echo "about to compile module..."
gcc -shared -DMS_WIN64 -I$conda_headers -I$spincore -I$numpy -L$conda_libs -L$spincore Hahn_echo_ph.c Hahn_echo_ph_wrap.c -lpython27 -lmrispinapi64 -o _Hahn_echo_ph.pyd
echo "module compiled."
