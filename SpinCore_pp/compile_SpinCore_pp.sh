#!/usr/bin/bash
echo "about to construct wrapper..."
swig -python -threads -o SpinCore_pp_wrap.c SpinCore_pp.i
echo "wrapper constructed."
echo "about to compile module..."
gcc -shared -DMS_WIN64 -I$conda_headers -I$spincore -I$numpy -L$conda_libs -L$spincore SpinCore_pp.c SpinCore_pp_wrap.c -lpython27 -lmrispinapi64 -o _SpinCore_pp.pyd
echo "module compiled."
