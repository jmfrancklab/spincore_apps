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
 * \brief The example program tests the analog outputs of the PBDDS-II.
 * This program will produce a 1 MHz signal on the oscilloscope that is on
 * for 10 microseconds, off for 10 microseconds on both channels, and then repeat this pattern.
 * Specifically, this program demonstrates how to change the default "return to" states
 * of the TTL flags (each flag can be programmed to retun to low or high voltage when
 * the PulseBlaster Core is RESET from either a hardware or software reset signal).
 * IRQ0 is enabled.
 * \ingroup ddsII
 */

#include <stdlib.h>
#include <stdio.h>

#include "spinapi.h"

#define CLOCK_FREQ 75.0
#define FLAG_STATES (0x40000+0x08)
#define START_LOCATION (0x40000+0x07)
 
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
#define AMP4 4
#define PHASE0 0

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
* This example demonstrates the ability to change the "return-to" states  *
*      of the TTL Flag bits                                               *
***************************************************************************/
int
main (int argc, char *argv[])
{
	int start, i, isr1;
	int numBoards, choice;

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
  
    printf("This example program tests the analog and TTL outputs of the PBDDS-II.\n\n  This program will produce a 1.0 MHz signal on both channels that is on for 10 microseconds, off for 10 microseconds, and then repeats this pattern.\n\n");
	printf("Channel 1 and Channel 2 will alternate being on and off.\n\n");
    printf("This example shows the ability to change the 'return-to' states of the TTL\nflag bits with only one simple write to the board.  Currently they are set to\nreturn to 0xA5A which corresponds to the bit pattern 1010 0101 1010 (leftmost\nbit is most significant bit, i.e. FLAG 11). ");
    printf("This means that when the Pulse-\nBlaster Core is in a STOPPED state, the flag bits will return to the specified\noutput pattern.\n\n");
    printf("NOTE: Once the return to TTL flag state register has been changed, it will\nretain that changed value until it is changed again, or the board is powered\noff. It is important to terminate all signals properly (i.e. with a 50 Ohm\nterminating resistor at the end of your cable).  A reconstructing filter must\nalso be used at the RF outputs. When viewing the RF signals on an oscilloscope,\nthe oscilloscope should be triggered using a TTL signal\n\n");
    printf("See manual for details at: http://www.spincore.com/\n\n");
    pause();
    printf("\n\n");
	
	pb_core_clock (CLOCK_FREQ);		//Set the PB core clock value.
	pb_write_register (FLAG_STATES, 0x000); //Set the initial flag states to 0x000

/****** THIS SECTION PROGRAMS REGISTERS FOR CHANNEL 1 (DDS0) ******/
	pb_select_dds (0);		//Select DDS0 (this is selected by default.)

	pb_start_programming (FREQ_REGS);	//Program DDS0's frequency registers. NOTE: Each Channel has 16 available Frequency registers
	pb_set_freq (1.0 * MHz);	//Program Frequency Register 0.
	pb_set_freq (2.0 * MHz);	//Program Frequency Register 1.
	pb_stop_programming ();

	pb_start_programming (TX_PHASE_REGS);	//Program DDS0's phase registers. NOTE: Each Channel has 8 available Phase registers
	pb_set_phase (270.0);
	pb_stop_programming ();

	pb_set_amp (0.2, 0);		//Program DDS0's amplitude registers.  /** THIS IS WHAT YOU MUST CHANGE TO ADJUST THE AMPLITUDE OF CHANNEL 1 TO MATCH CHANNEL 2 **/
	pb_set_amp (0.5, 1);
	pb_set_amp (0.7, 2);
	pb_set_amp (1.0, 3);
  // NOTE: Each Channel has 4 available amplitude registers
/**********************************************************************/

/***** THIS SECTION PROGRAMS REGISTERS FOR CHANNEL 2 (DDS1) *****/
	pb_select_dds (1);		//Select DDS1.

	pb_start_programming (FREQ_REGS);	//Program DDS1's frequency registers. 
	pb_set_freq (1.0 * MHz);	//Program Frequency Register 0.
	pb_set_freq (2.0 * MHz);	//Program Frequency Register 1.
	pb_stop_programming ();

	pb_start_programming (TX_PHASE_REGS);	//Program DDS1's phase registers. 
	pb_set_phase (0.0);
	pb_stop_programming ();

	pb_set_amp (0.2, 0);		//Program DDS1's amplitude registers.
	pb_set_amp (0.5, 1);
	pb_set_amp (0.7, 2);
	pb_set_amp (1.0, 3);
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
*        Amplitude register 0 (which I changed to be 0.85 in order to match the amplitude of channel 2) *
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

    start =
    pb_inst_dds2 (FREQ0, PHASE0, AMP3, TX_ENABLE, NO_PHASE_RESET, FREQ0,
		  PHASE0, AMP0, TX_DISABLE, PHASE_RESET, 0xfff, CONTINUE, 0,
		  10.0 * us);
    pb_inst_dds2 (FREQ0, PHASE0, AMP0, TX_DISABLE, PHASE_RESET, FREQ0, PHASE0,
		AMP3, TX_ENABLE, NO_PHASE_RESET, 0x000, BRANCH, start,
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


/* The line below shows how to change the return to state for the TTL flag bits once the PB Core has been reset
 *  either by hardware reset of software reset (pb_stop() function).
 *  The Flag State Register is located at address 0x40000 + 0x08  */
 	pb_write_register (FLAG_STATES, 0xA5A);	// You may choose any 12 bit number to represent the 12 TTL Flags

	pb_write_register (START_LOCATION, 0);
 
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
		printf("No Boards were detected in your system. Verify that the board is properly powered and connected.\n\n");
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
