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

:inf

echo Installing INF files...
if %system64% == true (
  if %OS%==wlh (
    if "%version%"=="10.0" (
      pnputil -i -a pci\spinpci.inf
      pnputil -i -a usb\cypress\win10\x64\spinusb.inf
    ) ELSE (
      pnputil -i -a pci\spinpci.inf
      pnputil -i -a usb\cypress\legacy\wlh\x64\spinusb.inf
    )
    pnputil -i -a usb\d2xx\ftdibus.inf
    tools\x64\devcon.exe rescan
  )
) else (
  if %OS%==wlh (
    if %version%=="10.0" (
      pnputil -i -a pci\spinpci.inf
      pnputil -i -a usb\cypress\win10\x86\spinusb.inf
    ) ELSE (
      pnputil -i -a pci\spinpci.inf
      pnputil -i -a usb\cypress\legacy\wlh\x86\spinusb.inf
    )
    pnputil -i -a usb\d2xx\ftdibus.inf
    
    tools\x86\devcon.exe rescan
  )
  
  if %OS%==wxp (
    tools\legacy\devcon.exe rescan
  )

  if %OS%==w2k (
    tools\legacy\devcon.exe rescan
  )

)

echo Installation is complete.
endlocal

