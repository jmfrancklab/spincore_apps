@echo off
echo This program will uninstall drivers for SpinCore PCI products from your computer.

cd %~dp0 

REM Check operating system
ver | find /i "10.0" > nul
if %ERRORLEVEL% == 0 goto ver_10

ver | find /i "6.3" > nul
if %ERRORLEVEL% == 0 goto ver_81

ver | find /i "6.2" > nul
if %ERRORLEVEL% == 0 goto ver_8

ver | find /i "6.1" > nul
if %ERRORLEVEL% == 0 goto ver_7

ver | find /i "6.0" > nul
if %ERRORLEVEL% == 0 goto ver_vista

ver | find /i "5.2" > nul
if %ERRORLEVEL% == 0 goto ver_2003

ver | find /i "5.1" > nul
if %ERRORLEVEL% == 0 goto ver_xp

ver | find /i "Windows 2000" > nul
if %ERRORLEVEL% == 0 goto ver_2000

goto warn_os

:ver_2008
:ver_vista
:ver_7
:ver_8
:ver_81
:ver_10
set OS=wlh
goto install

:ver_2003
:ver_xp
set OS=wxp
goto install

:ver_2000
set OS=w2k
goto install

:install

echo %OS%

set system64=false
if not %OS%==w2k (
	if "%PROCESSOR_ARCHITECTURE%" == "AMD64" (
		set system64=true
	)
)
echo Uninstalling WinDriver...
if %system64% == false (
    echo 32-bit operating system detected.
        if %OS%==wlh (
          tools\x86\devcon.exe remove PCI\VEN_10E8
        ) else (
          tools\legacy\devcon.exe remove PCI\VEN_10E8
        )
	windriver\x86\wdreg.exe -inf "%CD%\windriver\x86\windrvr6.inf" uninstall > NUL
) else (
    tools\x64\devcon.exe remove PCI\VEN_10E8
    echo 64-bit operating system detected.
    windriver\x64\wdreg.exe -inf "%CD%\windriver\x64\windrvr6.inf" uninstall > NUL
)

goto exit_success
:warn_os
echo Unsupported operating system.
goto exit

:exit_success
echo Installation is complete.

:exit

