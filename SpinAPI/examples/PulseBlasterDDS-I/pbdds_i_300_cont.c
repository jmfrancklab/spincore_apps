/* Copyright (c) 2010 SpinCore Technologies, Inc.
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
 * \file dds_i_300_cont.c
 * \brief This example program tests the RF output of the PulseBlaster DDS 300.  This program will produce a 
 * continuous 1.0 MHz signal on the RF Out connector. 
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
	int start;
	int numBoards;
  
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

	printf ("Clock frequency: %.2lfMHz\n\n", CLOCK_FREQ);
	printf ("This example program produces a continuous RF sine wave on the PBDDS-I-300.\n" 
            "The default frequency is 1.0 MHz.\n\n");

	// Program the first 8 frequency registers for the PBDDS-1-300
	pb_start_programming (FREQ_REGS);
	pb_set_freq (1.0 * MHz);	// Frequency Register 0
	pb_set_freq (2.0 * MHz);	// Frequency Register 1
	pb_set_freq (3.0 * MHz);	// Frequency Register 2
	pb_set_freq (4.0 * MHz);	// Frequency Register 3
	pb_set_freq (5.0 * MHz);	// Frequency Register 4
	pb_set_freq (6.0 * MHz);	// Frequency Register 5
    pb_set_freq (7.0 * MHz);	// Frequency Register 6
	pb_set_freq (8.0 * MHz);	// Frequency Register 7
	pb_stop_programming ();

	// Program the first 2 phase registers
	pb_start_programming (TX_PHASE_REGS);
	pb_set_phase (0.0);		// Register 0
	pb_set_phase (0.0);		// Register 1
	pb_stop_programming ();


	// Write the pulse program
	pb_start_programming (PULSE_PROGRAM);

	//pb_inst_dds(freq, tx_phase, tx_enable, phase_reset, flags, inst, inst_data, length)
	start = pb_inst_dds (0, 1, TX_ENABLE, NO_PHASE_RESET, 0x1FF, CONTINUE, 0, 1000.0 * ms);
		    pb_inst_dds (0, 1, TX_ENABLE, NO_PHASE_RESET, 0x000, BRANCH, start, 1000.0 * ms);

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
}
