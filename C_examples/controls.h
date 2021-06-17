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
  * controls.h
  * mrispinapi source file for various control functions
  */

#ifndef CONTROLS_H
#define CONTROLS_H

#ifndef SPINCORE_API
#define SPINCORE_API
#endif

// errors
#define INPUT_OUT_OF_BOUNDS	0x81000001
#define UNSUCCESSFUL_WRITE	0x81000002
#define NULL_CURRENT_BOARD	0x81000003

typedef struct
{
	/// Location of the least significant bit
	DWORD start_bit;
	/// Number of bits for the control signal
	int bits;
	/// Address of the register that contains the signal
	DWORD address;
} CONTROL;


SPINCORE_API DWORD spmri_set_config_bits(DWORD data, CONTROL dest_control);
SPINCORE_API DWORD spmri_read_config_bits(DWORD* data, CONTROL dest_control);

SPINCORE_API DWORD spmri_set_fir_num_taps(DWORD data);
SPINCORE_API DWORD spmri_read_fir_num_taps(DWORD* data);

SPINCORE_API DWORD spmri_set_fir_shift_amount(DWORD data);
SPINCORE_API DWORD spmri_read_fir_shift_amount(DWORD* data);

SPINCORE_API DWORD spmri_set_fir_dec_amount(DWORD data);
SPINCORE_API DWORD spmri_read_fir_dec_amount(DWORD* data);

SPINCORE_API DWORD spmri_set_fir_reset(DWORD data);
SPINCORE_API DWORD spmri_read_fir_reset(DWORD* data);
SPINCORE_API DWORD spmri_fir_reset();

SPINCORE_API DWORD spmri_set_fir_bypass(DWORD data);
SPINCORE_API DWORD spmri_read_fir_bypass(DWORD* data);

SPINCORE_API DWORD spmri_set_cic_stages(DWORD data);
SPINCORE_API DWORD spmri_read_cic_stages(DWORD* data);

SPINCORE_API DWORD spmri_set_cic_dec_amount(DWORD data);
SPINCORE_API DWORD spmri_read_cic_dec_amount(DWORD* data);

SPINCORE_API DWORD spmri_set_cic_shift_amount(DWORD data);
SPINCORE_API DWORD spmri_read_cic_shift_amount(DWORD* data);

SPINCORE_API DWORD spmri_set_cic_m_is_two(DWORD data);
SPINCORE_API DWORD spmri_read_cic_m_is_two(DWORD* data);

SPINCORE_API DWORD spmri_set_cic_bypass(DWORD data);
SPINCORE_API DWORD spmri_read_cic_bypass(DWORD* data);

SPINCORE_API DWORD spmri_set_num_segments(DWORD data);
SPINCORE_API DWORD spmri_read_num_segments(DWORD* data);

SPINCORE_API DWORD spmri_set_scan_segment_reset(DWORD data);
SPINCORE_API DWORD spmri_read_scan_segment_reset(DWORD* data);
SPINCORE_API DWORD spmri_reset_segment_count();

SPINCORE_API DWORD spmri_set_scan_count_reset(DWORD data);
SPINCORE_API DWORD spmri_read_scan_count_reset(DWORD* data);
SPINCORE_API DWORD spmri_reset_scan_count();

SPINCORE_API DWORD spmri_set_num_samples(DWORD data);
SPINCORE_API DWORD spmri_read_num_samples(DWORD* data);

SPINCORE_API DWORD spmri_set_dac_div(DWORD data);
SPINCORE_API DWORD spmri_read_dac_div(DWORD* data);

SPINCORE_API DWORD spmri_set_dac_feedthrough(DWORD data);
SPINCORE_API DWORD spmri_read_dac_feedthrough(DWORD* data);

SPINCORE_API DWORD spmri_set_bnc_clk_sel(DWORD data);
SPINCORE_API DWORD spmri_read_bnc_clk_sel(DWORD* data);

SPINCORE_API DWORD spmri_set_filter_internal_dds(DWORD data);
SPINCORE_API DWORD spmri_read_filter_internal_dds(DWORD* data);

SPINCORE_API DWORD spmri_set_filter_bypass_mult(DWORD data);
SPINCORE_API DWORD spmri_read_filter_bypass_mult(DWORD* data);

SPINCORE_API DWORD spmri_set_overflow_reset(DWORD data);
SPINCORE_API DWORD spmri_read_overflow_reset(DWORD* data);
SPINCORE_API DWORD spmri_overflow_reset();

SPINCORE_API DWORD spmri_set_force_avg(DWORD data);
SPINCORE_API DWORD spmri_read_force_avg(DWORD* data);

SPINCORE_API DWORD spmri_set_bypass_avg(DWORD data);
SPINCORE_API DWORD spmri_read_bypass_avg(DWORD* data);

SPINCORE_API DWORD spmri_set_adc_offset(int offset);
SPINCORE_API DWORD spmri_read_adc_offset(int* offset);

#endif
