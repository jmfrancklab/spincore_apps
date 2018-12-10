#!/usr/bin/bash
echo "about to construct wrapper..."
swig -python -o ppg_lang_wrap.c ppg_lang.i
echo "wrapper constructed."
echo "about to compile module..."
gcc -shared -DMS_WIN64 -I$conda_headers -I$spincore -I$numpy -L$conda_libs -L$spincore ppg_lang.c ppg_lang_wrap.c -lpython27 -lmrispinapi64 -o _ppg_lang.pyd
echo "module compiled."
