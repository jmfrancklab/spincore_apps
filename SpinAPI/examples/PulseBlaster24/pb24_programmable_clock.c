/* Copyright (c) 2010 SpinCore Technologies, Inc.
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
 * \file pb24_programmable_clock.c
 * PulseBlaster24 Programmable Clock Example
 *
 * \brief This program demonstrates use of the user programmable clock outputs.
 * This program will only work with firmware 13-9.  Other firmwares do not have
 * this custom behavior.  This example generates a clock signal with a 5 MHz
 * frequency and a 10% duty cycle on the four clock pins.  Each clock pin will
 * be offset by a different amount.  For more details, see Appendix II of the
 * PulseBlaster USB manual.
 * \ingroup pb24
 */

#include <stdio.h>
#include <stdlib.h>

#define PB24
#include "spinapi.h"

int detect_boards();
int select_board(int numBoards);

void pause(void)
{
	printf("Press enter to continue...");
	char buffer = getchar();
	while(buffer != '\n' && buffer != EOF);
	getchar();
}

int main()
{
	int start, status;
	int numBoards;
	int firmware;

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

	// check to see if the firmware is 13-09
	firmware = pb_get_firmware_id();
	if( firmware != 0x0D09 ) {
		printf("Error: This program only works with firmware 13-9.\n");
		printf("This example does not apply to your board.\n");
		pause();
		return -1;
	}

	printf("Clock frequency: 100.00MHz\n\n");
	
	printf("User Programmable Clock Example Program\n");
	printf("Only works with USB PulseBlaster firmware 13-9.\n\n");
	printf("    This example generates a clock signal with a 5 MHz frequency\n");
	printf("    and a 10%% duty cycle on the four clock pins.  Each clock pin\n");
	printf("    will be offset by a different amount.\n\n");

	// Tell the driver what clock frequency the board has (in MHz)
	pb_core_clock(100.0);
	
	// Channel 0 - 200 ns period - 20 ns high - 20 ns offset
	pb_set_pulse_regs(0, 200.0 * ns, 20.0 * ns, 20.0 * ns);
	
	// Channel 1 - 200 ns period - 20 ns high - 20 ns offset
	pb_set_pulse_regs(1, 200.0 * ns, 20.0 * ns, 40.0 * ns);
	
	// Channel 2 - 200 ns period - 20 ns high - 20 ns offset
	pb_set_pulse_regs(2, 200.0 * ns, 20.0 * ns, 60.0 * ns);
	
	// Channel 3 - 200 ns period - 20 ns high - 20 ns offset
	pb_set_pulse_regs(3, 200.0 * ns, 20.0 * ns, 80.0 * ns);

	printf("The clock pins should now be running.\n");
	pause();

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
		     "is firmly secured in the PCI slot.\n\n");
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

	return choice;
}
