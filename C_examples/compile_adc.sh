#!/usr/bin/bash
echo "about to compile"
gcc adc_offset.c mrispinapi64.lib -o adc_offset
echo "compiled"
