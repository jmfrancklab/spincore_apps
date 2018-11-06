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
 * \file longdelaytest.c
 * \brief PulseBlasterESR-PRO example program
 *
 * The following program tests the functionality of the long delay opcode. The
 * long delay opcode determines what the delay value is by multipling the given
 * delay value by the data field. Thus, this program will output a pulse train
 * with period (100ns*long_delay)
 *
 * This program takes two optional command-line arguments.
 * The first is the clock frequency, the default is 400MHz.  
 * The second is the number of delay loops in the pulse train, the default is 5.  
 *
 * The largest value for the delay field of pb_inst is 850ns.
 * For longer delays, use the LONG_DELAY instruction.  The maximum value
 * for the data field of the LONG_DELAY is 1048576.  Even longer delays can
 * be achieved using the LONG_DELAY instruction inside of a loop.
 *
 * \ingroup ESRPRO
 */

#include <stdio.h>
#include <stdlib.h>

#define PBESRPRO
#include "spinapi.h"

#define CLOCK_FREQ 400.0	//The value of your clock oscillator in MHz
#define DELAY_LOOP 5

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
	int start = 0, delay_loop = DELAY_LOOP;
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
 	
	if (argc > 2) {
		delay_loop = atoi (argv[2]);
	}
	else {
		printf("Please enter the number of loops for the long delay instruction.\n"
               "The minimum number of loops for this program to run is 3.\n"
		       "The resulting period will be 200*(number of loops)ns.\n");
		printf("Number of long delay loops: ");
		scanf("%d",&delay_loop);
        printf("\n");
        while (delay_loop<3)
        {
           printf("The number of loops has to be greater that 2.\n");
           printf("Number of long delay loops: ");
		   scanf("%d",&delay_loop);
         }
	}

  printf ("Clock frequency: %.2fMHz\n\n", clock_freq);
  printf ("BNCs 0-3 should output a 50%% duty cycle square wave with period %uns\n\n", delay_loop * 100 * 2);

  // Tell driver what clock frequency the board uses
  pb_core_clock (clock_freq);

  //Begin pulse program
  pb_start_programming (PULSE_PROGRAM);

  //Instruction format
  //int pb_inst(int flags, int inst, int inst_data, int length)

  // Instruction 0 - continue to inst 1 in (100ns*delay_loop)
  start = pb_inst (ON | 0xF, LONG_DELAY, delay_loop, 100.0 * ns);

  // Instruction 1 - continue to instruction 2 in (100ns*(delay_loop-1))
  pb_inst (0x0, LONG_DELAY, delay_loop - 1, 100.0 * ns);

  // Instruction 2 - branch to start
  pb_inst (0x0, BRANCH, start, 100.0 * ns);

  // End of programming registers and pulse program
  pb_stop_programming ();

  // Trigger pulse program
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
