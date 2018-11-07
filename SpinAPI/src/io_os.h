#pragma once
#ifdef __WINDOWS__
#include <Windows.h>
#include "cyioctl.h"

/** 
 * This structure defines the OS-dependent
 * information needed to perform an async. IO.
 * On Windows, we need to keep track of the associated
 * system device handle, and allocated overlapped structure 
 * which contains a valid event handle for blocking on.
 */
struct io_future_desc 
{
	HANDLE handle; /*< Windows system device handle*/
	DWORD dwBytes; /*Number of bytes completed*/
	SINGLE_TRANSFER transfer; /*Transfer object for IO request*/
	OVERLAPPED ov; /*< Associated overlapped IO data structure*/
};

#endif
