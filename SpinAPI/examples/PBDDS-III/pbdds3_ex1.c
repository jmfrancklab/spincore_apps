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
 * \file pbdds3_ext1.c
 * \brief Example 1 for the PulseBlasterDDS
 *
 * This program outputs a 1MHz sine wave on both TX and RX channels.
 * The TX Channel cycles between being on and off with a period
 * of 8us.
 * The TX and RX channels are set to have a 90 degree phase offset.
 * \ingroup ddsIII
 */

#include <stdio.h>
#include <stdlib.h>

#define PBDDS
#include "spinapi.h"

#define CLOCK 100.0

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
main (int argc, char **argv)
{
	int start, numBoards;
	int status;

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

	printf ("Clock frequency: %.2lf MHz\n\n", CLOCK);
	printf("This program outputs a 1 MHz sine wave on both TX and RX channels.\n"
		   "The TX Channel cycles between being on and off with a period of 8us.\n"
		   "The TX and RX channels are set to have a 90 degree phase offset. \n\n");

	// Tell the driver what clock frequency the board has
	pb_core_clock (CLOCK);

	// Program the frequency registers
	pb_start_programming (FREQ_REGS);
	pb_set_freq (1.0 * MHz);	// Register 0
	pb_set_freq (2.0 * MHz);	// Register 1
	pb_stop_programming ();

	// Program RX phase registers (DAC_OUT_1) [Units in degrees]
	pb_start_programming (PHASE_REGS_1);
	pb_set_phase (0.0);		// Register 0
	pb_set_phase (90.0);		// Register 1
	pb_stop_programming ();

	// Program the TX phase registers (DAC_OUT_0 and DAC_OUT_2)
	pb_start_programming (PHASE_REGS_0);
	pb_set_phase (0.0);		// Register 0
	pb_set_phase (180.0);		// Register 1
	pb_stop_programming ();

	// Send the pulse program to the board
	pb_start_programming (PULSE_PROGRAM);

	//For PulseBlasterDDS boards, the pb_inst function is translated to the
	//pb_inst_tworf() function, which is defined as follows:
	//pb_inst_tworf(freq, tx_phase, tx_output_enable, rx_phase, rx_output_enable, flags, inst, inst_data, length);

	//Instruction 0 - Continue to instruction 1 in 2us
	///Output frequency in freq reg 0 to both TX and RX channels
	//Set all TTL output lines to logical 1
	start = pb_inst (0, 1, TX_ANALOG_ON, 0, RX_ANALOG_ON, 0x1FF, CONTINUE, 0, 2.0 * us);

	//Instruction 1 - Continue to instruction 2 in 4us
	//Output frequency in freq reg 0 RX channels, TX channel is disabled
	//Set all TTL outputs to logical 0
	pb_inst (0, 1, TX_ANALOG_OFF, 0, RX_ANALOG_ON, 0x000, CONTINUE, 0, 4.0 * us);

	//Instruction 2 - Branch to "start" (Instruction 0) in 2us
	//Output frequency in freq reg 0 to both TX and RX channels
	//Set all TTL output lines to logical 1
	pb_inst (0, 1, TX_ANALOG_ON, 0, RX_ANALOG_ON, 0x000, BRANCH, start, 2.0 * us);

	pb_stop_programming ();

	// Trigger the pulse program
    pb_reset();
	pb_start ();

	// Retreive the status of the current board. This will be 0x04 since
	// the pulse program is a loop and will continue running indefinitely.
	status = pb_read_status ();
	printf ("status: 0x%.2x\n", status);
	printf (pb_status_message ());
	printf ("\n");
	pause();
  
	pb_stop();

	// Release Control of the PulseBlasterDDS Board
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
	
	return 0;
}
