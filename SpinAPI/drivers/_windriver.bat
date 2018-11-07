@echo off
setlocal
REM Check operating system

set OS=unknown
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
if "%version%" == "10.0" set OS=wlh
if "%version%" == "6.3" set OS=wlh
if "%version%" == "6.2" set OS=wlh
if "%version%" == "6.1" set OS=wlh
if "%version%" == "6.0" set OS=wlh
if "%version%" == "5.2" set OS=wxp
if "%version%" == "5.1" set OS=wxp
if "%version%" == "5.0" set OS=w2k

if %OS%==unknown (
  echo Unsupported operating system.
)

:install
set system64=false
if not %OS%==w2k (
	if "%PROCESSOR_ARCHITECTURE%" == "AMD64" (
		set system64=true
	)
)

echo Installing WinDriver...

REM if "%version%" == "10.0" (
REM   echo Windows 10 is not currently supported for PCI/PCIe devices
REM   goto :inf
REM )

if %system64% == false (
    echo 32-bit operating system detected.
    tools\x86\devcon.exe remove PCI\VEN_10E8
    windriver\x86\wdreg.exe -inf "%CD%\windriver\x86\windrvr6.inf" install 
) else (
    echo 64-bit operating system detected.
    tools\x64\devcon.exe remove PCI\VEN_10E8
    windriver\x64\wdreg.exe -inf "%CD%\windriver\x64\windrvr6.inf" install 
)

:inf

echo Installation is complete.
endlocal

