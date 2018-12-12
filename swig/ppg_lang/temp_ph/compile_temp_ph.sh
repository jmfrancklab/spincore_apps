#!/usr/bin/bash
echo "about to construct wrapper..."
swig -python -o ppg_temp_ph_wrap.c ppg_temp_ph.i
echo "wrapper constructed."
echo "about to compile module..."
gcc -shared -DMS_WIN64 -I$conda_headers -I$spincore -I$numpy -L$conda_libs -L$spincore ppg_temp_ph.c ppg_temp_ph_wrap.c -lpython27 -lmrispinapi64 -o _ppg_temp_ph.pyd
echo "module compiled."
