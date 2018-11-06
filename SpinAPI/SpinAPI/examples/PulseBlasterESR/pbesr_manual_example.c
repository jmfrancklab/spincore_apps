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
 * \file ESR_manual_example.c
 * \brief PulseBlasterESR  Example program from product manual
 *
 *  This program will create an infinite loop consisting of three intervals during 
 *  which a) all 24 output bits will be ON for 40ns, b) bit #0 will be OFF and the
 *  remaining 23 output bits will be ON for 80 ns, and c) all output bits will be
 *  OFF for 1us.
 *
 * \ingroup ESR
 */

#include <stdio.h>
#include <stdlib.h>

#define PBESR
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

int
main (int argc, char **argv)
{
	int start, numBoards; 
	double clock_freq;

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
	
	//Set the clock frequency.
	if (argc > 1) {
		clock_freq = atof (argv[1]);
	}
	else {
		//User input clock
		input_clock(&clock_freq);
	}
	
	printf ("Using clock frequency: %.2f MHz\n\n", clock_freq);
	printf("You should now see a pulsetrain where: \n\n a) all 24 output bits will be ON for 40ns, then \n\n b) bit #0 will be OFF and the remaining 23 output bits will be ON for 80 ns, and then \n\n c) all output bits will be OFF for 1us. \n\n");

	// Tell driver what clock frequency the board uses
	pb_core_clock (clock_freq);

	// Prepare the board to receive Pulse Program instructions
	pb_start_programming (PULSE_PROGRAM);

	// Instruction #0 - All outputs ON, continue to Instruction #1 after 40ns
	// Flags = 0xFFFFFF (all outputs ON), 
	// OPCODE = CONTINUE (proceed to next instruction after specified delay)
	// Data Field = empty.  This field is ignored for CONTINUE instructions.
	// Delay Count = 40*ns (other valid units are *us, *ms)
	start = pb_inst (0xFFFFFF, CONTINUE, 0, 40 * ns);

	// Instruction #1 – Output bit 0 OFF, continue to instruction 2 after 80ns
	// Flags = 0xFFFFFE (all outputs ON except output bit 0) 
	// OPCODE = CONTINUE (proceed to next instruction after specified delay)
	// Data Field = empty.  This field is ignored for CONTINUE instructions.
	// Delay Count = 80*ns (other valid units are *us, *ms)
	pb_inst (0xFFFFFE, CONTINUE, 0, 80 * ns);

	// Instruction #2 - Branch to "start" (Instruction #0) after 1us
	// Flags = 0x000000 (all output bits are OFF), 
	// OPCODE = BRANCH
	// Data Field = start (the target branch address)
	// Delay Count = 1*us (other valid units are *ns, *ms)
	pb_inst (0x000000, BRANCH, start, 1 * us);

	pb_stop_programming ();	// Finished Sending Instructions
    pb_reset();
	pb_start ();
	pause();
  
	pb_stop();
	pb_close ();
  
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
