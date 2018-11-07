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
 * \file pb-Quad_Core250_example2.c
 * \brief PulseBlaster Quad-Core Example 2
 * This program is an example to show how to generate different patterns on each of the 4 cores.
 * \ingroup QuadCore
 */

#include <stdio.h> 
#include <stdlib.h>

#include "spinapi.h"

#define CLOCK 250.0  //This is the internal ON-CHIP frequency which will differ from the external ON-BOARD oscillator

//User Friendly Defines:
#define CORE0 0x1
#define CORE1 0x2
#define CORE2 0x4
#define CORE3 0x8
#define ALL_CORES 0xF

void printLicense(void);
int detect_boards();
int select_board(int numBoards);

int 
main (void)
{
    int numBoards;
	
	printLicense();
	
	//Uncommenting the line below will generate a debug log in your current
	//directory that can help debug any problems that you may be experiencing   
	//pb_set_debug(1); 
  
	printf("Using SpinAPI library version %s\n", pb_get_version());
	  
	if((numBoards = detect_boards()) > 1) { /*If there is more than one board in the system, have the user specify.*/
		select_board(numBoards); /*Request the board numbet to use from the user*/
	}
	
	if (pb_init () != 0) {
		printf ("Error initializing board: %s\n", pb_get_error ());
		system("pause");
		return -1;
	}
	
	printf ("Clock frequency: %.2f MHz\n\n", CLOCK);
	printf ("Example 2\n---------\n");
	printf ("This program is an example to show how to generate different patterns on each\nof the 4 cores.\n\n");
	printf ("Be sure to use cables of the same length for each channel and be sure \neach one is terminated with a 50 Ohm resistor.\n\n");

	// Tell the driver what clock frequency the board has (in MHz)
	pb_core_clock (CLOCK);
  
	printf("Continuing will begin execution of the pulse program\n"); 
	system("pause"); 
  
/********* Program Core3 ******************/
	// Select Which Core to program
	pb_select_core(CORE3);
	pb_start_programming (PULSE_PROGRAM);

	pb_4C_inst (1, 20.0 * ns);
	pb_4C_inst (0, 20.0 * ns);
	pb_4C_inst (1, 20.0 * ns);
	pb_4C_inst (0, 20.0 * ns);
	pb_4C_inst (1, 20.0 * ns);
	pb_4C_inst (0, 20.0 * ns);
	pb_4C_inst (1, 20.0 * ns);
	pb_4C_inst (0, 20.0 * ns);
	pb_4C_stop ();

	pb_stop_programming ();

/******** Program Core2 ************************/
	pb_select_core(CORE2);
	pb_start_programming (PULSE_PROGRAM);

	pb_4C_inst (1, 20.0 * ns);
	pb_4C_inst (0, 20.0 * ns);
	pb_4C_inst (1, 20.0 * ns);
	pb_4C_inst (0, 20.0 * ns);
	pb_4C_inst (1, 20.0 * ns);
	pb_4C_inst (0, 60.0 * ns);
	pb_4C_stop ();

	pb_stop_programming ();
  
/********** Program Core1 ***************************/
	pb_select_core(CORE1);
	pb_start_programming (PULSE_PROGRAM);

	pb_4C_inst (1, 20.0 * ns);
	pb_4C_inst (0, 20.0 * ns);
	pb_4C_inst (1, 20.0 * ns);
	pb_4C_inst (0, 100.0 * ns);
	pb_4C_stop ();

	pb_stop_programming ();

/********** Program Core0 ****************************/
	pb_select_core(CORE0);
	pb_start_programming (PULSE_PROGRAM);
	pb_4C_inst (1, 20.0 * ns);
	pb_4C_inst (0, 140.0 * ns);
	pb_4C_stop ();

	pb_stop_programming ();


	pb_start();
	printf("\n");
	system ("pause");
	pb_close ();
  
	return 0;
}

void printLicense(void)
{
     printf("Copyright (c) 2009 SpinCore Technologies, Inc.\n");
     printf(" http://www.spincore.com\n\n");
     printf("This software is provided 'as-is', without any express or implied warranty.\n");
     printf("In no event will the authors be held liable for any damages arising from the\n"); 
     printf("use of this software.\n");
     printf("\n");
     printf("Permission is granted to anyone to use this software for any purpose,\n");
     printf("including commercial applications, and to alter it and redistribute it\n");
     printf("freely, subject to the following restrictions:\n");
     printf("\n");
     printf("1. The origin of this software must not be misrepresented; you must not\n");
     printf("claim that you wrote the original software. If you use this software in a\n");
     printf("product, an acknowledgment in the product documentation would be appreciated\n");
     printf("but is not required.\n");
     printf("2. Altered source versions must be plainly marked as such, and must not be\n");
     printf("misrepresented as being the original software.\n");
     printf("3. This notice may not be removed or altered from any source distribution.\n\n");
     system("pause");
     system("cls");
     return;
}

int
detect_boards()
{
	int numBoards;

	numBoards = pb_count_boards();	/*Count the number of boards */

    if (numBoards <= 0) {
		printf("No Boards were detected in your system. Verify that the board is firmly secured in the PCI slot.\n\n");
		system("PAUSE");
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
