/* Copyright (c) 2014 SpinCore Technologies, Inc.
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
 * \file DirectCapture.c
 *
 * \brief This program demonstrates how to use the Direct Ram Capture feature of the 
 * RadioProcessor.
 * NOTE: This feature is only enabled in the PCI RadioProcessor with Firmware Revisions
 * 10-14 and up and USB RadioProcessors with Firmware Revisions 12-5 and up.
 * \ingroup RP
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "spinapi.h"

//Defines for easy reading.
#define RAM_SIZE (16*1024)
#define BOARD_STATUS_IDLE 0x3
#define DO_TRIGGER 1
#define NO_TRIGGER 0
#define ADC_FREQUENCY 75.0

//The number of points your board will acquire.
//For PCI boards, the full ram size is 16384 points.  For USB boards it is 4*16384 points.
#define NUMBER_POINTS 4*16384

//The number of scans to perform (with signal averaging enabled.)
//If you use signal averaging, please make sure that there is phase coherence between scans.
#define NUMBER_SCANS 1

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
	int i, numBoards;
	short data[NUMBER_POINTS], data_imag[NUMBER_POINTS];
    int idata[NUMBER_POINTS],idata_imag[NUMBER_POINTS];
	double wait_time;
	int start;
  
	//These variables are used for the Title Block in Felix  
	char *program_type = "DirectCapture";
	char title_string[412];

	//Uncommenting the line below will generate a debug log in your current
	//directory that can help debug any problems that you may be experiencing   
	//pb_set_debug(1); 
  
	printf("Using SpinAPI library version %s\n", pb_get_version());
	  
	if((numBoards = detect_boards()) > 1) { /*If there is more than one board in the system, have the user specify.*/
		select_board(numBoards); /*Request the board numbet to use from the user*/
	}
	
	if (pb_init () != 0) {
		printf ("Error initializing board: %s\n", pb_get_error ());
		pause();
		return -1;
	}

	pb_set_defaults ();
	pb_core_clock (ADC_FREQUENCY);	//Set the PulseBlaster Core Operating frequency.
	pb_overflow (1, 0);		// Reset the overflow counters.
	pb_scan_count (1);		// Reset scan counter.

	pb_set_radio_control (RAM_DIRECT);	//Enable direct ram capture.

	pb_set_num_points (NUMBER_POINTS);	//This is the number of points that we are going to be capturing.

	wait_time = 1000.0 * (NUMBER_POINTS) / (ADC_FREQUENCY * 1e6);	// Time in ms

	pb_start_programming (PULSE_PROGRAM);
	start =
    pb_inst_radio_shape (0, 0, 0, 0, 0, 0, NO_TRIGGER, 0, 0, 0x02, LOOP,
			 NUMBER_SCANS, 1.0 * us);
	  pb_inst_radio_shape (0, 0, 0, 0, 0, 0, DO_TRIGGER, 0, 0, 0x01, END_LOOP,
		       start, wait_time * ms);
	  pb_inst_radio_shape (0, 0, 0, 0, 0, 0, NO_TRIGGER, 0, 0, 0x02, STOP, 0,
		       1.0 * us);
	pb_stop_programming ();

	printf ("Performing direct ram capture...\n");

  pb_reset();
	pb_start ();

	printf ("Waiting for the data acquisition to complete.\n");

	while (pb_read_status () != BOARD_STATUS_IDLE) { //Wait for the board to complete execution.
      pb_sleep_ms (100);
    }

	pb_get_data_direct(NUMBER_POINTS,data);

	pb_unset_radio_control (RAM_DIRECT);	//Disable direct ram capture.

	pb_close ();
	
	//pb_write_ascii ("direct_data.txt", NUMBER_POINTS, 1.0, idata, idata_imag);
	
	FILE* fp_ascii = fopen("direct_data.txt","w");
   
   for(i=0;i<NUMBER_POINTS;++i)
   {
    fprintf(fp_ascii,"%d\n",data[i]);
   } 
   fclose(fp_ascii);

	//The spectrometer frequency does not matter in a direct ram capture. Using 1.0 MHz for
	//proper file format.
  
	//Create Title Block String
	strcpy (title_string,"Program = ");
	strcat (title_string,program_type);
	
	for(i=0;i<NUMBER_POINTS; ++i) 
   {
       idata[i] = data[i];
       idata_imag[i] = data_imag[i];
   }  
      
	pb_write_felix ("direct_data.fid", title_string, NUMBER_POINTS, ADC_FREQUENCY * 1e6, 1.0,
		  idata, idata_imag);

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
