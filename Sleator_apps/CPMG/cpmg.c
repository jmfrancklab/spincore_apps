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

/*Contributors: Spincore Technologies.
 *				Tycho Sleator
 *				Philip Christoffersen: 
 *					-Added checks for proper memory allocation
 *					-Intialized real and imaginary arrays to 0
 *					-Changed pulse program so that power amplifier de-blanks 
 *						and ringsdown during tau period to allow for proper 
 *						impelmentation of tau
 *					-Cleaned up and reformatted program to match 
 *						Single Pulse NMR structure
 *                  -Ensured that number of points is always a power of 2
 *					-Re-implemented segmented scanning so that a single point
 * 						can be taken per echo
 *					-Added a least squares regression function to calculate T2
 */
 
/**
 * cpmg.h
 * Modified from CPMG.c
 *  
 *	This program is used to control the RadioProcessor series of boards in conjuction with the iSpin setup.
 *	It generates an initial RF pulse (90 degree pulse) of variable frequency, amplitude, phase and duration.
 *	It then, optionally, acquires the NMR response of the 90 degree pulse. 
 *	It then generates another RF pulse (180 degree) pulse of the same frequency and amplitude,
 *		90 degrees out of phase with the first pulse, and of specified duration.
 *	It then acquires the acquires the NMR response (echo) of the 180 degree pulse. 
 *  It repeats this sequence for the specified number of echoes.
 *	It can also only perform acquistion for a specified number of points per echo.
 *	In this mode it can calculate a value for T2.
 *	
 * SpinCore Technologies, Inc.
 * www.spincore.com
 * $Date: 2017/07/11 11:00:00 $
 */
 
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "spinapi.h"
#include "cpmg.h"

#ifdef _MSC_VER
#define inline __inline
#endif

int main (int argc, char **argv){
	SCANPARAMS *myScan;
	int *real, *imag;
	
	printProgramTitle();
    
    
    //
    //Process Arguments
    //
    
    allocInitMem((void *) &myScan, sizeof(SCANPARAMS));
    	
	int processStatus = processArguments (argc, argv, myScan);
	if (processStatus != 0){
		system("pause");
		return processStatus;
	}
	
	if (myScan->debug){
		pb_set_debug(1);
	}
	
	
	//
	// Configure Board
	//
	
	//Set board defaults.
	if (configureBoard (myScan) < 0){
		printf ("Error: Failed to configure board.\n");
		system("pause");
		return CONFIGURATION_FAILED;
	}
	
	// Allocate data arrays
	allocInitMem((void *) &real, myScan->num_points * sizeof(int));
	allocInitMem((void *) &imag, myScan->num_points * sizeof(int));
	
	
	//
	//Print Parameters
	//
	
	printScanParams (myScan);
	
	//Calculate and print total time
	double repetition_delay_ms = myScan->repetition_delay * 1000;
	double total_time = (myScan->scan_time + repetition_delay_ms) * myScan->num_scans;
	if(total_time < 1000){
		printf ("Total Experiment Time   : %lf ms\n\n", total_time);
	}
	else if(total_time < 60000){
		printf ("Total Experiment Time   : %lf s\n\n", total_time/1000);	
	}
	else if(total_time < 3600000){
		printf ("Total Experiment Time   : %lf minutes\n\n", total_time/60000);	
	}
	else{
		printf ("Total Experiment Time   : %lf hours\n\n", total_time/3600000);	
	}
	printf ("Waiting for the data acquisition to complete... \n\n");
	
	
	//
	//Program the board.
	//
	
	if (programBoard (myScan) != 0){
		printf ("Error: Failed to program board.\n");
		system("pause");
		return PROGRAMMING_FAILED;
	}
	
	
	///
    /// Trigger Pulse Program
    ///
	
	pb_reset();
    pb_start();
	
	
    //
    // Count Scans
    //
	
	int scan_count = 0; // Scan count is not deterministic. Reported scans may be skipped or repeated (actual scan count is correct)
	do{      
		pb_sleep_ms (total_time/myScan->num_scans);
		
		if (scan_count != pb_scan_count(0)){
			scan_count = pb_scan_count(0);
			printf("Current Scan: %d\n", scan_count);
		}
	} while (!(pb_read_status() & STATUS_STOPPED));	//Wait for the board to complete execution.
	
	printf("\nExecution complete \n\n\n");
	
	
	///
    /// Read Data From RAM
    ///
    
	if( pb_get_data (myScan->num_points, real, imag) < 0 ){ // For PCI boards, can read any size <= 16384
		printf("Failed to get data from board.\n");
		system("pause");
		return DATA_RETRIEVAL_FAILED;
	}
	
	//If segemented scan, perform an exponential fit to find T2
	if(myScan->num_echo_points > 0){
		//Calculate peaks and magnitudes (this allocates memory so make sure the memory gets deallocated properly)
		double* mag = calcMag(real, imag, myScan->num_points);
		double* peaks = findPeaks(mag, myScan);
		
		//Calculate T2
		double sec_per_peak = (myScan->tau + myScan->p180_time + myScan->tau)/1000000;
		double T2 = calcT2(myScan->num_echoes, sec_per_peak, peaks);
		
		printf("T2: %f seconds\n(Calculated using least squares regression)\n\n\n", T2);
		
		//Deallocate memory
		free(mag);
		free(peaks);
	}
	
	
	//
	// Write Output Files
	//
	
	writeDataToFiles(myScan, real, imag);				  
	
	
	//
	// End Program
	//
	
	pb_stop();
	
	pb_close();
	
	free(myScan);
	free(imag);
	free(real);
	

	return 0;
}


//
//
// FUNCTIONS
//
//

int allocInitMem (void **array, int size){
	//Allocate memory
	*array = (void *) malloc (size);
	
	//Verify allocation
	if( *array == NULL ){
		printf("Memory allocation failed.\n");
		system("pause");
		return ALLOCATION_FAILED;
	}
	
	//Initialize allocated memory to zero
	memset ((void *) *array, 0, size);
	
	return 0;
}


//
// Parameter Reading
//

int processArguments (int argc, char *argv[], SCANPARAMS * scanParams){
	//Check for valid argument count
	if (argc != NUM_ARGUMENTS + 1){
		printProperUse ();
		system("pause");
		return INVALID_NUM_ARGUMENTS;
    }

	
	//
	//Process arguments
	//
	
	scanParams->file_name           = argv[1];
	
	//Board Parameters
	scanParams->board_num           = atoi (argv[2]);
	scanParams->deblank_bit         = (unsigned short) atoi (argv[3]);
	scanParams->deblank_bit_mask    = (1 << scanParams->deblank_bit);
	scanParams->debug               = (unsigned short) atoi (argv[4]);
	
	//Frequency Parameters
	scanParams->ADC_frequency       = atof (argv[5]);
	scanParams->SF                  = atof (argv[6]);
	scanParams->SW                  = atof (argv[7]);
	
	//Pulse Parameters
  	scanParams->num_echoes          = (unsigned int) atoi (argv[8]);
	scanParams->amplitude           = atof (argv[9]);  
	scanParams->p90_time            = atof (argv[10]);
	scanParams->p90_phase           = atof (argv[11]);
	scanParams->p180_time           = atof (argv[12]);
	scanParams->p180_phase          = scanParams->p90_phase + 90;
	
	//Acquisition Parameters
	scanParams->include_90          = (unsigned short) atoi (argv[13]);
	scanParams->bypass_fir          = (unsigned short) atoi (argv[14]);
	scanParams->num_echo_points     = (unsigned short) atoi (argv[15]);
	scanParams->num_scans           = (unsigned int) atoi (argv[16]);
	scanParams->tau                 = atof (argv[17]);
	
	//Delay Parameters
	scanParams->deblank_delay       = atof (argv[18]);
	scanParams->transient_delay	    = atof (argv[19]);
	scanParams->repetition_delay    = atof (argv[20]);
	
	//Set acquisition times
	scanParams->a90_time            = scanParams->tau - scanParams->transient_delay;
	scanParams->a180_time           = 2 * scanParams->tau;
	
	//Do not acquire 90 degree pulse if the power amplifier must be on the whole time
	double deblank_delay_us = 1000 * scanParams->deblank_delay;
	if((scanParams->tau <= deblank_delay_us + scanParams->transient_delay) & scanParams->num_echo_points == 0){
		scanParams->keep_90_deblank = 1;
		printf("| Notice:                                                                      |\n"); 
		printf("|     The total delay from de-blanking and ringdown are larger than tau.       |\n");
		printf("|     The power amplifier will be de-blanked during 90 degree acquisition.     |\n");
		printf("|                                                                              |\n");
	}
  	

	//Check parameters
	if (verifyArguments (scanParams)){
		return INVALID_ARGUMENTS;
	}
	
	return 0;
}

int verifyArguments (SCANPARAMS * scanParams){
	if (pb_count_boards () <= 0){
       printf("No RadioProcessor boards were detected in your system.\n");
	   system("pause");
	   return BOARD_NOT_DETECTED;
    }
	
	if (pb_count_boards () > 0 && scanParams->board_num > pb_count_boards () - 1){
		printf ("Error: Invalid board number. Use (0-%d).\n",pb_count_boards () - 1);
		return -1;
	}
	
	pb_select_board(scanParams->board_num);
	
	if (pb_init ()){
		printf ("Error initializing board: %s\n", pb_get_error ());
		return -1;
	}
  
	if (scanParams->amplitude < 0.0 || scanParams->amplitude > 1.0){
		printf ("Error: Amplitude value out of range.\n");
		return -1;
	}

	if(scanParams->SF < 0.0 || scanParams->SF > 100.0){
		printf("Spectrometer Freq. must be between 0 and 100 MHz\n");
		return -1;
	}

	if(scanParams->SW < 0.0 || scanParams->SW > 10000.0){
		printf("Invalid Spectral Width\n");
		return -1;
	}
	
	if(scanParams->p90_time < 0.065){
		printf("P1 time must be > 0.065 us\n");
		return -1;
 	}

	if(scanParams->p180_time < 0.065){
		printf("P2 time must be > 0.065 us\n");
		return -1;
	}
	
	if (scanParams->transient_delay < 0.065){
		printf ("Error: Transient delay is too small to work with board.\n");
		return -1;
	}
	
	if(scanParams->tau < 0.065){
		printf("tau must be > 0.065 us\n");
		return -1;
	}
	
	if (scanParams->num_scans < 1){
		printf ("Error: There must be at least one scan.\n");
		return -1;
	}
	
	if (scanParams->deblank_delay < 0){
	    printf("Invalid de-blanking delay.\n");
		return -1;
	}
  
	if (scanParams->deblank_bit > 3 || scanParams->deblank_bit < 0){
    	printf("Invalid de-blanking bit. Value must be between 0 and 5.\n");
		return -1;
  	}
	
  	if (scanParams->include_90 > 1 || scanParams->include_90 < 0){
    	printf("Invalid value for include_90. Must be 1 (include) or 9 (don't include)\n");
		return -1;
	}
	
	if (scanParams->num_echoes < 1){
		printf("Invalid value for num_echoes. At least 1 echo is needed for CPMG");
		return -1;
	}
	
  	return 0;
}


//
// Terminal Output
//

void printProgramTitle(char* title){
	//Create a title block of 80 characters in width
	printf ("|------------------------------------------------------------------------------|\n");
	printf ("|                                                                              |\n");
	printf ("|                                     CPMG                                     |\n");
	printf ("|                                                                              |\n");
	printf ("|                       Using SpinAPI Version:  %.8s                       |\n", pb_get_version());
	printf ("|                                                                              |\n");
	printf ("|------------------------------------------------------------------------------|\n");
}

inline void printProperUse (){
	printf ("Incorrect number of arguments, there should be %d. Syntax is:\n", NUM_ARGUMENTS);
	printf ("--------------------------------------------\n");
	printf ("Variable                       Units\n");
	printf ("--------------------------------------------\n");
	printf ("Filename.......................Filename to store output\n");
	printf ("Board Number...................(0-%d)\n", pb_count_boards () - 1);
	printf ("De-blanking TTL Flag Bit.......(0-5)\n");
	printf ("Debugging Output...............(1 for enabled, 0 for disabled)\n");
	printf ("ADC Frequency..................ADC sample frequency\n");
	printf ("Spectrometer Frequency.........MHz\n");
	printf ("Spectral Width.................kHz\n");
	printf ("Number of Echoes...............(1 or greater)\n");
	printf ("Amplitude......................Amplitude of excitation pulse (0.0 to 1.0)\n");
	printf ("90 Degree Pulse Time...........us\n");
	printf ("90 Degree Pulse Phase..........degrees\n");
	printf ("180 Degree Pulse Time..........us\n");
	printf ("Include 90 Degree Pulse FID....(0-1)");
	printf ("Bypass FIR.....................(1 to bypass, or 0 to use)\n");
	printf ("Number of Scans................(1 or greater)\n");
	printf ("Tau............................us\n");
	printf ("De-blanking Delay..............Delay between de-blanking and the TX Pulse (ms)\n");
	printf ("Transient Delay................us\n");
	printf ("Repetition Delay...............s\n");
}

void printScanParams (SCANPARAMS * myScan){
	//Create a table of 80 characters in width
	char buffer[80] = {0};
	printf ("|-----------------------------  Scan  Parameters  -----------------------------|\n");
	printf ("|------------------------------------------------------------------------------|\n");
	printf ("| Filename: %-66s |\n",											myScan->file_name);
	printf ("|                                                                              |\n");
	printf ("| Board Parameters:                                                            |\n");
	sprintf(buffer, "%d", myScan->board_num);
	printf ("|      Board Number                   : %-38s |\n", buffer);
	sprintf(buffer, "%d", myScan->deblank_bit);
	printf ("|      De-blanking TTL Flag Bit       : %-38s |\n", buffer);
	printf ("|      Debugging                      : %-38s |\n", (myScan->debug != 0) ? "Enabled":"Disabled");
	printf ("|                                                                              |\n");
	printf ("| Frequency Parameters:                                                        |\n");
	sprintf(buffer, "%.4f MHz", myScan->ADC_frequency);
	printf ("|      ADC Frequency                  : %-38s |\n", buffer);
	sprintf(buffer, "%.4f MHz", myScan->SF);
	printf ("|      Spectrometer Frequency         : %-38s |\n", buffer);
	sprintf(buffer, "%.4f kHz", myScan->SW);
	printf ("|      Spectral Width                 : %-38s |\n", buffer);
	printf ("|                                                                              |\n");
	printf ("| Pulse Parameters:                                                            |\n");
	printf ("|      Include 90 Degree Pulse        : %-38s |\n", (myScan->include_90 != 0) ? "Enabled":"Disabled");
	sprintf(buffer, "%d", myScan->num_echoes);
	printf ("|      Number of Echoes               : %-38s |\n", buffer);
	sprintf(buffer, "%.4f", myScan->amplitude);
	printf ("|      Amplitude                      : %-38s |\n", buffer);
	sprintf(buffer, "%.4f us", myScan->p90_time);
	printf ("|      90 Degree Pulse Time           : %-38s |\n", buffer);
	sprintf(buffer, "%.4f degrees", myScan->p90_phase);
	printf ("|      90 Degree Pulse Phase          : %-38s |\n", buffer);
	sprintf(buffer, "%.4f us", myScan->p180_time);
	printf ("|      180 Degree Pulse Time          : %-38s |\n", buffer);
	sprintf(buffer, "%.4f degrees", myScan->p180_phase);
	printf ("|      180 Degree Pulse Phase         : %-38s |\n", buffer);
	printf ("|                                                                              |\n");
	printf ("| Acquistion Parameters:                                                       |\n");
	printf ("|      Bypass FIR                     : %-38s |\n", (myScan->bypass_fir != 0) ? "Enabled":"Disabled");
	sprintf(buffer, "%d", myScan->num_echo_points);
	printf ("|      Number of Echo Points          : %-38s |\n", buffer);
	sprintf(buffer, "%d", myScan->num_points);
	printf ("|      Number of Points               : %-38s |\n", buffer);
	sprintf(buffer, "%d", myScan->num_scans);
	printf ("|      Number of Scans                : %-38s |\n", buffer);
	sprintf(buffer, "%.4f us", myScan->tau);
	printf ("|      Tau                            : %-38s |\n", buffer);
	sprintf(buffer, "%.4f us", myScan->a90_time);
	printf ("|      90 Degree Acquisition Time     : %-38s |\n", buffer);
	sprintf(buffer, "%.4f us", myScan->a180_time);
	printf ("|      180 Degree Acquisition Time    : %-38s |\n", buffer);
	sprintf(buffer, "%.4f ms", myScan->scan_time);
	printf ("|      Total Acquisition Time         : %-38s |\n", buffer);
	printf ("|                                                                              |\n");
	printf ("| Delay Parameters:                                                            |\n");
	sprintf(buffer, "%.4f ms", myScan->deblank_delay);
	printf ("|      De-blanking Delay              : %-38s |\n", buffer);
	sprintf(buffer, "%.4f us", myScan->transient_delay);
	printf ("|      Transient Delay                : %-38s |\n", buffer);
	sprintf(buffer, "%.4f s", myScan->repetition_delay);
	printf ("|      Repetition Delay               : %-38s |\n", buffer);
	printf ("|                                                                              |\n");
	printf ("|------------------------------------------------------------------------------|\n");
}


//
// Board Interfacing
//

int configureBoard (SCANPARAMS * myScan){
	
	pb_set_defaults ();
	pb_core_clock (myScan->ADC_frequency);   

	pb_overflow (1, 0);		//Reset the overflow counters
	pb_scan_count (1);		//Reset scan counter
	
	
	///
    /// Set acquisition parameters
    ///
    
    //Determine actual spectral width
	int cmd = 0;
	if (myScan->bypass_fir){
		cmd = BYPASS_FIR;
	}
	
	double SW_MHz = myScan->SW/1000.0;
	int dec_amount = pb_setup_filters (SW_MHz, myScan->num_scans, cmd);
	if (dec_amount <= 0){
		printf("\n\nError: Invalid data returned from pb_setup_filters(). Please check your board.\n\n");
		return INVALID_DATA_FROM_BOARD;
    }
    
    double ADC_frequency_kHz = myScan->ADC_frequency * 1000;
    myScan->actual_SW = ADC_frequency_kHz / (double) dec_amount;
   
   
 	//Determine ccontinous/segmented scanning points/times
  	int num_segments;
 	int points_per_segment;
 	
 	
 	//Find segmented scan parameters
	if(myScan->num_echo_points > 0){
		//Determine number of points
		myScan->num_points = myScan->num_echoes * myScan->num_echo_points;
		
		/*
		//Make the number of points a power of 2 to avoid crashes and allow FFT
		myScan->num_points = roundUpPower2(myScan->num_points);  
		*/
		
		if(myScan->num_points > 16384){
			myScan->num_points = 16384;
			printf("| Notice:                                                                      |\n"); 
			printf("|     The number of points used in acquisition are greater than 16k (16384).   |\n");
			printf("|     Acquisition will only save 16k points.                                   |\n");
			printf("|                                                                              |\n");
		}
		
		//Determine scan time, the total amount of time that data is collected in one scan cycle
		double actual_SW_Hz = myScan->actual_SW * 1000;
		myScan->scan_time = (double) 1e3 * (myScan->num_points)/actual_SW_Hz;			//ms
		myScan->a180_time = (double) 1e6 * (myScan->num_echo_points)/actual_SW_Hz;	//us
		
		if(myScan->a180_time >= 2 * myScan->tau){
			myScan->num_echo_points = 0;
			printf("| Notice:                                                                      |\n"); 
			printf("|     Echo acquisition time is greater than or equal to 2 * tau.               |\n");
			printf("|     Performing continous acquisition instead.                                |\n");
			printf("|                                                                              |\n");
		}
		
		else{
			double allowed_dedeblank_period_ms = (myScan->tau - myScan->a180_time/2)/1000;
			if(myScan->deblank_delay > allowed_dedeblank_period_ms){
				char min_tau_string[6];
				double min_tau = myScan->deblank_delay * 1000 + myScan->a180_time/2;
				sprintf(min_tau_string, "%.2f", min_tau);
				
				myScan->deblank_delay = allowed_dedeblank_period_ms;
				
				printf("| Notice:                                                                      |\n"); 
				printf("|     The blanking delay is larger than the allowed deblanking period          |\n");
				printf("|     for this combination of tau and number of echo points.                   |\n");
				printf("|                                                                              |\n");
				printf("|     The blanking delay will be reduced for segmenterd acquisition.           |\n");
				printf("|     Try using a tau of at least %-6s us to allow for full deblanking.     |\n", min_tau_string);
				printf("|                                                                              |\n");
			}
		}
		
		num_segments = myScan->num_echoes;
		points_per_segment = myScan->num_echo_points;		
	}
 	
	//Find continous scan parameters		 	
	if(myScan->num_echo_points == 0){		
		//Determine scan time, the total amount of time that data is collected in one scan cycle
		if(myScan->include_90){
			myScan->scan_time = (myScan->p180_time * myScan->num_echoes + (1 + 2 * myScan->num_echoes) * myScan->tau)/1000;	
		}
   		else{
			myScan->scan_time = (myScan->p180_time * (myScan->num_echoes - 1) + 2 * (myScan->tau) * (myScan->num_echoes))/1000;
   		}
   		
   		//Determine number of points 
   		myScan->num_points = floor(myScan->scan_time * myScan->actual_SW);
   		
		//Make the number of points a power of 2 to avoid crashes and allow FFT
		myScan->num_points = roundUpPower2(myScan->num_points);   	   
		
		if(myScan->num_points > 16384){
			myScan->num_points = 16384;
			printf("| Notice:                                                                      |\n"); 
			printf("|     The number of points used in acquisition are greater than 16k (16384).   |\n");
			printf("|     Acquisition will only save 16k points.                                   |\n");
			printf("|                                                                              |\n");
		}
					
   		num_segments = 1;
   		points_per_segment = myScan->num_points;
	}
	
	
	//Set continous/segmented scan parameters
	pb_set_num_points (points_per_segment);
	pb_set_scan_segments (num_segments);
	
	return 0;
}

int programBoard (SCANPARAMS * myScan){
	///
	/// Program frequency, phase and amplitude registers
	///
	
	int scan_loop_label, echo_loop_label;
	
	//Frequency
	pb_start_programming (FREQ_REGS);
	pb_set_freq (myScan->SF);
	pb_stop_programming ();
	
	//Real Phase
	pb_start_programming (COS_PHASE_REGS);
	pb_set_phase (0.0);
	pb_set_phase (90.0);
	pb_set_phase (180.0);
	pb_set_phase (270.0);
	pb_stop_programming ();
	
	//Imaginary Phase
	pb_start_programming (SIN_PHASE_REGS);
	pb_set_phase (0.0);
	pb_set_phase (90.0);
	pb_set_phase (180.0);
	pb_set_phase (270.0);
	pb_stop_programming ();
	
	//Transmitted Phase
	pb_start_programming (TX_PHASE_REGS);
	pb_set_phase (myScan->p90_phase);
	pb_set_phase (myScan->p180_phase);
	pb_stop_programming ();
	
	//Amplitude
	pb_set_amp(myScan->amplitude , 0);
	
	
	///
	/// Specify pulse program
	///

	 pb_start_programming (PULSE_PROGRAM);

   
 	//Program for continous acquisition
 	if(myScan->num_echo_points == 0){
		// Reset phase initially, so that the phase of the excitation pulse will be
	    // the same for every scan. This is the beginning of the scan loop
	 	// Warm-up PA before P1 pulse
		scan_loop_label =
		 	//De-blank amplifier for the blanking delay so that it can fully amplify a pulse
		    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, PHASE_RESET,
			   NO_TRIGGER,0,0, myScan->deblank_bit_mask, LOOP, myScan->num_scans, myScan->deblank_delay * ms);
		
		    //Transmit 90 degree pulse
		    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_ENABLE, NO_PHASE_RESET,
			   NO_TRIGGER,0,0, myScan->deblank_bit_mask, CONTINUE, 0, myScan->p90_time * us);
			
			//If no 90 degree acquistion avoid second de-blanking delay by keeping the power amplifier enabled until 180 degree output 
			if(!myScan->include_90){
				//Delay so that tau is the distance between the end of the 90 degree pulse and the start of the 180 degree pulse
				pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
				   myScan->include_90,0,0, myScan->deblank_bit_mask, CONTINUE, 0, (myScan->tau) * us);
			}
		
			else{
				//Blank amplifier to reduce noise and wait for the transient to subside
			    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
				   NO_TRIGGER,0,0, BLANK_PA, CONTINUE, 0, myScan->transient_delay * us);
						
				//Keep amplifier blanked and perform 90 degree acquisition
				pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
				   myScan->include_90,0,0, BLANK_PA, CONTINUE, 0, (myScan->a90_time) * us - myScan->deblank_delay * ms);
				  
				//De-blank amplifier for the blanking delay		
				pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
				   myScan->include_90,0,0, myScan->deblank_bit_mask, CONTINUE, 0, myScan->deblank_delay * ms);
			}
			
			echo_loop_label = 
				//Transmit 180 degree pulse 
			    pb_inst_radio_shape (0, PHASE090, PHASE000, 1, TX_ENABLE, NO_PHASE_RESET,
				   NO_TRIGGER,0,0, myScan->deblank_bit_mask, LOOP, myScan->num_echoes, myScan->p180_time * us); 
				
				if(myScan->num_echoes == 1){
					//Perform 180 degree echo aquisition
				    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
					   DO_TRIGGER,0,0, BLANK_PA, END_LOOP, echo_loop_label, myScan->a180_time * us);
				}
				else{
					//Perform 180 degree echo aquisition with blanked power amplifier to reduce noise
				    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
					   DO_TRIGGER,0,0, BLANK_PA, CONTINUE, 0, myScan->a180_time * us - myScan->deblank_delay * ms);
					
					//De-blank amplifier for the blanking delay and finish 180 degree echo aquisition,		
					pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
					   DO_TRIGGER,0,0, myScan->deblank_bit_mask, END_LOOP, echo_loop_label, myScan->deblank_delay * ms);
				}
		    
			//Scan acquisition complete
	
			//Allow sample to relax before performing another scan cycle
			//Then loop back to scan_loop_label and repeat the scan cycle. This will occur num_scans times
		    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
			   NO_TRIGGER,0,0, BLANK_PA, END_LOOP, scan_loop_label, myScan->repetition_delay * 1000.0 * ms);
		
	    //After all scans complete, stop the pulse program
	    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
		   NO_TRIGGER,0,0, BLANK_PA, STOP, 0, 1.0 * us);	
 	}
 	
 	//Program for segmented acquisition
 	else{
 		scan_loop_label =
		 	//De-blank amplifier for the blanking delay so that it can fully amplify a pulse
		    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, PHASE_RESET,
			   NO_TRIGGER,0,0, myScan->deblank_bit_mask, LOOP, myScan->num_scans, myScan->deblank_delay * ms);
		
		    //Transmit 90 degree pulse
		    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_ENABLE, NO_PHASE_RESET,
			   NO_TRIGGER,0,0, myScan->deblank_bit_mask, CONTINUE, 0, myScan->p90_time * us);
			
			//Avoid second de-blanking delay by keeping the power amplifier enabled until 180 degree output 
			//Delay so that tau is the distance between the end of the 90 degree pulse and the start of the 180 degree pulse
			pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
			   NO_TRIGGER,0,0, myScan->deblank_bit_mask, CONTINUE, 0, (myScan->tau) * us);
			
			echo_loop_label = 
				//Transmit 180 degree pulse 
			    pb_inst_radio_shape (0, PHASE090, PHASE000, 1, TX_ENABLE, NO_PHASE_RESET,
				   NO_TRIGGER,0,0, myScan->deblank_bit_mask, LOOP, myScan->num_echoes, myScan->p180_time * us); 
				
				//Wait to start 180 degree echo aquisition, so that acquisition is centered around peak
				pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
				   NO_TRIGGER,0,0, BLANK_PA, CONTINUE, 0, myScan->tau * us - myScan->a180_time/2 * us);
				
				//Perform 180 degree echo aquisition with blanked power amplifier to reduce noise
				pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
				   DO_TRIGGER,0,0, BLANK_PA, CONTINUE, 0, myScan->a180_time * us);
				
				//De-blank amplifier and wait until 2 tau
				pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
				   NO_TRIGGER,0,0, myScan->deblank_bit_mask, END_LOOP, echo_loop_label, myScan->tau * us - myScan->a180_time/2 * us);	
		    
			//Scan acquisition complete
	
			//Allow sample to relax before performing another scan cycle
			//Then loop back to scan_loop_label and repeat the scan cycle. This will occur num_scans times
		    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
			   NO_TRIGGER,0,0, BLANK_PA, END_LOOP, scan_loop_label, myScan->repetition_delay * 1000.0 * ms);
		
	    //After all scans complete, stop the pulse program
	    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
		   NO_TRIGGER,0,0, BLANK_PA, STOP, 0, 1.0 * us);
 	}
	
	
	pb_stop_programming ();
    
    return 0;
}


//
// File Writing
//

void createFelixTitleBlock(SCANPARAMS *myScan, char *title_string){
	//These variables are used for the Title Block in Felix
	char *program_type = "CPMG";
	char buff_string[40];
	
	//Create Title Block String
	strcpy (title_string,"Program = ");
	strcat (title_string,program_type);
	strcat (title_string,"\r\n\r\nSpectrometer Frequency = ");
	sprintf(buff_string,"%f",myScan->SF);
	strcat (title_string,buff_string);
	strcat (title_string,"\r\nSpectral Width = ");
	sprintf(buff_string,"%f",myScan->SW);
	strcat (title_string,buff_string);
	strcat (title_string,"\r\n90 Degree Pulse Time = ");
	sprintf(buff_string,"%f",myScan->p90_time);
	strcat (title_string,buff_string);
	strcat (title_string,"\r\nTransient Delay = ");
	sprintf(buff_string,"%f",myScan->transient_delay);
	strcat (title_string,buff_string);
	strcat (title_string,"\r\n90 Degree Pulse Phase = ");
	sprintf(buff_string,"%f",myScan->p90_phase);
	strcat (title_string,buff_string);
	strcat (title_string,"\r\n180 Degree Pulse Phase = ");
	sprintf(buff_string,"%f",myScan->p180_phase);
	strcat (title_string,buff_string);
	strcat (title_string,"\r\nTau = ");
	sprintf(buff_string,"%f",myScan->tau);
	strcat (title_string,buff_string);
	strcat (title_string,"\r\n# of Scans = ");
	sprintf(buff_string,"%d",myScan->num_scans);
	strcat (title_string,buff_string);
	strcat (title_string,"\r\nBypass FIR = ");
	sprintf(buff_string,"%d",myScan->bypass_fir);
	strcat (title_string,buff_string);
	strcat (title_string,"\r\nADC Frequency = ");
	sprintf(buff_string,"%f",myScan->ADC_frequency);
	strcat (title_string,buff_string);
	strcat (title_string,"\r\nRepetition Delay = ");
	sprintf(buff_string,"%f",myScan->repetition_delay);
	strcat (title_string,buff_string);
 }
 
 void writeDataToFiles(SCANPARAMS* myScan, int* real, int* imag){
	double actual_SW_Hz = (myScan->actual_SW)*1000;
	
	char fid_fname[FNAME_SIZE];
	char jcamp_fname[FNAME_SIZE];
	char ascii_fname[FNAME_SIZE];
	
	char Felix_title_block[412];
	
	//Set up file names		
	//Copy up to 5 less than the file name size to leave room for extension and null terminator
	strncpy (fid_fname, myScan->file_name, FNAME_SIZE-5);
	strncat (fid_fname, ".fid", 4);
	strncpy (jcamp_fname, myScan->file_name, FNAME_SIZE-5);
	strncat (jcamp_fname, ".jdx", 4);
	strncpy (ascii_fname, myScan->file_name, FNAME_SIZE-5);
	strncat (ascii_fname, ".txt", 4);
	
	
	createFelixTitleBlock(myScan, Felix_title_block);
					
	pb_write_felix (fid_fname, Felix_title_block, myScan->num_points, 
			actual_SW_Hz,
			myScan->SF, real, imag);
	pb_write_ascii_verbose (ascii_fname, myScan->num_points,
			actual_SW_Hz,
			myScan->SF, real, imag);
	pb_write_jcamp (jcamp_fname, myScan->num_points,
			actual_SW_Hz,
			myScan->SF, real, imag);
}


//
// Calculations
//
 
//Round a number up to the nearest power of 2 
 int roundUpPower2(int number){
 	int remainder_total = 0;
 	int rounded_number = 1;
 	
 	//Determine next highest power of 2
	 while(number != 0){
 		remainder_total += number % 2;
 		number /= 2;
 		rounded_number *= 2;
	}
	
	//If the number was originally a power of 2, it will only have a remainder for 1/2, which is 1
	//Then lower it a power of 2 to recieve the original value
	if(remainder_total == 1){
		rounded_number /= 2;	
	}
	
 	return rounded_number;
 }
 
 double * calcMag(int* real, int* imag, int num_points){
 	double* mag;
 	allocInitMem((void *) &mag, num_points * sizeof(double));

 	int i;
	for(i = 0; i < num_points; i++){
		double real_squared = (double) real[i] * (double) real[i];
		double imag_squared = (double) imag[i] * (double) imag[i];
		mag[i] = sqrt(real_squared + imag_squared);
 	}
 	
 	return mag;
 }
 
 //Find the maximum peak magnitude from a selection of points
 double * findPeaks(double* data, SCANPARAMS* myScan){
 	double* peaks;
 	allocInitMem((void *) &peaks, myScan->num_echoes * sizeof(double));
 	
 	int points_per_echo = myScan->num_echo_points;	
 	
 	//If only one point is taken per echo every point is a peak
 	if(points_per_echo == 1){
 		int i;
		for(i = 0; i < myScan->num_echoes; i++){
 			peaks[i] = data[i];
 		}
 	}
 	
	else{
		int initial_offset_points = 0;
		int continuous_offset_points = 0;
		
		//Adjust parameters in the event of continous scanning
		if(points_per_echo == 0){
			double ms_per_echo = (2 * myScan->tau)/1000;
			points_per_echo = ms_per_echo * myScan->actual_SW;
			
			continuous_offset_points = myScan->p180_time/1000 * myScan->actual_SW;
			
			double initial_offset_time_ms = myScan->include_90 * (myScan->tau - myScan->transient_delay + myScan->p180_time)/1000;
			initial_offset_points = initial_offset_time_ms * myScan->actual_SW;
		}
		
		//Find peaks
 		int i;
 		double peak;
 		for(i = 0; i < myScan->num_echoes; i++){
 			int j;
 			int j_offset = initial_offset_points + i * (continuous_offset_points + points_per_echo);
 			peak = data[j_offset];
 			for(j = j_offset; j < j_offset + points_per_echo; j++){
 				if(peak < data[j]){
 					peak = data[j];
 				}
 			}
 			peaks[i] = peak;
		}
 	}
 	
 	return peaks;
}
 
 //Perform an exponential fit of the data. T2 is the negative inverse of the exponential fit.
double calcT2(int num_points, double time_per_point, double* mag){
	double exp_fit;
	double T2;
	double* time;
	allocInitMem((void *) &time, num_points * sizeof(double));
	
	int i;
	for(i = 0; i < num_points; i++){
		time[i] = ((double) i) * time_per_point;
 	}
 	
 	//Calculate exponential fit
 	exp_fit = calcExpFit(num_points, time, mag);
 	
 	//Calculate T2
	T2 = -1/exp_fit;
 	
 	free(time);
 	
	return T2;
}

//Perform a linear regression of the form y = m*x + b, where y is the natural log of the data. data = e^(mx + b)
double calcExpFit(int num_points, double* x, double* exp_y){
	double m;
 	 	
 	double x_sum = 0;			//x = time per point
 	double x_squared_sum = 0;	//x^2
 	double y_sum = 0;			//y = ln(data)
 	double x_y_sum = 0;			//x*y
	
	int i;
	for(i = 0; i < num_points; i++){
		double y = log(exp_y[i]);
		
		//Calculate summations
		x_sum += x[i];
 		x_squared_sum += (x[i] * x[i]);
 		y_sum += y; 
 		x_y_sum += (x[i] * y);
 	}
 	
 	//Calculate exponential fit
 	m = ((x_sum * y_sum) - (num_points * x_y_sum))/
	 		((x_sum * x_sum) - (num_points * x_squared_sum));
 	
	return m;
}
