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
 * \file example2_8bit.c
 * \brief PulseBlasterESR-Pro-II high speed memory output Example program
 *
 * This program loads a custom pulse sequence onto the PulseBlasterESR-Pro-II
 * board and then triggers it.  This is a high-speed output function that will
 * not work for any other PulseBlaster or RadioProcessor board.
 *
 * This specific file is intended for PBESR-Pro-II designs with 8 output flag bits.
 * The program will not work properly for 24-bit designs.
 * For more information visit http://www.spincore.com/products/PulseBlasterESR-PRO-II/
 * \ingroup PROII
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "spinapi.h"

#define CLOCK 250.0 

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
main(int argc, char **argv)
{
    int numBoards;

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
	
    printf("This example program demonstrates the ability to change flag outputs every\nsingle clock cycle. Channel 1 is on for 12 ns, with channel 2 going on for 4 ns\nduring this time. Channels 2 and 3 alternate on and off every 4 ns 8 times.\nAll channels are off for 200 ns, then program repeats.\n\n");
    printf("NOTE: It is important to terminate all signals properly (i.e. with a 50 Ohm\nterminating resistor at the end of your cable).\n\n");
    printf("See manual for details at: http://www.spincore.com/\n\n");
	pause();
    printf("\n\n");
    
	//setup the clock frequency
	pb_core_clock(CLOCK);
  
	//The following two lines are used for PBESR-Pro-II designs in place of
	//   pb_start_programming(...) and pb_stop_programming().
	pb_outp(0,0); //Reset the board
	pb_outp(4,0); //Reset the memory counter
	  
	//*** Pulse program loading begins here ***
	/* Max length of pulse sequence is 262.144 us
	*  The leftmost bit is Channel 7, followed by Channel 6, 
	*    Channel 5, ... , Channel 1, and the rightmost bit is Channel 0. 
	*/
	pb_inst_hs8("00000001",4.0*ns);
	pb_inst_hs8("00000011",4.0*ns);   
	pb_inst_hs8("00000101",4.0*ns);
	pb_inst_hs8("00000010",4.0*ns);
	pb_inst_hs8("00000100",4.0*ns);
	pb_inst_hs8("00000010",4.0*ns);
	pb_inst_hs8("00000100",4.0*ns);
	pb_inst_hs8("00000010",4.0*ns);
	pb_inst_hs8("00000100",4.0*ns); 
  
	//Nothing for 200 ns
	pb_inst_hs8("00000000",200.0*ns);

	//Trigger the board
	printf("Beginning pulse generation\n");
	pb_outp(1,0);

	//Signal the end of communication
	pb_close();
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
