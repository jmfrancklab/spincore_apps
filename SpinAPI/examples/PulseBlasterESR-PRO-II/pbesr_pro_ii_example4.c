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
 * \file example4_24bit.c
 * \brief PulseBlasterESR-Pro-II high speed memory output Example program
 *
 *
 * This program loads a custom pulse sequence onto the PulseBlasterESR-Pro-II
 * board and then triggers it.  This is a high-speed output function that will
 * not work for any other PulseBlaster or RadioProcessor board.
 *
 * This specific file is intended for PBESR-Pro-II designs with 24 output flag bits.
 * The program will not work properly for 8-bit designs. It is intended to test
 * the maximum pulse-sequence length for design 9-4b.
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

int main(int argc, char **argv)
{
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
	
    printf("This example program tests the maximum pulse-sequence length (32.768 us) of\nthe 9-4b PBESR-Pro-II design. Channel 1 outputs a 42.144 us pulse followed by\nalternating 20 us pulses on Channels 2 and 3. All channels are off for 12 us,\nthen the program repeats indefinitely.\n\n");
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
	/* Max length of pulse sequence is 32.768 us
	*  The leftmost bit is Channel 23, followed by Channel 22, 
	*    Channel 21, ... , Channel 1, and the rightmost bit is Channel 0. 
	*/
	pb_inst_hs24("000000000000000000000001",4.768*us);
	pb_inst_hs24("000000000000000000000010",2.0*us);   
	pb_inst_hs24("000000000000000000000100",2.0*us);
	pb_inst_hs24("000000000000000000000010",2.0*us);
	pb_inst_hs24("000000000000000000000100",2.0*us);
	pb_inst_hs24("000000000000000000000010",2.0*us);
	pb_inst_hs24("000000000000000000000100",2.0*us);
	pb_inst_hs24("000000000000000000000010",2.0*us);
	pb_inst_hs24("000000000000000000000100",2.0*us); 
  
	//Nothing for 12 us
	pb_inst_hs24("00000000",12.0*us);

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
