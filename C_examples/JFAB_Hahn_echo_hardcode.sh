#!/usr/bin/bash
gcc JFAB_Hahn_echo_hardcode.c mrispinapi64.lib -ggdb -o JFAB_Hahn_echo_hardcode
echo "done compiling, about to run"
gdb JFAB_Hahn_echo_hardcode
