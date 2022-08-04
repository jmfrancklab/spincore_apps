#!/usr/bin/bash
echo "about to compile"
gcc -c Spincore_pp/Spincore_pp.c mrispinapi64.lib -o Spincore_pp.o
gcc adc_offset.c Spincore_pp.o mrispinapi64.lib -o adc_offset
echo "compiled"
