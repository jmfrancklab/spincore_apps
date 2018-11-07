#ifdef __WINDOWS__
#include <windows.h>
#include <stdio.h>
#endif

#include "io_os.h"
#include "io.h"
#include "debug.h"

extern int usb_io_cancel(HANDLE handle);

int 
io_future_init(struct io_future_t *future)
{
#ifdef __WINDOWS__
	struct io_future_desc *desc;

	future->reserved = malloc(sizeof(struct io_future_desc));

	ZeroMemory(future->reserved, sizeof(struct io_future_desc));
	desc = (struct io_future_desc *)future->reserved;

	desc->ov.hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
	desc->handle = INVALID_HANDLE_VALUE;

#else
	debug(DEBUG_WARNING, "This function is not implemented for your system.");
	return -1;
#endif

	return 0;
}

int 
io_future_reset(struct io_future_t *future)
{
#ifdef __WINDOWS__
	struct io_future_desc *desc;
	desc = (struct io_future_desc *)future->reserved;
	ResetEvent(desc->ov.hEvent);

#else
	debug(DEBUG_WARNING, "This function is not implemented for your system.");
	return -1;
#endif

	return 0;
}

int 
io_future_wait(struct io_future_t *future)
{
#ifdef __WINDOWS__
	BOOL bResult;
	DWORD transferred = 0;

	struct io_future_desc *desc;
	desc = (struct io_future_desc *) future->reserved;

	if(desc->handle == INVALID_HANDLE_VALUE) {
		return 0; //future not active, nothing to wait for
	}

	//Check the overlapped status and see if the transfer has completed
	bResult = GetOverlappedResult(desc->handle, &desc->ov, &transferred, FALSE);

	//It either failed or the xfer has not yet finished
	if(!bResult) {
		if(GetLastError() == ERROR_IO_INCOMPLETE) {
			//Block on the even handle for the async. transaction
			DWORD result = WaitForSingleObject(desc->ov.hEvent, future->wait_ms);

			if(result == WAIT_OBJECT_0) {
					return IO_FUTURE_WAIT_COMPLETE;
			}
			else if(result == WAIT_TIMEOUT) {
					return IO_FUTURE_WAIT_TIMEOUT;
			}
		}
		else {
			return IO_FUTURE_WAIT_ERROR;
		}
	}
#else
	debug(DEBUG_WARNING, "This function is not implemented for your system.");
	return -1;
#endif

	return IO_FUTURE_WAIT_COMPLETE;
}

int 
io_future_status(struct io_future_t *future)
{
#ifdef __WINDOWS__
	BOOL bResult;
	DWORD transferred;

	struct io_future_desc *desc;
	desc = (struct io_future_desc *)future->reserved;

	if(desc->handle == INVALID_HANDLE_VALUE) {
		return 0; //future not active, nothing to wait for
	}

	bResult = GetOverlappedResult(desc->handle, &desc->ov, &transferred, FALSE);
	if(!bResult) {
		if(GetLastError() == ERROR_IO_PENDING) {
			return 0;
		}
		return -1;
	}

	return 1;
#else
	debug(DEBUG_WARNING, "This function is not implemented for your system.");
	return -1;
#endif
}

int 
io_future_free(struct io_future_t *future)
{
#ifdef __WINDOWS__
	struct io_future_desc *desc;
	desc = (struct io_future_desc *) future->reserved;

	CloseHandle(desc->ov.hEvent);
	free(future->reserved);

#else
	debug(DEBUG_WARNING, "This function is not implemented for your system.");
	return -1;
#endif
	return 0;
}

int
io_future_cancel(struct io_future_t *future) 
{
	if(future == NULL ) {
		debug(DEBUG_ERROR, "Null pointer passed");
		return -1;
	}

#ifdef __WINDOWS__
	//TODO: Pass in system handle
	usb_io_cancel(future->handle);

#else
	debug(DEBUG_WARNING, "This function is not implemented for your system.");
	return -1;
#endif

	return 0;
}
