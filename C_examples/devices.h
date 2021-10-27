/* 
  * Copyright (c)  2011, SpinCore Technologies, Inc.
  * All rights reserved.
  *
  * This program is free software: you can redistribute it and/or modify
  * it under the terms of the GNU General Public License as published by
  * the Free Software Foundation, either version 3 of the License, or
  * (at your option) any later version.
  * 
  * This program is distributed in the hope that it will be useful,
  * but WITHOUT ANY WARRANTY; without even the implied warranty of
  * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  * GNU General Public License for more details.
  * 
  * You should have received a copy of the GNU General Public License
  *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
  */

/*
  * devices.h
  * mrispinapi source file for various device control functions
  */

#ifndef DEVICES_H
#define DEVICES_H

#ifndef SPINCORE_API
#define SPINCORE_API
#endif

#define DATA_OUT_OF_BOUNDS		0x87000001
#define DEVICE_NOT_SELECTED		0x87000002
#define INVALID_DEVICE_ADDRESS	0x87000003
#define DEVICE_NOT_WRITABLE		0x87000004
#define DEVICE_NOT_READABLE		0x87000005
#define INVALID_ARRAY_LENGTH	0x87000006
#define SHAPE_NUM_POINTS_ERROR	0x87000007
#define SHAPE_DATA_ERROR		0x87000008
#define AMP_DATA_ERROR			0x87000009
#define INVALID_NUM_POINTS		0x8700000A

#define DEVICE_OFFSET_MASK	0xFF000000
#define DEVICE_ADDR_MASK	0x00FFFFFF

// DEVICE structure
typedef struct
{
	// Address of the register that contains the destination address
	DWORD destaddr_addr;
	// Address of the register that contains the destination data
	DWORD destdata_addr;
	// Address offset for the device
	DWORD addr_offset;
	// Number of registers in the device
	int num_registers;
	// Width of the data port in bits
	int width;
	// Tells if the device is readable
	int readable;
	// Tells if the device is writable
	int writable;
} DEVICE;


SPINCORE_API DWORD spmri_write_to_device( DWORD data, DEVICE dev );

SPINCORE_API DWORD spmri_write_to_device_address( DWORD data, DWORD address, DEVICE dev );

SPINCORE_API DWORD spmri_read_from_device( DWORD* data, DEVICE dev );

SPINCORE_API DWORD spmri_read_from_device_address( DWORD* data, DWORD address, DEVICE dev );

SPINCORE_API DWORD spmri_set_device_address( DWORD address, DEVICE dev );

SPINCORE_API DWORD spmri_read_device_address( DWORD* address, DEVICE dev );

SPINCORE_API DWORD spmri_start_device_programming( DEVICE dev );

SPINCORE_API DWORD spmri_set_frequency_registers( double* freqs, int num_freqs );

SPINCORE_API DWORD spmri_set_envelope_frequency_registers( double* freqs, int num_freqs );

SPINCORE_API DWORD spmri_set_phase_registers( double* tx_phases, int num_phases );

SPINCORE_API DWORD spmri_set_envelope_shape( double* shape, int num_points );

SPINCORE_API DWORD spmri_set_carrier_shape( double* shape, int num_points );

SPINCORE_API DWORD spmri_set_amplitude_registers( double* amp, int num_amps );

SPINCORE_API DWORD spmri_read_memory( int* real, int* imag, int num_points );
#endif
