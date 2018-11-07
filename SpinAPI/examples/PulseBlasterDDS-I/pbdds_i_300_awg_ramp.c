/*
 * Copyright (c) 2015 SpinCore Technologies, Inc.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include "spinapi.h"

#define CLOCK_FREQ 75.0

// User friendly names for the control bits
#define TX_ENABLE 1
#define TX_DISABLE 0
#define PHASE_RESET 1
#define NO_PHASE_RESET 0
#define DO_TRIGGER 1
#define NO_TRIGGER 0
#define USE_SHAPE 1
#define NO_SHAPE 0

void pause(void)
{
	printf("Press enter to continue...");
	char buffer = getchar();
	while(buffer != '\n' && buffer != EOF);
	getchar();
}

int
main (int argc, char **argv)
{
  int start, i;
  float shape_data[1024];	// Waveform for the pulse shape

  printf ("Copyright (c) 2015 SpinCore Technologies, Inc.\n\n");
 
	if (pb_init () != 0) {
		printf ("Error initializing board: %s\n", pb_get_error ());
		return -1;
	}

	pb_select_board(0); 
	pb_core_clock (CLOCK_FREQ);
	pb_set_defaults ();

	//The DDS Shape table allows for 1024 envelope points which modulates the output
	for (i = 0; i < 1024; i++) {
		shape_data[i] = -1*((float)i)/512.0 + 1.0;
	}

	//Load the shape data on the board
	pb_dds_load (shape_data, DEVICE_SHAPE);

	printf ("\n");
	printf("This program demonstrates the shaped pulse feature of the PBDDS-I-300.\n"
		 "For a DC ramp from -2V to 2V when terminated with a 50 ohm load.\n\n");

	//Set amplitude register to full scale output 1
	pb_set_amp (1, 0);

	// Zero frequency is DC (always 1 when phase is 90.0)
	pb_start_programming (FREQ_REGS);
	pb_set_freq (0.0 * MHz);
	pb_stop_programming ();

	// Set the TX phase to 90.0 (start at sine wave peak)
	pb_start_programming (TX_PHASE_REGS);
	pb_set_phase (90.0);		
	pb_stop_programming ();

	pb_start_programming (PULSE_PROGRAM);

	// 20 us shaped pulse, with amplitude set by register 0. TTL outputs on
	start = pb_inst_dds_shape (0, 0, TX_ENABLE, NO_PHASE_RESET, USE_SHAPE, 0, 0x1FF, CONTINUE, 0, 20.0 * ms);
	pb_inst_dds_shape (0, 0, TX_DISABLE, PHASE_RESET, NO_SHAPE, 0, 0x00, BRANCH, start, 50.0 * ms);
	  
	pb_stop_programming ();

    pb_reset();
	pb_start ();

	printf("Program has been triggered.\n");

	pause();

	// Release control of the board
	pb_close ();

	return 0;
}
