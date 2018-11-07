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
  * \file pb24_ex3.c
  * \brief Example program for PulseBlaster24 boards
  * 
  * This demonstrates the ability to set the default flag states 
  * on the certain PB24 designs.
  * 
  * \ingroup pb24
  *
  */

#include <stdio.h>
#include <stdlib.h>

#define PB24
#include "spinapi.h"

int detect_boards();
int select_board(int numBoards);
int input_clock(double *retClock);

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
	double clock;

	//Uncommenting the line below will generate a debug log in your current
	//directory that can help debug any problems that you may be experiencing   
	//pb_set_debug(1); 

	printf("Copyright (c) 2010 SpinCore Technologies, Inc.\n\n");

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
	
	//User input clock
	input_clock(&clock);
	
	// Tell driver what clock frequency the board uses
	pb_core_clock(clock);

	printf("Clock frequency: %lfMHz\n\n", clock);
	printf("TTL outputs 0-3 will generate a pulse with a period of "
	       "100 ms.  The outputs will be high for 60 ms, low for 40 ms, and "
	       "then program will repeat.\n\n");

	// Prepare the board to receive pulse program instructions
	pb_start_programming(PULSE_PROGRAM);

	// Instruction 0 - Continue to instruction 1 in 20ns
	// The lower 4 bits (all BNC connectors) will be driving high
	// For PBESR-PRO boards, or-ing THREE_PERIOD with the flags
	// causes a 3 period short pulse to be used. 
	start = pb_inst(0xF, CONTINUE, 0, 20.0 * ms);

	// Instruction 1 - Continue to instruction 2 in 40ns
	// The lower 4 bits (all BNC connectors) will be driving high
	// the entire 40ns.
	pb_inst(0xF, CONTINUE, 0, 40.0 * ms);

	// Instruction 2 - Branch to "start" (Instruction 0) in 40ns
	// Outputs are off
	pb_inst(0, BRANCH, start, 40.0 * ms);

	pb_stop_programming();	// Finished sending instructions

	pb_reset();
	pb_start();

	// End communication with the PulseBlaster24 board. The pulse program
	// will continue to run even after this is called.
	pb_close();

	pause();
	return 0;
}

int detect_boards()
{
	int numBoards;

	numBoards = pb_count_boards();	/*Count the number of boards */

	if (numBoards <= 0) {
		printf
		    ("No Boards were detected in your system. Verify that the board "
		     "is properly connected.\n\n");
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
}

int input_clock(double *retClock)
{	
	char clock[256];
	double user_input = -1.0;
	char* user_end;	
		
	do {
		fflush(stdin);
		printf("\nPlease enter internal clock frequency (MHz): ");
		scanf("%256s", clock);
		user_input = strtod(clock,&user_end);
	}	while(user_end[0] != '\0');

    *retClock = user_input;
}
