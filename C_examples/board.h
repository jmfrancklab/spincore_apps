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

#ifndef BOARD_H
#define BOARD_H

#include "pci.h"

#ifndef SPINCORE_API
#define SPINCORE_API
#endif

// Register Addresses
#define IMW_ADDR	0x0000
#define IMW_DATA1	0x0004
#define IMW_DATA2	0x0008
#define IMW_DATA3	0x000C
#define IMW_DATA4	0x0010
#define	STATUS_REG	0x0014

// Errors
#define IMW_TRANSFER_ERROR 0x82000001

#ifndef DWORD
#define DWORD unsigned int
#endif

enum{BAR0=0,BAR1,BAR2,BAR3,BAR4,BAR5,BAR6,BAR7};

SPINCORE_API DWORD spmri_write_imw(DWORD* imw);
SPINCORE_API DWORD spmri_write_addr(DWORD addr);
SPINCORE_API DWORD spmri_read_addr(DWORD *addr);
SPINCORE_API DWORD spmri_write_imw_addr(DWORD addr, DWORD* imw);
SPINCORE_API DWORD spmri_start();
SPINCORE_API DWORD spmri_stop();
SPINCORE_API DWORD spmri_get_status(DWORD* status);
SPINCORE_API DWORD spmri_write_reg(DWORD address, DWORD data);
SPINCORE_API DWORD spmri_read_reg(DWORD address, DWORD* data);

#endif
