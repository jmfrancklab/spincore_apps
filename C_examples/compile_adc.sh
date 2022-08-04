#!/usr/bin/bash
echo "about to compile"
# Spincore_pp_copy.c is a copy of Spincore_pp.c from the other directory, so I can strip out the python-related stuff
gcc -c Spincore_pp_copy.c -o Spincore_pp.o
gcc adc_offset.c Spincore_pp.o ../mrispinapi64.lib -o adc_offset
echo "compiled"
