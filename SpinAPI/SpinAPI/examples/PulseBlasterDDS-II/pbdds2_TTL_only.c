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
 * \file dds2_excite_test.c
 * \brief The example program tests the TTL outputs of the PBDDS-II only.
 * This program will produce a pulse pattern with all TTL Flag Bits high
 * for 10 microseconds, low for 10 microseconds, and then repeat.
 * IRQ0 is enabled.
 * \ingroup ddsII
 */

#include <stdlib.h>
#include <stdio.h>

#include "spinapi.h"

#define CLOCK_FREQ 75.0

// User friendly names for the control bits
#define FLAG_STATES (0x40000+0x08)
#define START_LOCATION (0x40000+0x07)

void pause(void)
{
	printf("Press enter to continue...");
	char buffer = getchar();
	while(buffer != '\n' && buffer != EOF);
	getchar();
}

int
main (int argc, char *argv[])
{
	int start, i, isr0, isr1, isr2;
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
		
    printf("This example program tests the TTL outputs and the Interrupt functionality of the PBDDS-II.\n\n");
    printf("Here, all parameters related to the analog outputs are set to zero.  The main pulse program will generate a pulse train with all Flag Bits High for 10 us and then LOW for 10 us.\n\n");
    printf("Three interrupt service routines have been programmed:\n");
    printf("  IRQ0: TTL Flags HIGH for 200 us and LOW for 200 us. Repeats 10,000 times\n");
    printf("  IRQ1: TTL Flags HIGH for 100 us and LOW for 300 us. Repeats 10,000 times\n");
    printf("  IRQ2: TTL Flags HIGH for 300 us and LOW for 100 us. Repeats 10,000 times\n\n");
    printf("The ISR will execute when the corresponding IRQ pin receives a logical high\nvoltage\n\n");
    printf("NOTE: It is important to terminate all signals properly (i.e. with a 50 Ohm\nterminating resistor at the end of your cable).\n\n");
    printf("See manual for details at: http://www.spincore.com/\n\n");
    pause();
    printf("\n\n");
 
	pb_set_defaults ();
	pb_core_clock (CLOCK_FREQ);
	
	pb_write_register (FLAG_STATES, 0x0);
	pb_write_register (START_LOCATION, 0);

//The next section is where the actual pulse program is written:
//The line below shows which parameter/argument corresponds to which register or flag.
/***** SPINCORE_API int pb_inst_dds2(int freq0, int phase0, int amp0, int dds_en0, int phase_reset0, int freq1, int phase1, int amp1, int dds_en1, int phase_reset1, int flags, int inst, int inst_data, double length) ****/

  pb_start_programming (PULSE_PROGRAM);	//This line is used to start programming the pulse program.

/********************************************************************************************************
* Each piece of the pulse program is specified by a pb_inst_dds2(...) command                           *
* Here, all parameters related to the analog outputs (the first ten) are set to zero.                   *
*                                                                                                       *
* The 11th parameter sets the TTL Flag Bits.  0xfff is a hexadecimal value that corresponds to the      *
*       TTL flags. 0xfff equals 1111 1111 1111 which means that all 12 bits are HIGH (i.e., 1)          *
* The 12th parameter is the Instruction.  The first line is CONTINUE which does not require a DATA      *
*       field so it is set to zero. The second line contains a BRANCH instruction and the "start" in    *
*       the DATA field (the 13th parameter) tells the PulseBlaster core to return to the line labeled   *
*       with the "start" integer.                                                                       *
* The 14th parameter is length, or time, of the current instruction. In this example both instructions  *
*       last for 10 us, so you will see the TTL Flags HIGH for 10 us and then LOW for 10 us.            *
********************************************************************************************************/

    start = pb_inst_dds2 (0,0,0,0,0,0,0,0,0,0, 0xfff, CONTINUE, 0, 10.0 * us);
    pb_inst_dds2 (0,0,0,0,0,0,0,0,0,0, 0x000, BRANCH, start, 10.0 * us);


/*********************************************************************************************************
* The section below specifies the interrupt sub routines                                                 *
* The instructions follow the same general structure except that LOOP, END_LOOP and RTI instructions     *
*     are used.                                                                                          *
*********************************************************************************************************/
    isr0 =
    pb_inst_dds2 (0,0,0,0,0,0,0,0,0,0, 0x040, LOOP, 10000, 200.0 * us);
    pb_inst_dds2 (0,0,0,0,0,0,0,0,0,0, 0x000, END_LOOP, isr0, 200.0 * us);
    pb_inst_dds2 (0,0,0,0,0,0,0,0,0,0, 0x000, RTI, isr0, 100.0 * us);
    isr1 =
    pb_inst_dds2 (0,0,0,0,0,0,0,0,0,0, 0x040, LOOP, 10000, 100.0 * us);
    pb_inst_dds2 (0,0,0,0,0,0,0,0,0,0, 0x000, END_LOOP, isr1, 300.0 * us);
    pb_inst_dds2 (0,0,0,0,0,0,0,0,0,0, 0x000, RTI, isr1, 100.0 * us);
    isr2 =
    pb_inst_dds2 (0,0,0,0,0,0,0,0,0,0, 0x040, LOOP, 10000, 300.0 * us);
    pb_inst_dds2 (0,0,0,0,0,0,0,0,0,0, 0x000, END_LOOP, isr2, 100.0 * us);
    pb_inst_dds2 (0,0,0,0,0,0,0,0,0,0, 0x000, RTI, isr2, 100.0 * us);
    
    pb_stop_programming ();	// This line ends the pulse program
/*********** END PULSE PROGRAM **************************************************************************/    

	/***  The section below sets the interrupt masks ***/
	pb_set_isr (0, isr0);		//Program IRQ0 ISR
	pb_set_isr (1, isr1);		//Program IRQ1 ISR
	pb_set_isr (2, isr2);		//Program IRQ2 ISR
	pb_set_irq_enable_mask (0x7);	//Interrupt enable mask. 0x7 => bits 111.  This enables all three IRQs.
	pb_set_irq_immediate_mask (0x0);	//Set which IRQs are immediate IRQs (immediately perform ISR)
  
  
    // Send a software trigger (i.e. pb_start()) to the board to begin execution of the program	
	pb_start();
	printf("Continuing will stop program exectution\n");
    pause();
	
    pb_stop(); 
    pb_close();

	return 0;
}

int
detect_boards()
{
	int numBoards;

	numBoards = pb_count_boards();	/*Count the number of boards */

    if (numBoards <= 0) {
		printf("No Boards were detected in your system. Verify that the board is correctly powered and connected.\n\n");
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
