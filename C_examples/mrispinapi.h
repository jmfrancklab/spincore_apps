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
  * mrispinapi.h
  * main mrispinapi source file
  */

#ifndef MRISPINAPI_H
#define MRISPINAPI_H

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>

//if building windows dll, compile with -DDLL_EXPORTS flag
//if building code to use windows dll, no -D flag necessary
#if defined(WINDOWS) || defined(WIN32)
#ifdef DLL_EXPORTS
#define SPINCORE_API __declspec(dllexport)
#else
#define SPINCORE_API __declspec(dllimport)
#endif
// else if not on windows, SPINCORE_API does not mean anything
#else
#define SPINCORE_API
#endif

#include "board.h"
#include "devices.h"
#include "controls.h"


// Errors
#define NO_BOARDS_FOUND				0x80000001
#define INVALID_CLOCK_FREQUENCY		0x80000002
#define INSTRUCTION_TOO_SHORT		0x80000003
#define INVALID_DEV_NUM				0x80000004
#define FILTER_OVERFLOW_ERROR		0x80000005
#define ACQ_OVERFLOW_ERROR			0x80000006
#define OUT_OF_MEMORY				0x80000007
#define INVALID_DAC_AMP				0x80000008
#define INVALID_DAC_ADDR			0x80000009
#define INVALID_DAC_WRITE			0x8000000A
#define INVALID_DAC_UPDATE			0x8000000B
#define INVALID_DAC_CLEAR			0x8000000C
#define INVALID_CARRIER_FREQ_SEL	0x8000000D
#define INVALID_TX_PHASE_SEL		0x8000000E
#define INVALID_TX_EN				0x8000000F
#define INVALID_PHASE_RESET			0x80000010
#define INVALID_TRIGGER_SCAN		0x80000011
#define INVALID_ENVELOPE_FREQ_SEL	0x80000012
#define INVALID_AMP_SEL				0x80000013
#define INVALID_CYCLOPS_PHASE		0x80000014
#define FELIX_OPEN_FILE_ERROR		0x80000015
#define INSTRUCTION_DATA_ERROR		0x80000016




// API Errors
#define API_OK						0x00000000
#define API_NOT_INITIALIZED			0x84000001
#define API_NO_BOARDS_CONNECTED		0x84000002
#define API_NO_BOARD_SELECTED		0x84000003
#define API_CURRENT_BOARD_NOT_INIT	0x84000004

#define MAX_NUM_BOARDS 4

#define ns 1.0
#define us 1000.0
#define ms 1000000.0

#define CONTINUE 0
#define STOP 1
#define LOOP 2
#define END_LOOP 3
#define JSR 4
#define RTS 5
#define BRANCH 6
#define LONG_DELAY 7
#define WAIT 8
#define RTI 9

// Dac Instruction Defines
#define DAC1 0
#define DAC2 1
#define DAC3 2
#define ALL_DACS 3

#define SLICE_DAC 1
#define PHASE_DAC 0
#define READOUT_DAC 2

#define DONT_WRITE 0
#define DONT_UPDATE 0
#define DONT_CLEAR 0
#define DO_WRITE 1
#define DO_UPDATE 1
#define DO_CLEAR 1

// spmri_setup_filters defines
#define BYPASS_FIR 0x00000001
#define NARROW_BW 0x00000002

// readback registers
#define RREG_STATUS 0x14
#define RREG_FIRMWARE_ID 0x7C

#ifndef UINT64
#define UINT64 unsigned long long
#endif



// BOARD_INFO structure
typedef struct
{
	// Tells if the current board is initialized
	int initialized;
	
	double board_clock_MHz;
	double pb_clock_MHz;
	double adc_clock_MHz;
	double dac_clock_MHz;
	double dac_int_clock_MHz;
	
	// The clock period in nanoseconds of the clock controlling the pulse blaster core
	double pb_clock_period_ns;
	
	// The firmware ID in hex form (example: 0x0F04)
	int firmware_id;
	
	// pusle program limits
	int num_instructions;
	
	// IMW configuration
	// bit number where each control starts
	
	int imw_dac_amp_start;
	int imw_dac_amp_bits;
	int imw_dac_addr_start;
	int imw_dac_addr_bits;
	int imw_dac_write;
	int imw_dac_update;
	int imw_dac_clear;
	
	int imw_carrier_freq_start;
	int imw_carrier_freq_bits;
	int imw_envelope_freq_start;
	int imw_envelope_freq_bits;
	
	int imw_tx_phase_start;
	int imw_tx_phase_bits;
	int imw_tx_en;
	int imw_phase_reset;
	int imw_trigger_scan;
	
	int imw_amp_start;
	int imw_amp_bits;
	
	int imw_sin_phase_start;
	int imw_sin_phase_bits;
	int imw_cos_phase_start;
	int imw_cos_phase_bits;
	
	int imw_imag_add_sub;
	int imw_real_add_sub;
	int imw_ch_swap;
	
	
	// Control registers
	// Addresses for the control registers
	DWORD fir_1;
	DWORD fir_2;
	DWORD cic_1;
	DWORD cic_2;
	DWORD acq_1;
	DWORD acq_2;
	DWORD misc_1;
	
	DWORD reg_filter_overflow;
	DWORD reg_acq_overflow;
	DWORD reg_scan_count;
	DWORD reg_flags;
	
	// CONTROL structure for the individual controls
	CONTROL fir_num_taps;
	CONTROL fir_shift_amount;
	CONTROL fir_dec_amount;
	CONTROL fir_reset;
	CONTROL fir_bypass;
	
	CONTROL cic_stages;
	CONTROL cic_dec_amount;
	CONTROL cic_shift_amount;
	CONTROL cic_m_is_two;
	CONTROL cic_bypass;
	
	CONTROL acq_num_segments;
	CONTROL acq_segment_reset;
	CONTROL acq_count_reset;
	CONTROL acq_num_samples;
	
	CONTROL dac_div;
	CONTROL dac_feedthrough;
	
	CONTROL bnc_clk_sel;
	
	CONTROL filter_sel_internal_dds;
	CONTROL filter_bypass_mult;
	
	CONTROL overflow_reset;
	
	CONTROL mem_force_average;
	CONTROL mem_bypass_average;
	
	CONTROL adc_offset;
	
	// Device registers
	// Addresses for the different device registers
	DWORD freq_addr;
	DWORD freq_data;
	DWORD phase_addr;
	DWORD phase_data;
	DWORD shape_addr;
	DWORD shape_data;
	DWORD memory_addr;
	DWORD memory_data;
	DWORD fir_coeff_addr;
	DWORD fir_coeff_data;
	
	// DEVICE structures for each of the devices
	DEVICE cos_phase;
	DEVICE sin_phase;
	DEVICE tx_phase;
	
	DEVICE rx_freq;
	DEVICE tx_freq;
	DEVICE envelope_freq;
	
	DEVICE amp_shape;
	DEVICE carrier_shape;
	DEVICE envelope_shape;
	
	DEVICE memory;
	
	DEVICE fir_coeff;
	
	
} BOARD_INFO;


SPINCORE_API char* spmri_get_version();

SPINCORE_API DWORD spmri_api_check_status();

SPINCORE_API BOARD_INFO* spmri_get_current_board();

SPINCORE_API DWORD spmri_init();

SPINCORE_API DWORD spmri_set_clock(double clock_MHz);

SPINCORE_API DWORD spmri_set_defaults();

SPINCORE_API DWORD spmri_start_programming();

SPINCORE_API DWORD spmri_inst(UINT64 flags, DWORD data, char op, double delay_ns);

SPINCORE_API DWORD spmri_dac_inst(double amp, char dac_addr, char write, char update,
char clear, UINT64 flags, DWORD data, char op, double delay_ns);

SPINCORE_API DWORD spmri_mri_inst(double dac_amp, char dac_addr, char write, char update,
char clear, int freq, int tx_phase, char tx_en, char phase_reset,
char trigger_scan, char envelope_freq, int amp, char cyclops_phase,
UINT64 flags, DWORD data, char op, double delay_ns);

SPINCORE_API DWORD spmri_setup_filters(double spectral_width, int scan_repetitions, int cmd, int* dec_amount);

SPINCORE_API DWORD spmri_setup_cic(DWORD dec_amount, DWORD shift_amount, DWORD m, DWORD stages);

SPINCORE_API DWORD spmri_setup_fir(DWORD num_taps, int *coeff, DWORD shift_amount, DWORD dec_amount);

SPINCORE_API DWORD spmri_get_firmware_id(DWORD* board_id, DWORD* revision_id);

SPINCORE_API DWORD spmri_get_flags(DWORD* flags_out);

SPINCORE_API DWORD spmri_get_scan_count(DWORD* scan_count);

SPINCORE_API DWORD spmri_check_overflow();

SPINCORE_API DWORD spmri_write_felix(char *fnameout, char *title_string, int num_points, float SW, float SF, int *real_data, int *imag_data);

#endif
