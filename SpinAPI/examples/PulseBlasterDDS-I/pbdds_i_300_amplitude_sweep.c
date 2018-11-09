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
 * \file pbdds_i_300_amplitude_sweep.c 
 * \brief This example program tests demonstrates an amplitude sweep using all the registers of the 
 * PBDDS-I-300.
 * \ingroup pbddsI
 */

#include <stdio.h>
#include <stdlib.h>

#include "spinapi.h"

#define CLOCK_FREQ 75.0

// User friendly names for the control bits
#define TX_ENABLE 1
#define TX_DISABLE 0
#define PHASE_RESET 1
#define NO_PHASE_RESET 0

#define FREQUENCY 1.0		//The frequency of the output sine wave, in MHz.
#define NUM_AMPLITUDE_REGISTERS 4	//Specify the number of registers your board has.
#define RATE 3.6		//Time (in milliseconds) between amplitude changes.

int detect_boards();
int select_board(int numBoards);

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
	double cur_amp;
	int start, i;
	int status, numBoards;

	//Uncommenting the line below will generate a debug log in your current
	//directory that can help debug any problems that you may be experiencing   
	//pb_set_debug(1); 

    printf ("Copyright (c) 2010 SpinCore Technologies, Inc.\n\n");
  
	printf("Using SpinAPI library version %s\n", pb_get_version());
	
	if((numBoards = detect_boards()) > 1) { /*If there is more than one board in the system, have the user specify.*/
		select_board(numBoards); /*Request the board numbet to use from the user*/
	}  
  
	if (pb_init () != 0) {
		printf ("Error initializing board: %s\n", pb_get_error ());
		pause();
		return -1;
	}
	
	pb_set_defaults ();
	pb_core_clock (CLOCK_FREQ);

	printf ("Clock frequency: %.2lf MHz\n\n", CLOCK_FREQ);
	printf ("This example program demonstrates an amplitude sweep using the PBDDS-I-300.\n\n"
			 "This program has specified %d different amplitudes to sweep using a %.2f MHz\n"
             "sine wave. The sweep should go from maximum to minimum amplitude, and then\n"
             "from minimum to maximum amplitude indefinitely. The time between amplitude\n"
             "changes is %.2f ms.\n",NUM_AMPLITUDE_REGISTERS, FREQUENCY, RATE);

	// Program the frequency register.
	pb_start_programming (FREQ_REGS);
	pb_set_freq (FREQUENCY * MHz);
	pb_stop_programming ();

	// Program the first 2 phase registers.
	pb_start_programming (TX_PHASE_REGS);
	pb_set_phase (0.0);		// Register 0
	pb_set_phase (0.0);		// Register 1
	pb_stop_programming ();

	cur_amp = 1.0;

	for (i = 0; i < NUM_AMPLITUDE_REGISTERS; ++i) {
		pb_set_amp (cur_amp, i);
		cur_amp -= 1.0 / NUM_AMPLITUDE_REGISTERS;
	}

	// Write the pulse program
	pb_start_programming (PULSE_PROGRAM);

	start = pb_inst_dds (0, 0, TX_DISABLE, PHASE_RESET, 0x000, CONTINUE, 0, 1.0 * us);

	for (i = 0; i < NUM_AMPLITUDE_REGISTERS; ++i) {	//Program instructions (increasing)
		pb_inst_dds_shape (0, 0, TX_ENABLE, NO_PHASE_RESET, 0, i, 0x1FF, CONTINUE, 0, RATE * ms);
	}

	for (i = NUM_AMPLITUDE_REGISTERS - 1; i >= 1; --i) {	//Program instructions (decreasing)
		pb_inst_dds_shape (0, 0, TX_ENABLE, NO_PHASE_RESET, 0, i, 0x1FF, CONTINUE, 0, RATE * ms);
	}

	pb_inst_dds (0, 0, TX_ENABLE, NO_PHASE_RESET, 0x1FF, BRANCH, start, RATE * ms);
	
	pb_stop_programming ();

	// Trigger program
    pb_reset();
	pb_start ();

	// Release control of the board
	pb_close ();

	pause();
	return 0;
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
