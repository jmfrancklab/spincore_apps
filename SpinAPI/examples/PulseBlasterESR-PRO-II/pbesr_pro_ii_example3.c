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
 * \file example3_8bit.c
 * \brief PulseBlasterESR-Pro-II high speed memory output Example program
 *
 * For more information visit: http://www.spincore.com/products/PulseBlasterESR-PRO-II/
 *
 * This is the program from the PulseBlasterESR-Pro-II Manual (see "Programming
 * the PulseBlasterESR-Pro-II" -> "Example Use of C Functions". This program 
 * loads a custom pulse sequence onto the PulseBlasterESR-Pro-II board and then 
 * triggers it.  This is a high-speed output function that will not work for 
 * any other PulseBlaster or RadioProcessor board.  It is only intended for 
 * 8-bit versions of PBESSR-PRO-II, but can be modified for 24-bit.
 * For more information visit: http://www.spincore.com/products/PulseBlasterESR-PRO-II/
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
	
	printf("This example program will generate the pulse pattern shown in the\nPulseBlasterESR-Pro-II Manual (see 'Introduction' -> 'Product Overview'). The\ncode is equivalent to that found in the 'Programming the PulseBlasterESR-Pro-II' -> 'Example Use of C Functions' section.\n\n");
	printf("NOTE: It is important to terminate all signals properly (i.e. with a 50 Ohm\nterminating resistor at the end of your cable).\n\n");
	printf("See manual for details at: http://www.spincore.com/\n\n");
	pause();
	printf("\n\n");	 

	//Setup the clock frequency
	pb_core_clock(CLOCK);

	//Reset the board
	pb_outp(0,0); 
  
	//Reset the memory counter
	pb_outp(4,0); 
  
	//*** Pulse program loading begins here ***
	// The leftmost bit is Channel 8, followed by Channel 7, 
	//   Channel 6, ... , Channel 1, and the rightmost bit is Channel 0. 
  
	pb_inst_hs8("00001001",4.0*ns);
	pb_inst_hs8("00000001",4.0*ns);
	pb_inst_hs8("00000000",8.0*ns);
	pb_inst_hs8("00000001",4.0*ns);
	pb_inst_hs8("00000011",4.0*ns);
	pb_inst_hs8("00000111",4.0*ns);
	pb_inst_hs8("00001101",4.0*ns); 
	pb_inst_hs8("00001000",4.0*ns);
	pb_inst_hs8("00000011",4.0*ns);
	pb_inst_hs8("00000001",4.0*ns);
	pb_inst_hs8("00000011",4.0*ns); 
	pb_inst_hs8("00000001",8.0*ns);   
  
	//Nothing for 480ns
	pb_inst_hs8("00000000",480*ns);

	//Trigger the board
	printf("Beginning pulse generation\n");
	pb_outp(1,0);

	//Signal the end of communication
	pb_close();
  
	//For convenience, pause here and display a message
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
