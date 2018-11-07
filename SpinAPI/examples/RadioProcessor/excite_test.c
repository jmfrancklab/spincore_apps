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
 * \file excite_test.c
 * \brief The example program tests the excitation portion of the RadioProcessor.
 * This program will produce a 1MHz signal on the oscilloscope that is on
 * for 10 microseconds, off for 1 milisecond, and the repeat this pattern.
 * \ingroup RP
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
#define DO_TRIGGER 1
#define NO_TRIGGER 0

int detect_boards();
int select_board(int numBoards);

void pause(void)
{
	printf("Press enter to continue...");
	char buffer = getchar();
	while(buffer != '\n' && buffer != EOF);
	getchar();
}

int main(int argc, char **argv)
{
	int start;
	int numBoards;

	//Uncommenting the line below will generate a debug log in your current
	//directory that can help debug any problems that you may be experiencing   
	//pb_set_debug(1); 

	printf("Using SpinAPI library version %s\n", pb_get_version());

	/*If there is more than one board in the system, have the user specify. */
	if ((numBoards = detect_boards()) > 1) {
		select_board(numBoards);
	}

	if (pb_init() != 0) {
		printf("Error initializing board: %s\n", pb_get_error());
		pause();
		return -1;
	}

	pb_set_defaults();
	pb_core_clock(CLOCK_FREQ);

	printf("Clock frequency: %.2lfMHz\n\n", CLOCK_FREQ);
	printf("The example program tests the excitation portion of the "
	       "RadioProcessor.  This program will produce a 1MHz signal on the "
	       "RF connector that is on for 10 microseconds, off for 1 "
	       "milisecond, and will then repeat this pattern.\nAll TTL flags "
	       "will be high during the RF signal and low while it is off.\n\n");

	// Write 1 MHz to the first frequency register
	pb_start_programming(FREQ_REGS);
	pb_set_freq(1.0 * MHz);
	pb_stop_programming();

	// Write 0.0 degrees to the first phase register of all channels
	pb_start_programming(TX_PHASE_REGS);
	pb_set_phase(0.0);
	pb_stop_programming();

	pb_start_programming(COS_PHASE_REGS);
	pb_set_phase(0.0);
	pb_stop_programming();

	pb_start_programming(SIN_PHASE_REGS);
	pb_set_phase(0.0);
	pb_stop_programming();

	// Write the pulse program
	pb_start_programming(PULSE_PROGRAM);

	// This instruction enables a 1 MHz analog output
	start =
	    pb_inst_radio(0, 0, 0, 0, TX_ENABLE, NO_PHASE_RESET, NO_TRIGGER,
			  0x3F, CONTINUE, 0, 10.0 * us);

	// This instruction disables the analog output (and resets the phase in
	// preparation for the next instruction)
	pb_inst_radio(0, 0, 0, 0, TX_DISABLE, PHASE_RESET, NO_TRIGGER, 0x0,
		      BRANCH, start, 1.0 * ms);

	pb_stop_programming();

	// Trigger program
	pb_reset();
	pb_start();

	// print warning and wait for user to press a key while board runs
	printf("***WARNING***\nIf the command line is closed without a preceeding "
		   "key press, the board will continue to run until excite_test is run"
		   " again and allowed to complete properly.\n");
	pause();

	// Stop the program
	pb_stop();

	// Release control of the board
	pb_close();

	return 0;
}

int detect_boards()
{
	int numBoards;

	numBoards = pb_count_boards();	/*Count the number of boards */

	if (numBoards <= 0) {
		printf
		    ("No Boards were detected in your system. Verify that the board "
		     "is firmly secured in the PCI slot, or that the USB cable is plugged in.\n\n");
		pause();
		exit(-1);
	}

	return numBoards;
}

int select_board(int numBoards)
{
	int choice;

	do {
		printf
		    ("Found %d boards in your system. Which board should be used? "
		     "(0-%d): ", numBoards, numBoards - 1);
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
