#include <stdio.h>
#include <string.h>

#include <Windows.h>
#include <Setupapi.h>

#include "debug.h"
#include "cyioctl.h"
#include "driver-usb.h"
#include "usb.h"
#include "usb_endpoints.h"
#include "util.h"
#include "io.h"
#include "io_os.h"

#define MAX_USB 128
#define MAX_IO_WAIT_TIME 500	//Max time to wait for a IO transfer (read or write) to complete in milliseconds.
#define MAX_IO_ATTEMPTS  3	    //Number of times to try a single transfer before giving up.

static HANDLE h_list[MAX_USB];
int pid_list[MAX_USB];

// Helper function internal to the usb code. These should not be accessed outside this file
static HANDLE usb_get_handle (int dev_num);
static int usb_get_device_name (HANDLE h);
static int usb_get_friendly_name (HANDLE h);
static int usb_get_num_endpoints (HANDLE h);
static unsigned int usb_get_driver_version (HANDLE h);
//static int usb_get_power_state(HANDLE h);
//static int usb_get_xfer_size(HANDLE h, int pipe);
//static int usb_set_xfer_size(HANDLE h, int pipe, unsigned int xfer_size);
static int usb_reset_pipe (HANDLE h, int pipe);
static int usb_abort_pipe (HANDLE h, int pipe);



const GUID CYUSBDRV_GUID =
  { 0xae18aa60, 0x7f6a, 0x11d4, {0x97, 0xdd, 0x00, 0x01, 0x02, 0x29, 0xb9,
				 0x59}
};


int
os_usb_count_devices (int vendor_id)
{
	int i, j, ret;

	SP_DEVINFO_DATA devInfoData;
	devInfoData.cbSize = sizeof(SP_DEVINFO_DATA);

	SP_DEVICE_INTERFACE_DATA devInterfaceData;
	devInterfaceData.cbSize = sizeof(SP_DEVICE_INTERFACE_DATA);

	PSP_INTERFACE_DEVICE_DETAIL_DATA functionClassDeviceData;

	ULONG requiredLength = 0;

	HDEVINFO hwDeviceInfo = SetupDiGetClassDevs((LPGUID)& CYUSBDRV_GUID,
		NULL,
		NULL,
		DIGCF_PRESENT |
		DIGCF_INTERFACEDEVICE);


	if (hwDeviceInfo == INVALID_HANDLE_VALUE)
	{
		debug(DEBUG_ERROR, "os_usb_count_devices: SetupDiGetClassDevs() failed with %d", (int)GetLastError());
		return -1;
	}

	debug(DEBUG_INFO, "os_usb_count_devices: Enumerating USB Devices...");

	for (i = 0, j = 0; i < MAX_USB; ++i)
	{

		if (!SetupDiEnumDeviceInterfaces
			(hwDeviceInfo, 0, (LPGUID)& CYUSBDRV_GUID, i, &devInterfaceData))
		{
			if (!((ret = GetLastError()) == ERROR_NO_MORE_ITEMS))
			{
				debug(DEBUG_ERROR, "os_usb_count_devices: SetupDiEnumDeviceInterfaces failed with error code %d!", (int)GetLastError());
				break;
			}
			else
			{
				debug(DEBUG_INFO, "os_usb_count_devices: Enumeration Completed. Found %d Devices.", i);
				break;
			}
		}
		SetupDiGetInterfaceDeviceDetail(hwDeviceInfo, &devInterfaceData, NULL,
			0, &requiredLength, NULL);

		functionClassDeviceData =
			(PSP_INTERFACE_DEVICE_DETAIL_DATA)malloc(requiredLength);
		functionClassDeviceData->cbSize =
			sizeof(SP_INTERFACE_DEVICE_DETAIL_DATA);

		if (!SetupDiGetInterfaceDeviceDetail(hwDeviceInfo, &devInterfaceData,
			functionClassDeviceData,
			requiredLength,
			&requiredLength, &devInfoData))
		{

			debug(DEBUG_ERROR, "usb_get_handle: SetupDiGetClassDevs() failed with %d", (int)GetLastError());
			break;

		}

		if (strncmp(functionClassDeviceData->DevicePath + 8, "vid_0403&pid_c1a9", 17) == 0)
		{
			pid_list[j] = 0xc1a9;
			debug(DEBUG_INFO, "-SP7 Board Detected.");
		}
		else
			if (strncmp(functionClassDeviceData->DevicePath + 8, "vid_0403&pid_c2a9", 17) == 0)
			{
				pid_list[j] = 0xc2a9;
				debug(DEBUG_INFO, "-SP15 Board Detected.");
			}
			else
				if (strncmp(functionClassDeviceData->DevicePath + 8, "vid_0403&pid_c1aa", 17) == 0)
				{
					pid_list[j] = 0xc1aa;
					debug(DEBUG_INFO, "-SP9 Board Detected.");
				}
				else
					if (strncmp(functionClassDeviceData->DevicePath + 8, "vid_0403&pid_c1ab", 17) == 0)
					{
						pid_list[j] = 0xc1ab;
						debug(DEBUG_INFO, "-SP9 Board Detected (pid_c1ab).");
					}
					else
					{
						debug(DEBUG_WARNING, "-Cypress USB Chip detected. VID/PID unknown.");
					}

		if (pid_list[j] != 0)
		{
			h_list[j] = CreateFile(functionClassDeviceData->DevicePath,
				GENERIC_WRITE | GENERIC_READ,
				FILE_SHARE_WRITE | FILE_SHARE_READ,
				NULL,
				OPEN_EXISTING, FILE_FLAG_OVERLAPPED, NULL);

			debug(DEBUG_INFO, "Device Handle=0x%lx", (unsigned long long)h_list[j]);
			debug(DEBUG_INFO, "--System Path: %s", functionClassDeviceData->DevicePath);
			j++;
		}

		free(functionClassDeviceData);
	}

	SetupDiDestroyDeviceInfoList(hwDeviceInfo);

	return ((ret == ERROR_NO_MORE_ITEMS) ? i : ret);
}

int
os_usb_init (int dev_num)
{
	HANDLE h;

	int num_endpoints;

	// Get a handle to the device
	h = usb_get_handle(dev_num);

	if (h == INVALID_HANDLE_VALUE)
	{
		debug(DEBUG_ERROR, "os_usb_init: Unable to get handle for device", );
		return -1;
	}

	h_list[dev_num] = h;

	num_endpoints = usb_get_num_endpoints(h);

	if (num_endpoints != 3) {
		debug(DEBUG_ERROR, "os_usb_init(): Internal error: device has wrong # of endpoints (found: %d)", num_endpoints);
		return -1;
	}

	//usb_get_device_name(h);
	usb_get_friendly_name(h);
	usb_get_driver_version(h);
	//usb_get_power_state(h);

	return pid_list[dev_num];
}

int
os_usb_close ()
{
	int i;

	for (i = 0; i < MAX_USB; ++i)
	{
		if (h_list[i] == INVALID_HANDLE_VALUE)
			break;
		else
			CloseHandle(h_list[i]);
	}
	return 0;
}

static HANDLE
usb_get_handle (int dev_num)
{
  return h_list[dev_num];
}

int
usb_io_cancel(HANDLE handle)
{
	usb_abort_pipe(handle, EP1OUT);
	usb_reset_pipe(handle, EP1OUT);

	usb_abort_pipe(handle, EP6IN);
	usb_reset_pipe(handle, EP6IN);

	usb_abort_pipe(handle, EP2OUT);
	usb_reset_pipe(handle, EP2OUT);

	return 0;
}

int
os_usb_reset_pipes (int dev_num)
{
  debug(DEBUG_INFO, "Resetting USB endpoints...");
  usb_io_cancel(h_list[dev_num]);

  return 0;
}


int
usb_io_async(HANDLE handle, UCHAR ep, struct io_future_t *future)
{
	BOOL bResult;
	PSINGLE_TRANSFER pTransfer;
	OVERLAPPED *overlapped;

	struct io_future_desc *desc = (struct io_future_desc*) future->reserved;

	//Setup OS-dependent transfer specifics
	overlapped = &desc->ov;
	desc->dwBytes = 0;
	pTransfer = &desc->transfer;

	if (handle == INVALID_HANDLE_VALUE) {
		return -1;
	}

	if (desc->handle != INVALID_HANDLE_VALUE) {
		debug(DEBUG_ERROR, "IO operation failed. Future provided has already been used or not been initialized/reset.");
		return -1;
	}

	//Store the handle associated with the IO into the future.
	desc->handle = handle;

	//Setup single transfer description
	ZeroMemory(pTransfer, sizeof(SINGLE_TRANSFER));
	pTransfer->ucEndpointAddress = ep;

	//Queue the transfer

	bResult = DeviceIoControl(handle, IOCTL_ADAPT_SEND_NON_EP0_DIRECT,
		(PUCHAR)pTransfer, sizeof(SINGLE_TRANSFER),
		future->buffer, future->sz_buffer,
		&desc->dwBytes, &desc->ov);

	if (!bResult && GetLastError() != ERROR_IO_PENDING) {
		goto usb_io_non_ep0_async_error;
	}

	return 0;

usb_io_non_ep0_async_error:
	{
		LPTSTR pMsgBuf;
		FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
			NULL, GetLastError(), MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPTSTR)&pMsgBuf, 0, NULL);

		debug(DEBUG_ERROR, "IO Failure: %s", pMsgBuf);
		HeapFree(GetProcessHeap(), 0, pMsgBuf);
	}

	return -1;
}
#define DEFAULT_IO_TIMEOUT_MS 1000
int
usb_io_sync(HANDLE handle, unsigned char ep, void *buffer, unsigned int nbytes)
{
	struct io_future_t future;
	int io_status;

	//Initialize the future
	io_future_init(&future);

	future.handle = handle; //Subsystem handle for device
	future.wait_ms = DEFAULT_IO_TIMEOUT_MS; //Wait at most 1 second
	future.buffer = buffer;
	future.sz_buffer = nbytes;

	//Perform an asynchronous operation
	if (usb_io_async(handle, ep, &future) != 0) {
		debug(DEBUG_ERROR, "Failed to queue IO operation.");
		goto _usb_io_sync_error;
	}

	//Wait for completion
	io_status = io_future_wait(&future);

	switch (io_status) {
	case IO_FUTURE_WAIT_TIMEOUT:
		debug(DEBUG_ERROR, "Synchronous operation time-out.");
		goto _usb_io_sync_error;

	case IO_FUTURE_WAIT_ERROR:
		debug(DEBUG_ERROR, "Synchronous operation error.");
		goto _usb_io_sync_error;
		break;
	}

	//Cleaup the future
	io_future_free(&future);

	return 0;

_usb_io_sync_error:
	//Cancel IO
	io_future_cancel(&future);

	io_future_free(&future);
	return -1;
}

int
os_usb_write (int dev_num, int pipe, const void *data, int size)
{
	return usb_io_sync(h_list[dev_num], pipe, *((void**)&data), size);
}

int
os_usb_read (int dev_num, int pipe, void *data, int size)
{
	return usb_io_sync(h_list[dev_num], pipe, data, size);
}

static int
usb_get_device_name (HANDLE handle)
{
	DWORD dwBytes = 0;
	UCHAR iobuf[256];
	BOOL bResult;

	bResult = DeviceIoControl(handle, IOCTL_ADAPT_GET_DEVICE_NAME,
		iobuf, sizeof(iobuf), /*lpInBuffer,  nInBufferSize*/
		iobuf, sizeof(iobuf), /*lpOutBuffer, nOutBufferSize*/
		&dwBytes, NULL);

	if (bResult == 0) {
		LPTSTR pMsgBuf;
		FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
			NULL, GetLastError(), MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPTSTR)&pMsgBuf, 0, NULL);
		debug(DEBUG_ERROR, "Failed to get USB friendly name: %s", pMsgBuf);
		HeapFree(GetProcessHeap(), 0, pMsgBuf);
		return -1;
	}

	debug(DEBUG_INFO, "Name: %s", iobuf);

#if 0
	if (buffer != NULL) {
		CopyMemory(buffer, iobuf, sizeof(iobuf));
	}
#endif
	return 0;
}

static int
usb_get_friendly_name (HANDLE handle)
{
	DWORD dwBytes = 0;
	UCHAR iobuf[256];
	BOOL bResult;

	bResult = DeviceIoControl(handle, IOCTL_ADAPT_GET_FRIENDLY_NAME,
		iobuf, sizeof(iobuf), /*lpInBuffer,  nInBufferSize*/
		iobuf, sizeof(iobuf), /*lpOutBuffer, nOutBufferSize*/
		&dwBytes, NULL);

	if (!bResult) {
		LPTSTR pMsgBuf;
		FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
			NULL, GetLastError(), MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPTSTR)&pMsgBuf, 0, NULL);
		debug(DEBUG_ERROR, "Failed to get USB friendly name: %s", pMsgBuf);
		HeapFree(GetProcessHeap(), 0, pMsgBuf);
		return -1;
	}

	debug(DEBUG_INFO, "Friendly Name: %s", iobuf);
#if 0
	if (buffer != NULL) {
		CopyMemory(buffer, iobuf, sizeof(iobuf));
	}
#endif
	return 0;
}

static int
usb_get_num_endpoints (HANDLE handle)
{
	DWORD dwBytes = 0;
	BOOL bResult;
	UCHAR endpoints;

	bResult = DeviceIoControl(handle, IOCTL_ADAPT_GET_NUMBER_ENDPOINTS,
		NULL, 0, /*lpInBuffer,  nInBufferSize*/
		&endpoints, sizeof(UCHAR), /*lpOutBuffer, nOutBufferSize*/
		&dwBytes, NULL);

	if (!bResult) {
		LPTSTR pMsgBuf;
		FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
			NULL, GetLastError(), MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPTSTR)&pMsgBuf, 0, NULL);
		debug(DEBUG_ERROR, "Failed to detect number of endpoints: %s", pMsgBuf);
		HeapFree(GetProcessHeap(), 0, pMsgBuf);
		return -1;
	}

	debug(DEBUG_INFO, "Detected endpoints: %d", endpoints);

	return endpoints;
}


static unsigned int
usb_get_driver_version (HANDLE handle)
{
	DWORD dwBytes = 0;
	BOOL bResult;
	ULONG ver;

	bResult = DeviceIoControl(handle, IOCTL_ADAPT_GET_DRIVER_VERSION,
		&ver, sizeof(ULONG),  /*lpInBuffer,  nInBufferSize*/
		&ver, sizeof(ULONG),  /*lpOutBuffer, nOutBufferSize*/
		&dwBytes, NULL);

	if (!bResult) {
		LPTSTR pMsgBuf;
		FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
			NULL, GetLastError(), MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPTSTR)&pMsgBuf, 0, NULL); \

			debug(DEBUG_ERROR, "Failed to get driver version: %s", pMsgBuf);
		HeapFree(GetProcessHeap(), 0, pMsgBuf);
		return -1;
	}

	debug(DEBUG_INFO, "Driver version: %d", ver);

	return ver;
}


static int
usb_reset_pipe (HANDLE handle, int pipe)
{
	DWORD dwBytes = 0;
	BOOL bResult;
	UCHAR address = pipe;

	bResult = DeviceIoControl(handle, IOCTL_ADAPT_RESET_PIPE,
		&address, sizeof(UCHAR), /*lpInBuffer,  nInBufferSize*/
		NULL, 0,                 /*lpOutBuffer, nOutBufferSize*/
		&dwBytes, NULL);

	if (!bResult) {
		LPTSTR pMsgBuf;
		FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
			NULL, GetLastError(), MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPTSTR)&pMsgBuf, 0, NULL);

		debug(DEBUG_ERROR, "Failed to reset USB endpoint address=0x%x: %s", address, pMsgBuf);

		HeapFree(GetProcessHeap(), 0, pMsgBuf);
		return -1;
	}

  return 0;
}

static int
usb_abort_pipe (HANDLE handle, int pipe)
{
	DWORD dwBytes = 0;
	BOOL bResult;
	UCHAR address = pipe;

	bResult = DeviceIoControl(handle, IOCTL_ADAPT_ABORT_PIPE,
		&address, sizeof(UCHAR), /*lpInBuffer,  nInBufferSize*/
		NULL, 0,                 /*lpOutBuffer, nOutBufferSize*/
		&dwBytes, NULL);

	if (!bResult) {
		LPTSTR pMsgBuf;

		FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
			NULL, GetLastError(), MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPTSTR)&pMsgBuf, 0, NULL);

		debug(DEBUG_ERROR, "Failed to abort USB endpoint address=0x%x: %s", address, pMsgBuf);

		HeapFree(GetProcessHeap(), 0, pMsgBuf);
		return -1;
	}

	return 0;
}
