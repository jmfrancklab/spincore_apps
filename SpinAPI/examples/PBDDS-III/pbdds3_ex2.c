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
 * \file pbdds3_ex2.c
 * \brief Example 2 for the PulseBlasterDDS
 *
 * This program makes use of all available instructions (except WAIT)
 *
 * On the TX channel:
 * There will be a single period of a 1MHz sine wave, followed by a 1us gap.
 * This pattern will be repeated 2 more times followed by a long (5ms) gap,
 * after which the pattern will repeat again.
 *
 * On the RX channel:
 * There will be a 1 MHz sine wave, which will be turned off for short
 * periods of time and have its phase changed several times. See the
 * pulse program below for details.
 *
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
main (void)
{
	int start, loop, sub;
	int numBoards, i;

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
	printf ("On the TX channel: \n There will be a single period of a 1MHz sine wave, followed by a 1 us gap.\n"
            "This pattern will be repeated 2 more times followed by a long (5ms) gap, after which the pattern\n"
			"will repeat again. \n\nOn the RX channel: \n There will be a 1 MHz sine wave, which will be turned\n"
			"off for short periods of time and have its phase changed several times. See pbdds2_ex2.c for details.\n\n");

	// Tell driver what clock frequency the board has
	pb_core_clock (CLOCK);

	//Program the frequency registers
	pb_start_programming (FREQ_REGS);
	for(i=0; i<16;++i) {
		pb_set_freq ((i+1.0) * MHz); // Set register i
	}
	pb_stop_programming ();

	//Program the RX phase registers (DAC_OUT_1) [Units in degrees]
	pb_start_programming (PHASE_REGS_1);
	for(i=0; i<16;++i) {
		pb_set_phase (i*22.5); // Set register i
	}
	pb_stop_programming ();

	//Program the TX phase registers (DAC_OUT_0 and DAC_OUT_2)
	pb_start_programming (PHASE_REGS_0);
	for(i=0; i<16;++i) {
		pb_set_phase (i*22.5); // Set register i
	}
	pb_stop_programming ();

	//Begin pulse program
	pb_start_programming (PULSE_PROGRAM);

	//For PulseBlasterDDS boards, the pb_inst function is translated to the
	//pb_inst_tworf() function, which is defined as follows:
	//pb_inst_tworf(freq, tx_phase, tx_output_enable, rx_phase, rx_output_enable, flags, inst, inst_data, length);

	sub = 5;			// Since we are going to jump forward in our program, we need to 
						// define this variable by hand.  Instructions start at 0 and count up

	// Instruction 0 - Jump to Subroutine at Instruction 5 in 1us
	start = pb_inst (0, 0, TX_ANALOG_OFF, 0, RX_ANALOG_ON, 0x1FF, JSR, sub, 1 * us);

	// Loop. The next two instructions make up a loop which will be repeated
	// 3 times.
	// Instruction 1 - Beginning of Loop (Loop 3 times).  Continue to next instruction in 1us
	loop = pb_inst (0, 0, TX_ANALOG_OFF, 0, RX_ANALOG_OFF, 0x0, LOOP, 3, 1 * us);
  
	// Instruction 2 - End of Loop.  Return to beginning of loop or continue to next instruction in 1us
		 pb_inst (0, 0, TX_ANALOG_ON, 0, RX_ANALOG_OFF, 0x0, END_LOOP, loop, 1 * us);

	// Instruction 3 - Stay here for (5*1ms) then continue to Instruction 4
		 pb_inst (0, 0, TX_ANALOG_OFF, 0, RX_ANALOG_ON, 0x0, LONG_DELAY, 5, 1 * ms);

	// Instruction 4 - Branch to "start" (Instruction 0) after 1us
		// This has the effect of looping the entire program indefinitely.
		 pb_inst (0, 0, TX_ANALOG_OFF, 0, RX_ANALOG_ON, 0x0, BRANCH, start, 1 * us);

	// Subroutine. This subroutine is called by using the JSR instruction
	// and specifying the address of instruction 5. (As is done in instruction 1)
	// Instruction 5 - Reset phase and continue to next instruction in 2us
		 pb_inst (0, 4, TX_ANALOG_OFF, 8, RX_ANALOG_ON, 0x200, CONTINUE, 0, 2 * us);

	// Instruction 6 - Return from Subroutine after 2us
		 pb_inst (0, 8, TX_ANALOG_OFF, 8, RX_ANALOG_ON, 0x0, RTS, 0, 2 * us);

	pb_stop_programming ();

	//Trigger the pulse program
    pb_reset();
	pb_start ();
	printf("\n");
	pause();

	// Release control of the PulseBlasterDDS-III board
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
