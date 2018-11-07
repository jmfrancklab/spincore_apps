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
 * \brief The example program tests the analog and TTL outputs of the PBDDS-II.
 * It also shows the ability to write multiple pulse programs and then choose
 * the starting location with one write to the board.
 * This program will produce a 2 MHz signal on the Channel 1 that is on for 
 * 40 microseconds and off for 10 microseconds, a 2 MHz signal on Channel 2 that
 * is off for 40 us and on for 10 us, and then repeat this pattern.  The output 
 * will be different if a different starting address is chosen.
 * IRQ0 is enabled.
 * \ingroup ddsII
 */

#include <stdlib.h>
#include <stdio.h>
#include "spinapi.h"

#define CLOCK_FREQ 75.0

// User friendly names for the control bits
#define TX_ENABLE 1
#define TX_DISABLE 0
#define PHASE_RESET 1
#define NO_PHASE_RESET 0
#define DO_TRIGGER 1
#define NO_TRIGGER 0
#define FREQ0 0
#define FREQ1 1
#define AMP0 0
#define AMP1 1
#define AMP2 2
#define AMP3 3
#define PHASE0 0
#define PHASE1 1
#define PHASE2 2

void printTable (void);

int detect_boards();
int select_board(int numBoards);

void pause(void)
{
	printf("Press enter to continue...");
	char buffer = getchar();
	while(buffer != '\n' && buffer != EOF);
	getchar();
}

/**************************************************************************
* This example demonstrates the ability to write multiple pulse programs  *
*      at one time, then choose the stating address by writing to a       *
*      register                                                           *
***************************************************************************/
int
main (int argc, char *argv[])
{
	int start, i;
	int start1, start2, start3, start4;
	int isr1;
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
	
    printf("This example program tests the analog and TTL outputs of the PBDDS-II.\n\n  The program output varies depending on which program starting address is used\nin the corresponding C file.\n\n");
    printf("This example demonstrates the ability to write multiple pulse programs and \nthen choose the starting location with just one write to the board. See the\ncorresponding C file for details\n\n");
	printf("A logical high voltage on the IRQ0 pin will cause an ISR to be performed that\nproduces a 2.0 MHz signal on both channels that is on for 200.0 us, off for\n200.0 us and repeats this pattern 10,000 times. It will turn both channels off\nfor 100.0 us and then returns to the main pulse program.\n\n");
    printf("NOTE: Once the starting address has been changed, it will retain that changed\nvalue until it is changed again, or the board is powered off. It is important\nto terminate all signals properly (i.e. with a 50 Ohm terminating resistor at\nthe end of your cable).  A reconstructing filter must also be used at the RF\noutputs.  When viewing the RF signals on an oscilloscope, the oscilloscope\nshould be triggered using a TTL signal\n\n");
    printf("See manual for details at: http://www.spincore.com/\n\n");
    pause();
    printTable();
  
	pb_core_clock (75.0);		//Set the PB core clock value.

/****** THIS SECTION PROGRAMS REGISTERS FOR CHANNEL 1 (DDS0) ******/
	pb_select_dds (0);		//Select DDS0 (this is selected by default.)

	pb_start_programming (FREQ_REGS);	//Program DDS0's frequency registers. NOTE: Each Channel has 16 available Frequency registers
	pb_set_freq (1.0 * MHz);	//Program Frequency Register 0.
	pb_set_freq (2.0 * MHz);	//Program Frequency Register 1.
	pb_stop_programming ();

	pb_start_programming (TX_PHASE_REGS);	//Program DDS0's phase registers. NOTE: Each Channel has 8 available Phase registers
	pb_set_phase (270.0); //Program Phase Register 0.
	pb_set_phase (90.0); //Program Phase Register 1.
	pb_set_phase (85.0); //Program Phase Register 2.
	pb_stop_programming ();

	pb_set_amp (1.0, AMP0);	//Program DDS0's amplitude registers.  /** THIS IS WHAT YOU MUST CHANGE TO ADJUST THE AMPLITUDE OF CHANNEL 1 TO MATCH CHANNEL 2 **/
	  // NOTE: Each Channel has 4 available amplitude registers
	pb_set_amp (0.7, AMP1);
	pb_set_amp (0.5, AMP2);
	pb_set_amp (0.2, AMP3);
/**********************************************************************/

/***** THIS SECTION PROGRAMS REGISTERS FOR CHANNEL 2 (DDS1) *****/
	pb_select_dds (1);		//Select DDS1.

	pb_start_programming (FREQ_REGS);	//Program DDS1's frequency registers. 
	pb_set_freq (1.0 * MHz);	//Program Frequency Register 0.
	pb_set_freq (2.0 * MHz);	//Program Frequency Register 1.
	pb_stop_programming ();

	pb_start_programming (TX_PHASE_REGS);	//Program DDS1's phase registers. 
	pb_set_phase (0.0); //Program Phase Register 0.
	pb_set_phase (0.0); //Program Phase Register 1
	pb_set_phase (90.0); //Program Phase Register 2.
	pb_stop_programming ();

	pb_set_amp (1.0, AMP0);	//Program DDS1's amplitude registers.
	pb_set_amp (0.7, AMP1);
	pb_set_amp (0.5, AMP2);
	pb_set_amp (0.2, AMP3);
/************************************************************************/

//The next section is where the actual pulse program is written:
//The line below shows which parameter/argument corresponds to which register or flag.
/***** SPINCORE_API int pb_inst_dds2(int freq0, int phase0, int amp0, int dds_en0, int phase_reset0, int freq1, int phase1, int amp1, int dds_en1, int phase_reset1, int flags, int inst, int inst_data, double length) ****/

	pb_start_programming (PULSE_PROGRAM);	//This line is used to start programming the pulse program.

/********************************************************************************************************
* Each piece of the pulse program is specified by a pb_inst_dds2(...) command                           *
* The first line says that for Channel 1 use:                                                           *
*        Frequency register 0 (which was programmed to be 1 MHz)                                        *
*        Phase register 0 (which was programmed to be 0)                                                *        
*        Amplitude register 0 (which is 0.85)                                                           *
*        Enable Channel 1                                                                               *
*        Do not reset the phase of channel 1                                                            *
* The first line also says for Channel 2 use:                                                           *
*        Frequency register 0 (which was programmed to be 1 MHz)                                        *
*        Phase register 0 (which was programmed to be 0)                                                *
*        Amplitude register 0 (which was programmed to be 1.0)                                          *
*        Do not enable Channel                                                                          *
*        Reset the phase of channel 1                                                                   *
* 0xfff is a hexadecimal value that corresponds to the TTL flags fff equals 1111 1111 1111 which means  *
*       that all 12 bits are HIGH                                                                       *
* The specific instruction for this line is CONTINUE which does not require a DATA field so it is set   *
*       to zero.                                                                                        *
* All of this takes place for 10us                                                                      *
* The second line does the same thing except Channel 1 and Channel 2 are switched, the TTL flags are    *
*       now all LOW, and the instruction branches back to the first line (this also happens for 10us)   *
********************************************************************************************************/

  start1 =
    pb_inst_dds2 (FREQ0, PHASE0, AMP0, TX_ENABLE, NO_PHASE_RESET, FREQ0,
		  PHASE2, AMP0, TX_DISABLE, PHASE_RESET, 0xfff, CONTINUE, 0,
		  10.0 * us);
  pb_inst_dds2 (FREQ0, PHASE2, AMP0, TX_DISABLE, PHASE_RESET, FREQ0, PHASE1,
		AMP3, TX_ENABLE, NO_PHASE_RESET, 0x000, BRANCH, start1,
		10.0 * us);

  start2 =
    pb_inst_dds2 (FREQ1, PHASE0, AMP1, TX_ENABLE, NO_PHASE_RESET, FREQ0,
		  PHASE2, AMP0, TX_DISABLE, PHASE_RESET, 0xfff, CONTINUE, 0,
		  20.0 * us);
  pb_inst_dds2 (FREQ0, PHASE2, AMP0, TX_DISABLE, PHASE_RESET, FREQ0, PHASE1,
		AMP2, TX_ENABLE, NO_PHASE_RESET, 0x000, BRANCH, start2,
		10.0 * us);

  start3 =
    pb_inst_dds2 (FREQ0, PHASE0, AMP1, TX_ENABLE, NO_PHASE_RESET, FREQ0,
		  PHASE2, AMP0, TX_DISABLE, PHASE_RESET, 0xfff, CONTINUE, 0,
		  30.0 * us);
  pb_inst_dds2 (FREQ0, PHASE2, AMP0, TX_DISABLE, PHASE_RESET, FREQ1, PHASE1,
		AMP1, TX_ENABLE, NO_PHASE_RESET, 0x000, BRANCH, start3,
		10.0 * us);

  start4 =
    pb_inst_dds2 (FREQ1, PHASE0, AMP3, TX_ENABLE, NO_PHASE_RESET, FREQ0,
		  PHASE2, AMP0, TX_DISABLE, PHASE_RESET, 0xfff, CONTINUE, 0,
		  40.0 * us);
  pb_inst_dds2 (FREQ0, PHASE2, AMP0, TX_DISABLE, PHASE_RESET, FREQ1, PHASE1,
		AMP0, TX_ENABLE, NO_PHASE_RESET, 0x000, BRANCH, start4,
		10.0 * us);
/*********************************************************************************************************
* The section below specifies the interrupt sub routine                                                  *
* The instructions follow the same general structure except that LOOP, END_LOOP and RTI instructions     *
*     are used.  Here you will notice the error where Channel 1 uses Frequency register 1, but Channel 2 *
*     uses Frequency register 0, so they are not the same frequency                                      *
*********************************************************************************************************/
  isr1 =
    pb_inst_dds2 (FREQ1, PHASE0, AMP0, TX_ENABLE, NO_PHASE_RESET, FREQ1,
		  PHASE0, AMP0, TX_ENABLE, NO_PHASE_RESET, 0xfff, LOOP, 10000,
		  200.0 * us);
  pb_inst_dds2 (FREQ1, PHASE0, AMP0, TX_DISABLE, PHASE_RESET, FREQ0, PHASE0,
		AMP0, TX_DISABLE, PHASE_RESET, 0x000, END_LOOP, isr1,
		200.0 * us);
  pb_inst_dds2 (FREQ0, PHASE0, AMP0, TX_DISABLE, PHASE_RESET, FREQ0, PHASE0,
		AMP0, TX_DISABLE, PHASE_RESET, 0x000, RTI, isr1, 100.0 * us);
  pb_stop_programming ();	// This line ends the pulse program


  // The line below chooses which of the above locations to begin at.
  // Starting location is located at address 0x40000 + 0x07
#define START_LOCATION (0x40000+0x07)
  pb_write_register (START_LOCATION, start4);	// You may choose from start1, start2, start3, or start4

 #define FLAG_STATES (0x40000+0x08)
 pb_write_register (FLAG_STATES, 0);


 /***  The section below sets the interrupt masks ***/
  pb_set_isr (0, isr1);		//Program IRQ0 ISR
  pb_set_irq_enable_mask (0x1);	//Interrupt enable mask. 0x1 enables IRQ0.
  pb_set_irq_immediate_mask (0x0);	//Set which IRQs are immediate IRQs (immediately perform ISR as opposed to waiting for the current instruction to finish before executing the ISR)

  // Send a software trigger (i.e. pb_start()) to the board to begin execution of the program	
  pb_start();
  printf("Continuing will stop program exectution\n");
  pause();
  pb_stop ();

  return 0;
}

void printTable()
{
    system("cls");
    printf("\n\n");
    printf("        |         Channel 1         |         Channel 2         |\n");
    printf("------------------------------------------------------------------\n"); 
    printf(" start1 | time on: 10 us            | time on: 10 us            |\n");
    printf("        | frequency: 1 MHz          | frequency: 1 MHz          |\n");
    printf("        | phase: 0 degrees          | phase: 90 degrees         |\n");
    printf("        | amplitude: 1.0            | amplitude: 0.2            |\n") ; 
    printf("------------------------------------------------------------------\n");
    printf(" start2 | time on: 20 us            | time on: 10 us            |\n");
    printf("        | frequency: 2 MHz          | frequency: 1 MHz          |\n");
    printf("        | phase: 0 degrees          | phase: 90 degrees         |\n");
    printf("        | amplitude: 0.7            | amplitude: 0.5            |\n") ; 
    printf("------------------------------------------------------------------\n");
    printf(" start3 | time on: 30 us            | time on: 10 us            |\n");
    printf("        | frequency: 1 MHz          | frequency: 2 MHz          |\n");
    printf("        | phase: 0 degrees          | phase: 90 degrees         |\n");
    printf("        | amplitude: 0.7            | amplitude: 0.7            |\n") ; 
    printf("------------------------------------------------------------------\n");
    printf(" start4 | time on: 40 us            | time on: 10 us            |\n");
    printf("        | frequency: 2 MHz          | frequency: 2 MHz          |\n");
    printf("        | phase: 0 degrees          | phase: 90 degrees         |\n");
    printf("        | amplitude: 0.2            | amplitude: 1.0            |\n") ;
    printf("------------------------------------------------------------------\n\n");
    pause();
    printf("\nDefault is start4");
    printf("\n\n");
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
