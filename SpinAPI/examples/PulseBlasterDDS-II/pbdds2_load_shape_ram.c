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
 * \brief This example program shows the ability to modify the PBDDS-II DDS Shape
 * RAM while the PulseBlaster core is running.  Execute this program while dds2_awg.exe
 * Is running and the shape envelopes will change to the new programmed envelope.
 *
 * \ingroup ddsII
 */

#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include "spinapi.h"

#define CLOCK_FREQ 75.0  // This value must be 75 MHz for standard PBDDS-II-300 boards


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
    int numBoards;
   
   	float shape_data0[1024];		// Waveform for the pulse shape
   	float shape_data1[1024];		// Waveform for the pulse shape
   	//float dds_data[1024];		// Waveform for the DDS signal itself (normally a sinewave)
   	
	//Uncommenting the line below will generate a debug log in your current directory
	//that can help debug any problems that you may be experiencing   
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
   	
   	//Use the following functions to create an arbitrary envelope for your RF signal
   	shape_make_ramp (shape_data0); //calculate a ramp shape and store in shape_data0
   	shape_make_revramp (shape_data1); //create a reveresed ramp shape and store in shape_data1

    printf("This program shows how the DDS-II Shape RAM data for the PBDDS-II can be written "
	       "'on-the-fly'.\n\n  Simply execute this program while the dds2_awg.exe program is "
		   "running. The envelope shape of the signal on channel 1 will change to a ramp, a "
		   "linear increase in amplitude from 0 to 1, and the envelope shape of the signal on "
		   "channel 2 will change to a reverse ramp, a linear decrease in amplitude from 1 to "
		   "0.\n\n");
    
    pb_core_clock(CLOCK_FREQ); //Set the PB core clock value.
	pause();
    
/****** THIS SECTION PROGRAMS REGISTERS FOR CHANNEL 1 (DDS0) ******/    
    pb_select_dds(0); //Select DDS0 (this is selected by default.)
    
    pb_start_programming(TX_PHASE_REGS);
     pb_set_phase(75.0);
    pb_stop_programming();
    
    pb_dds_load (shape_data0, DEVICE_SHAPE); //Th 
    //pb_dds_load (dds_data, DEVICE_DDS); //The shape of the actual DDS signal can be modified as well
/**********************************************************************/ 
 
/***** THIS SECTION PROGRAMS REGISTERS FOR CHANNEL 2 (DDS1) *****/    
    pb_select_dds(1); //Select DDS1.
    pb_dds_load (shape_data1, DEVICE_SHAPE);
/************************************************************************/

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

