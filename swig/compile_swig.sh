# run from directory containing your scripts to compile
# $ ./../compile_swig.sh
echo "about to compile..."
winpty ./../swig.exe -python -o Hahn_echo_wrap.c Hahn_echo.i
gcc -shared -DMS_WIN64 -I'C:\ProgramData\Anaconda2\include' -I'C:\apps-su\spincore_apps' -L'C:\ProgramData\Anaconda2\libs' Hahn_echo.c Hahn_echo_wrap.c -lpython27 -o _Hahn_echo.pyd
echo "compiled, about to test..."
python -c 'import Hahn_echo;print Hahn_echo.get_time()'
