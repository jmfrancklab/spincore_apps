/*   Copyright (c) 2009 SpinCore Technologies, Inc.
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
 * \file ESR_loop_test.c
 * \brief PulseBlasterESR Example Program
 *
 * The following program tests the functionality of the loop instruction.
 * It takes two optional command-line arguments.
 * The first is the clock frequency, the default is 250MHz.  
 * The second is the number of loops, the default is 3 loops.  
 * 
 * BNCs 0-3 will output a pulse train with period 100ns. The number of pulses
 * in this train will be determined by the number of loops used. This pulse
 * train will be followed by ground level for 400ns, after which the entire
 * program will repeat.
 *
 * \ingroup ESR
 */

#include <stdio.h>
#include <stdlib.h>

#define PBESR
#include "spinapi.h"

#define NUM_LOOPS 3

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
	int numBoards;
	int start = 0, loop = 0, num_loops = NUM_LOOPS;
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
 	
	if (argc > 2) {
		num_loops = atoi (argv[2]);
	}
	else {
		printf("Please enter the number of loops for the loop instruction.\n");
		printf("Number of loops: ");
		scanf("%d",&num_loops);
        printf("\n");
	}
	
  printf ("Clock frequency: %.2lf MHz\n\n", clock_freq);
  printf("BNCs 0-3 will output %d successive pulses, each with a period of 100ns,\n"
		 "followed by ground level for 400ns and then the program will repeat\n\n", num_loops);

  // Tell driver what clock frequency the board uses
  pb_core_clock (clock_freq);

  //Begin pulse program
  pb_start_programming (PULSE_PROGRAM);

  //Instruction format
  //int pb_inst(int flags, int inst, int inst_data, int length)

  // Instruction 0 - continue to inst 1 in 200ns
  start = pb_inst (0x0, CONTINUE, 0, 200.0 * ns);

  // Instruction 1 - Beginning of Loop (Loop num_loop times). Continue to
  // next instruction in 50ns
  loop = pb_inst (0xF, LOOP, num_loops, 50.0 * ns);

  // Instruction 2 - End of Loop.  Return to beginning of loop (instruction 1)
  // or continue to next instruction in 50ns
  pb_inst (0x0, END_LOOP, loop, 50.0 * ns);

  // Instruction 3 - branch to start
  pb_inst (0x0, BRANCH, start, 200.0 * ns);

  // End of programming registers and pulse program
  pb_stop_programming ();

  // Trigger the pulse program
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
