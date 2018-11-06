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
 * \brief This example program tests the arbitrary wavefore generation (AWG) or shape capabilities of the PBDDS-II. 
 * A 2.0 MHz signal that is modulated with a ramp envelope is on Channel 1 and a 10.0 MHz signal that is modulated with
 * a 3 lobe 'sinc' waveform is produced on Channel 2. Both channels are on for 10 microseconds, off for 2 miliseconds
 * and then the pattern is repeated.
 * IRQ0 is enabled.
 *
 * \ingroup ddsII
 */

#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include "spinapi.h"

#define CLOCK_FREQ 75.0  // This value must be 75 MHz for standard PBDDS-II-300 boards

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
#define PHASE0 0
#define PHASE1 1
#define PHASE2 2
#define NO_SHAPE 0
#define USE_SHAPE 1

#define START_LOCATION (0x40000+0x07)
#define FLAG_STATES (0x40000+0x08)

void shape_make_sinc (float *shape_data, int lobes);
void shape_make_sin (float *shape_data);
void shape_make_ramp (float *shape_data);
void shape_make_revramp (float *shape_data);

int detect_boards();
int select_board(int numBoards);

const double pi = 3.1415926;

void pause(void)
{
	printf("Press enter to continue...");
	char buffer = getchar();
	while(buffer != '\n' && buffer != EOF);
	getchar();
}

int 
main(int argc, char *argv[])
{
    int start, isr1;
    int numBoards;
   
   	float shape_data0[1024];		// Waveform for the pulse shape
   	float shape_data1[1024];		// Waveform for the pulse shape
   	float dds_data[1024];		// Waveform for the DDS signal itself (normally a sinewave)
   	

	//Uncommenting the line below will generate a debug log in your current directory
	//that can help debug any problems that you may be experiencing   
	//pb_set_debug(1);

  printf ("Copyright (c) 2010 SpinCore Technologies, Inc.\n\n");
  
	printf("Using SpinAPI library version %s\n", pb_get_version());
	
	if((numBoards = detect_boards()) > 1) { /*If there is more than one board in the system, have the user specify.*/
		select_board(numBoards); /*Request the board numbet to use from the user */
	} 
  
	if (pb_init () != 0) {
		printf ("Error initializing board: %s\n", pb_get_error ());
		pause();
		return -1;
	}
	
   	pb_set_shape_defaults(); //Initialize shape parameters.
   	
   	//Use the functions below to create shape envolopes for RF pulses.
   	shape_make_ramp (shape_data0); //create a ramp envelope using shape_data0
   	shape_make_sinc (shape_data1,3); //create a 3-lobe sinc envelop using shape_data1
   	//shape_make_revramp (shape_data1);
   	//shape_make_spincore (shape_data1);
   	//shape_make_sin (dds_data); //The actual DDS signal can be modified as well
  
    printf("This example program tests the arbitrary wavefore generation (AWG) or shape capabilities of the PBDDS-II.\n\n  This program will produce a 2.0 MHz signal on Channel 1 that is modulated with a ramp envelope."
                 " A 10.0 MHz signal will that is modulated with a 3 lobe 'sinc' waveform is produced on Channel 2. Both channels are on for 10 microseconds, off for 2 miliseconds" 
                 "and then the pattern is repeated.\n\n");
	printf("A TTL logical high signal on the IRQ0 pin will cause an ISR to be performed \nthat pronduces a 2.0 MHz signal on both channels that is on for 200.0 us, off \nfor 200.0 us and repeats this pattern 10,000 times. It will turn both channels \noff for 100.0 us and then returns to the main pulse program.\n\n");
    printf("NOTE: It is important to terminate all signals properly (i.e. with a 50 Ohm\nterminating resistor at the end of your cable).  A reconstructing filter must\nalso be used at the RF outputs.  When viewing the RF signals on an oscilloscope,the oscilloscope should be triggered using a TTL signal\n\n");
    printf("See manual for details at: http://www.spincore.com/\n\n");
    pause();
    printf("\n\n");
    
    pb_core_clock(CLOCK_FREQ); //Set the PB core clock value.
    
/****** THIS SECTION PROGRAMS REGISTERS FOR CHANNEL 1 (DDS0) ******/    
    pb_select_dds(0); //Select DDS0 (this is selected by default.)
    
    pb_start_programming(FREQ_REGS); //Program DDS0's frequency registers. NOTE: Each Channel has 16 available Frequency registers
        pb_set_freq(2.0*MHz); //Program Frequency Register 0.
        pb_set_freq(2.0*MHz); //Program Frequency Register 1.
    pb_stop_programming();

    pb_start_programming(TX_PHASE_REGS); //Program DDS0's phase registers. NOTE: Each Channel has 8 available Phase registers
        pb_set_phase(75.0); //Program Phase Register 0.
        pb_set_phase(70.0); //Program Phase Register 1.
        // PHASE1 offset is introduced to improve the initial RF pulse response.  This phase is used during the "off" time of the RF pulse.
    pb_stop_programming();
 
    pb_set_amp(1.0,0); //Program DDS0's amplitude registers. 
    // NOTE: Each Channel has 4 available amplitude registers
    
    pb_dds_load (shape_data0, DEVICE_SHAPE); //Load the shape envelope into the DDS Shape RAM for DDS0
    //pb_dds_load (dds_data, DEVICE_DDS); //Load the modified DDS signal in the DDS RAM for DDS0
/**********************************************************************/ 
 
/***** THIS SECTION PROGRAMS REGISTERS FOR CHANNEL 2 (DDS1) *****/    
    pb_select_dds(1); //Select DDS1.

    pb_start_programming(FREQ_REGS); //Program DDS1's frequency registers. 
        pb_set_freq(10.0*MHz); //Program Frequency Register 0.
        pb_set_freq(2.0*MHz); //Program Frequency Register 1.
    pb_stop_programming();

    pb_start_programming(TX_PHASE_REGS); //Program DDS1's phase registers. 
        pb_set_phase(75.0); //Program Phase Register 0.
        pb_set_phase(70.0); //Program Phase Register 1.
    pb_stop_programming();

    pb_set_amp(1.0,0); //Program DDS1's amplitude registers.
    
    pb_dds_load (shape_data1, DEVICE_SHAPE); //Load the shape envelope defined by shape_data1 into the DDS Shape RAM for DDS1
/************************************************************************/

//The next section is where the actual pulse program is written:
//The line below shows which parameter corresponds to which register or flag.
/***** SPINCORE_API int pb_inst_dds2_shape(int freq0, int phase0, int amp0, int use_shape0, int dds_en0, int phase_reset0, int freq1, int phase1, int amp1, int use_shape1, int dds_en1, int phase_reset1, int flags, int inst, int inst_data, double length) ****/

	pb_start_programming(PULSE_PROGRAM);  //This line is used to start programming the pulse program.

           start = pb_inst_dds2_shape(FREQ0, PHASE0, AMP0, USE_SHAPE, TX_ENABLE,  NO_PHASE_RESET, FREQ0, PHASE0, AMP0, USE_SHAPE, TX_ENABLE, NO_PHASE_RESET, 0xfff, CONTINUE, 0, 10.0*us);
                   pb_inst_dds2_shape(FREQ0, PHASE1, AMP0, NO_SHAPE, TX_DISABLE, PHASE_RESET, FREQ0, PHASE1, AMP0, NO_SHAPE, TX_DISABLE, PHASE_RESET, 0x000, BRANCH, start, 2.0*ms);

/*********************************************************************************************************
* The section below specifies the interrupt sub routine                                                  *
* The instructions follow the same general structure except that LOOP, END_LOOP and RTI instructions     *
*     are used.  Here you will notice that where Channel 1 uses Frequency register 1 and Channel 2 		   *
*     uses Frequency register 1. Each DDS has it's own Frequency register 1, but in this case both 			 *
*		  requency register 1's are loaded with the same frequency of 2 MHz                                  *
*********************************************************************************************************/               
           isr1 = pb_inst_dds2(FREQ1, PHASE0, AMP0, TX_ENABLE, NO_PHASE_RESET, FREQ1, PHASE0, AMP0, TX_ENABLE, NO_PHASE_RESET, 0xfff, LOOP, 10000, 200.0*us);
                  pb_inst_dds2(FREQ1, PHASE0, AMP0, TX_DISABLE, PHASE_RESET, FREQ0, PHASE0, AMP0, TX_DISABLE, PHASE_RESET, 0x000, END_LOOP, isr1, 200.0*us);
                  pb_inst_dds2(FREQ0, PHASE0, AMP0, TX_DISABLE, PHASE_RESET, FREQ0, PHASE0, AMP0, TX_DISABLE, PHASE_RESET, 0x000, RTI, isr1, 100.0*us);

	pb_stop_programming();  // This line ends the pulse program
 
	pb_write_register (START_LOCATION, 0);
	pb_write_register (FLAG_STATES, 0);

	/***  The section below sets the interrupt masks ***/
	pb_set_isr(0, isr1);               //Program IRQ0 ISR
	pb_set_irq_enable_mask(0x1);       //Interrupt enable mask. 0x1 enables IRQ0.
	pb_set_irq_immediate_mask(0x0);    //Set which IRQs are immediate IRQs (immediately perform ISR)
	
    // Send a software trigger (i.e. pb_start()) to the board to begin execution of the program	
	pb_start();
	printf("Continuing will stop program exectution\n");
    pause();
    pb_stop(); 
    pb_close();
    
	return 0;
}

// Make a sinc shape, for use in generating soft pulses.
void
shape_make_sinc (float *shape_data, int lobes)
{
  int i;

  double x;
  double scale = (double) lobes * (2.0 * pi);
  for (i = 0; i < 1024; i++)
    {
      x = (double) (i - 512) * scale / 1024.0;
      shape_data[i] = sin (x) / x;
      if ((x) == 0.0)
	{
	  shape_data[i] = 1.0;
	}
    }
}


// Make one period of a sinewave
void
shape_make_sin (float *shape_data)
{
  int i;

  for (i = 0; i < 1024; i++)
      shape_data[i] = sin (2.0 * pi * ((float) i / 1024.0));
}


// Make a ramp shape
void shape_make_ramp (float *shape_data)
{
     int i;
     for(i=0;i<1024;i++)
        shape_data[i] = i/1024.0;
}


// Make an reversed ramp shape
void shape_make_revramp (float *shape_data)
{
     int i;
     for(i=0;i<1024;i++)
        shape_data[i] = (1024.0-i)/1024.0;     
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

