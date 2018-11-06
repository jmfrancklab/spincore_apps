/* Copyright (c) 2009 SpinCore Technologies, Inc.
 *   http://www.spincore.com
 *
 * This software is provided 'as-is', without any express or implied warranty. 
 * In no event will the authors be held liable for any damages arising from the 
 * use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose, 
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 * 1. The origin of this software must not be misrepresented; you must not
 * claim that you wrote the original software. If you use this software in a
 * product, an acknowledgment in the product documentation would be appreciated
 * but is not required.
 * 2. Altered source versions must be plainly marked as such, and must not be
 * misrepresented as being the original software.
 * 3. This notice may not be removed or altered from any source distribution.
 */
 
/**
 * \file pbdds_i_300_awg.c
 * \brief This program demonstrates the use of the shaped pulse feature of the 
 * PulseBlasterDDS-300
 *
 * \ingroup pbddsI
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

int detect_boards();
int select_board(int numBoards);

void program_and_start (float amp1, float amp2, float freq);
void shape_make_ramp (float *shape_data);
void shape_make_sin (float *shape_data);
void shape_make_sinc (float *shape_data, int lobes);

const double pi = 3.1415926;

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

  float amp1, amp2, freq;
  int numBoards;
  
  // These arrays will hold the value of the shapes to be used for the
  // shaped pulse feature.
  float dds_data[1024];		// Waveform for the DDS signal itself (normally a sinewave)
  float shape_data[1024];	// Waveform for the pulse shape
  
	//Uncommenting the line below will generate a debug log in your current
	//directory that can help debug any problems that you may be experiencing   
	//pb_set_debug(1); 

  printf ("Copyright (c) 2010 SpinCore Technologies, Inc.\n\n");
 
	if((numBoards = detect_boards()) > 1) { /*If there is more than one board in the system, have the user specify.*/
		select_board(numBoards); /*Request the board numbet to use from the user*/
	} 
  
	if (pb_init () != 0) {
		printf ("Error initializing board: %s\n", pb_get_error ());
		pause();
		return -1;
	}
	  
	pb_core_clock (CLOCK_FREQ);
	pb_set_defaults ();

	// Set the contents of the arrays to the desired waveform
	// (see below for the definition of these functions)
	shape_make_sinc (shape_data, 3);
	shape_make_sin (dds_data);

	//Load the shape data on the board
	pb_dds_load (shape_data, DEVICE_SHAPE);
	pb_dds_load (dds_data, DEVICE_DDS);

	printf ("\n");
	printf
		("This program demonstrates the shaped pulse feature of the PBDDS-I-300.\n"
		 "This example will output two sinc shaped pulses with the user specified\n" 
         "frequency and amplitudes. The TTL outputs are enabled during the pulse and\n"
         "can be used to trigger your oscilloscope.\n\n");

	printf ("Press CTRL-C at any time to quit\n\n");

	// Loop continuously, gathering parameters for the demo, and the programming
	// the board appropriately.
	 while (1) {
		printf ("Enter amplitude for pulse 1 (value from 0.0 to 1.0): ");
		scanf ("%f", &amp1);

		printf ("Enter amplitude for pulse 2 (value from 0.0 to 1.0): ");
		scanf ("%f", &amp2);

		printf ("Enter RF frequency (in MHz): ");
		scanf ("%f", &freq);

		program_and_start (amp1, amp2, freq);
	}

	// Release control of the board
	pb_close ();

	printf ("\n\n");
	pause();
	return 0;
}

// Program the PulseBlaster-I-300 board to run a simple demo of the shaped pulse
// feature, and then trigger the program. It will output two shaped pulses,
// as described above.
void
program_and_start (float amp1, float amp2, float freq)
{
	int start;

	pb_set_amp (amp1, 0);
	pb_set_amp (amp2, 1);
	// There are two more amplitude registers that can be programmed, but are
	// not used for this demo program.
	//pb_set_amp(0.5, 2);
	//pb_set_amp(0.3, 3);

	// set the frequency for the sine wave
	pb_start_programming (FREQ_REGS);
	pb_set_freq (freq * MHz);
	pb_stop_programming ();

	// Set the TX phase to 0.0
	pb_start_programming (TX_PHASE_REGS);
	pb_set_phase (0.0);		// in degrees
	pb_stop_programming ();

	printf ("Amplitude 1: %f\n", amp1);
	printf ("Amplitude 2: %f\n", amp2);
	printf ("Freqency:    %fMHz\n", freq);

	pb_start_programming (PULSE_PROGRAM);

	  //pb_inst_dds_shape(freq, tx_phase, tx_enable, phase_reset, use_shape, amp, flags, inst, inst_data, length)

	  // 10us shaped pulse, with amplitude set by register 0. TTL outputs on
	  start = pb_inst_dds_shape (0, 0, TX_ENABLE, NO_PHASE_RESET, USE_SHAPE, 0, 0x1FF, CONTINUE, 0, 10.0 * us);

	  // 20us shaped pulse, with amplitude set by register 1. TTL outputs on
			  pb_inst_dds_shape (0, 0, TX_ENABLE, NO_PHASE_RESET, USE_SHAPE, 1, 0x1FF, CONTINUE, 0, 20.0 * us);

	  // Output no pulse for 1ms. reset the phase. TTL outputs off. Execution
	  // branches back to the beginning of the pulse program.
			  pb_inst_dds_shape (0, 0, TX_DISABLE, PHASE_RESET, NO_SHAPE, 0, 0x00, BRANCH, start, 1.0 * ms);
	  
	  pb_stop_programming ();

      pb_reset();
	  pb_start ();
}

int
detect_boards()
{
	int numBoards;

	numBoards = pb_count_boards();	/*Count the number of boards */

    if (numBoards <= 0) {
		printf("No Boards were detected in your system. Verify that the board is firmly secured in the PCI slot.\n\n");
		pause();
		exit(-1);
	}
	
	return numBoards;
}

int
select_board(int numBoards)
{
	int choice;
	
	do {
		printf("Found %d boards in your system. Which board should be used? (0-%d): ",numBoards, numBoards - 1);
		fflush(stdin);
		scanf("%d", &choice);
		
		if (choice < 0 || choice >= numBoards) {
			printf("Invalid Board Number (%d).\n", choice);
		}
	} while (choice < 0 || choice >= numBoards);

	pb_select_board(choice);
	printf("Board %d selected.\n", choice);
	
	return 0;
}

// The following functions show how to build up arrays with different shapes
// for use with the pb_dds_load() function.

// Make a sinc shape, for use in generating soft pulses.
void
shape_make_sinc (float *shape_data, int lobes)
{
	int i;
	double x;
	double scale = (double) lobes * (2.0 * pi);
	  
	for (i = 0; i < 1024; i++) {
		  x = (double) (i - 512) * scale / 1024.0;
		  shape_data[i] = sin (x) / x;
		if ((x) == 0.0) {
		  shape_data[i] = 1.0;
		}
	}

}

// Make one period of a sinewave
void
shape_make_sin (float *shape_data)
{
	int i;

	for (i = 0; i < 1024; i++) {
		shape_data[i] = sin (2.0 * pi * ((float) i / 1024.0));
	}
}

// Make a ramp function. This is an example of a different kind of shape you
// could potentially for a shaped pulse
void
shape_make_ramp (float *shape_data)
{
	int i;

	for (i = 0; i < 1024; i++) {
		shape_data[i] = (float) i / 1024.0;
	}
}
