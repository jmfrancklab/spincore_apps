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
 * \file subtest.c 
 * \brief PulseBlasterESR-PRO example program. This demonstrates the use of the 
 * subroutine instruction.
 *
 * \ingroup ESRPRO
 */

#include <stdio.h>
#include <stdlib.h>

#define PBESRPRO
#include "spinapi.h"

#define CLOCK_FREQ 400.0	//The value of your clock oscillator in MHz

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
main (int argc, const char **argv)
{
	int start = 0, sub = 0;
	int numBoards;
	double clock_freq = CLOCK_FREQ;

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
		printf("\n");
	}
 	
	printf ("Using clock frequency: %.2fMHz\n\n", clock_freq);
	printf ("BNCs 0-3 will output a train of pulses, each high for 50 ns, followed by ground level for 250 ns.  This pattern will then repeat.\n\n");

	// Tell driver what clock frequency the board uses
	pb_core_clock (clock_freq);

	//Begin pulse program
	pb_start_programming (PULSE_PROGRAM);

	//Instruction format
	//int pb_inst(int flags, int inst, int inst_data, int length)

	// Instruction 0 - continue to inst 1 in 100ns
	start = pb_inst (0x0, CONTINUE, 0, 100.0 * ns);

	// Instruction 1 - Jump to subroutine
	sub = 3;
	pb_inst (0, JSR, sub, 50.0 * ns);

	// Instruction 2 - Branch back to the beginning of the program
	// (instruction 0)
	pb_inst (0x0, BRANCH, start, 100.0 * ns);

	// Instruction 3 - This is the start of the subroutine. Turn on
	// the BNC outputs for 50ns, and then return to the instruction
	// immediately after the JSR instruction that called this. In this
	// pulse program, the next instruction that will be executed is
	// instruction 2.
	pb_inst (ON | 0xF, RTS, 0, 50.0 * ns);

	// End of programming registers and pulse program
	pb_stop_programming ();

	// Trigger the pulse program
    pb_reset();
	pb_start ();

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
