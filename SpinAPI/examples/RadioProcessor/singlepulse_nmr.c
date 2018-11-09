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
 * singlepulse_nmr.c
 * Modified from singlepulse_nmr.c
 *
 *	This program is used to control the RadioProcessor series of boards in conjuction with the iSpin setup.
 *	It generates a single RF pulse of variable shape, frequency, amplitude, phase and duration.
 *	It then acquires the NMR response of the perturbing pulse.
 
 * SpinCore Technologies, Inc.
 * www.spincore.com
 * $Date: 2017/07/11 11:00:00 $
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include <spinapi.h>
#include "singlepulse_nmr.h"

#ifdef _MSC_VER
#define inline __inline
#endif

void pause(void)
{
	printf("Press enter to continue...");
	char buffer = getchar();
	while(buffer != '\n' && buffer != EOF);
	getchar();
}

int main (int argc, char *argv[]){
	SCANPARAMS *myScan;
	int *real, *imag;
	
	printProgramTitle();
		
	
	//
	//Process Arguments
	//
		
	allocInitMem((void *) &myScan, sizeof(SCANPARAMS));
		
	int processStatus = processArguments (argc, argv, myScan);
	if (processStatus != 0){
		pause();
		return processStatus;
	}	
	
	if (myScan->debug){
		pb_set_debug(1);
	}
	
		
	//
	//Configure Board
	//	
	
	//Set board defaults.
	if (configureBoard (myScan) < 0){
		printf ("Error: Failed to configure board.\n");
		pause();
		return CONFIGURATION_FAILED;
	}
	
	allocInitMem((void *) &real, myScan->num_points * sizeof(int));
	allocInitMem((void *) &imag, myScan->num_points * sizeof(int));
	
		
	//
	//Print Parameters
	//
		
	printScanParams (myScan);

	//Calculate and print total time
	double repetition_delay_ms = myScan->repetition_delay * 1000;
	double total_time = (myScan->scan_time + repetition_delay_ms)*myScan->num_scans;
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
		printf ("Total Experiment Time   : %lf hours\n\n\n", total_time/3600000);	
	}
	printf ("\nWaiting for the data acquisition to complete... \n\n");
	
		
	//
	//Program Board
	//
	
	if (programBoard (myScan) != 0){
		printf ("Error: Failed to program board.\n");
		pause();
		return PROGRAMMING_FAILED;
	}
		
		
	///
    /// Trigger Pulse Program
    ///
	
	pb_reset ();	
	pb_start ();
	
			
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
	
	if (myScan->enable_rx){
		if( pb_get_data (myScan->num_points, real, imag) < 0 ){
			printf("Failed to get data from board.\n");
			pause();
			return DATA_RETRIEVAL_FAILED;
		}
		
		//Estimate resonance frequency
		double SF_Hz = (myScan->SF)*1e6;
		double actual_SW_Hz = (myScan->SW)*1e3;
		myScan->res_frequency = pb_fft_find_resonance(myScan->num_points, SF_Hz, actual_SW_Hz, real, imag)/1e6;
		
		//Print resonance estimate	   
		printf("Highest Peak Frequency: %lf MHz\n\n\n", myScan->res_frequency);
	  	
	  	  	
	  	//
	  	// Write Output Files
	  	//
	  	
	  	writeDataToFiles(myScan, real, imag);
	}
	
		
	
	//
	// End Program
	//
	pb_stop ();
		
	pb_close ();

	free (myScan);
	free (real);
	free (imag);
	
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
		pause();
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
	scanParams->debug               = (unsigned short) atoi(argv[4]);
		
	//Frequency Parameters
	scanParams->ADC_frequency       = atof (argv[5]);
	scanParams->SF                  = atof (argv[6]);
	scanParams->SW                  = atof (argv[7]);
	
	//Pulse Parameters
	scanParams->enable_tx           = (unsigned short) atof (argv[8]);
	scanParams->use_shape           = (unsigned short) atoi (argv[9]);
	scanParams->amplitude           = atof (argv[10]);
	scanParams->p90_time            = atof (argv[11]);
	scanParams->p90_phase           = atof (argv[12]);
	
	//Acquisition Parameters
	scanParams->enable_rx           = (unsigned short) atof (argv[13]);
	scanParams->bypass_fir          = (unsigned short) atoi (argv[14]);
	scanParams->num_points          = (unsigned int) roundUpPower2(atoi (argv[15])); //Only use powers of 2
	scanParams->num_scans           = (unsigned int) atoi (argv[16]);
	
	//Delay Parameters
	scanParams->deblank_delay       = atof (argv[17]);
	scanParams->transient_delay     = atof (argv[18]);
	scanParams->repetition_delay    = atof (argv[19]);
	
	//Ensure number of points is a power of 2
	if(scanParams->num_points != atoi (argv[15])){
		printf("| Notice:                                                                      |\n"); 
		printf("|     The desired number of points is not a power of 2.                        |\n");
		printf("|     The number of points have been rounded up to the nearest power of 2.     |\n");
		printf("|                                                                              |\n");
	}
	
	//Check if transmit and recieve are both disabled and warn user
	if((scanParams->enable_tx == 0) && (scanParams->enable_rx == 0)){
			printf("| Notice:                                                                      |\n"); 
			printf("|     Transmit and recieve have both been disabled.                            |\n");
			printf("|     The board will not be programmed.                                        |\n");
			printf("|                                                                              |\n");
	}
	
	
	//Check parameters
	if (verifyArguments (scanParams) != 0){
		return INVALID_ARGUMENTS;
	}

	return 0;
}

int verifyArguments (SCANPARAMS * scanParams){
	int fw_id;
	
	if (pb_count_boards () <= 0){
		printf("No RadioProcessor boards were detected in your system.\n");
		return BOARD_NOT_DETECTED;
	}
	
	if (pb_count_boards () > 0 && scanParams->board_num > pb_count_boards () - 1){
		printf ("Error: Invalid board number. Use (0-%d).\n", pb_count_boards () - 1);
		return -1;
    }
    
	pb_select_board(scanParams->board_num);
	if (pb_init()){
		printf ("Error initializing board: %s\n", pb_get_error ());
		return -1;
    }
  
	fw_id = pb_get_firmware_id();
	if ((fw_id > 0xA00 && fw_id < 0xAFF) || (fw_id > 0xF00 && fw_id < 0xFFF)){
		if (scanParams->num_points > 16*1024 || scanParams->num_points < 1){
			printf ("Error: Maximum number of points for RadioProcessorPCI is 16384.\n");
			return -1;
		}
	}
	
	else if(fw_id > 0xC00 && fw_id < 0xCFF){
		if (scanParams->num_points > 256*1024 || scanParams->num_points < 1){
			printf ("Error: Maximum number of points for RadioProcessorUSB is 256k.\n");
			return -1;
		}
	}
  	
  	if (scanParams->num_scans < 1){
		printf ("Error: There must be at least one scan.\n");
		return -1;
    }

	if (scanParams->p90_time < 0.065){
		printf ("Error: Pulse time is too small to work with board.\n");
		return -1;
    }

	if (scanParams->transient_delay < 0.065){
		printf ("Error: Transient delay is too small to work with board.\n");
		return -1;
    }

	if (scanParams->repetition_delay <= 0){
		printf ("Error: Repetition delay is too small.\n");
		return -1;
    }

	if (scanParams->amplitude < 0.0 || scanParams->amplitude > 1.0){
		printf ("Error: Amplitude value out of range.\n");
		return -1;
    }

	// The RadioProcessor has 4 TTL outputs, check that the blanking bit
	// specified is possible if blanking is enabled.
	if (scanParams->deblank_bit < 0 || scanParams->deblank_bit > 3){
		printf("Error: Invalid de-blanking bit specified.\n");
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
	printf ("|                               Single Pulse NMR                               |\n");
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
  	printf ("Blanking TTL Flag Bit..........TTL Flag Bit used for amplifier blanking signal\n");
  	printf ("Debugging Output...............(1 enables debugging output logfile, 0 disables)\n");
	printf ("ADC Frequency..................ADC sample frequency\n");
	printf ("Spectrometer Frequency.........MHz\n");
	printf ("Spectral Width.................kHz\n");
	printf ("Enable Transmitter Stage.......(1 turns transmitter on, 0 turns transmitter off)\n");
	printf ("Shaped Pulse...................(1 to output shaped pulse, 0 otherwise)\n");
	printf ("Amplitude......................Amplitude of excitation pulse (0.0 to 1.0)\n");
	printf ("90 Degree Pulse Time...........us\n");
	printf ("90 Degree Pulse Phase..........degrees\n");
	printf ("Enable Receiver Stage..........(1 turns receiver on, 0 turns receiver off)\n");
	printf ("Bypass FIR.....................(1 to bypass, or 0 to use)\n");
	printf ("Number of Points...............(1-16384)\n");
	printf ("Number of Scans................(1 or greater)\n");
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
	printf ("|      Enable Transmitter             : %-38s |\n", (myScan->enable_tx != 0) ? "Enabled":"Disabled");
	printf ("|      Use Shape                      : %-38s |\n", (myScan->use_shape != 0) ? "Enabled":"Disabled");
	sprintf(buffer, "%.4f", myScan->amplitude);
	printf ("|      Amplitude                      : %-38s |\n", buffer);
	sprintf(buffer, "%.4f us", myScan->p90_time);
	printf ("|      90 Degree Pulse Time           : %-38s |\n", buffer);
	sprintf(buffer, "%.4f degrees", myScan->p90_phase);
	printf ("|      90 Degree Pulse Phase          : %-38s |\n", buffer);
	printf ("|                                                                              |\n");
	printf ("| Acquistion Parameters:                                                       |\n");
	printf ("|      Enable Reciever                : %-38s |\n", (myScan->enable_rx != 0) ? "Enabled":"Disabled");
	printf ("|      Bypass FIR                     : %-38s |\n", (myScan->bypass_fir != 0) ? "Enabled":"Disabled");
	sprintf(buffer, "%d", myScan->num_points);
	printf ("|      Number of Points               : %-38s |\n", buffer);
	sprintf(buffer, "%d", myScan->num_scans);
	printf ("|      Number of Scans                : %-38s |\n", buffer);
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
	
	
	// Load the shape parameters
	float shape_data[1024];
	int num_lobes = 3;
	
	make_shape_data (shape_data, (void *) &num_lobes, shape_sinc);
	pb_dds_load (shape_data, DEVICE_SHAPE);
	pb_set_amp (((myScan->enable_tx) ? myScan->amplitude : 0), 0);


	///
	/// Set acquisition parameters
	///

	//Determine actual spectral width
	int cmd = 0;
	if (myScan->bypass_fir){
		cmd = BYPASS_FIR;
    }

	double SW_MHz = myScan->SW / 1000.0;
	int dec_amount = pb_setup_filters (SW_MHz, myScan->num_scans, cmd);
	if (dec_amount <= 0){
		printf("\n\nError: Invalid data returned from pb_setup_filters(). Please check your board.\n\n");
		return INVALID_DATA_FROM_BOARD;
    }
	
	double ADC_frequency_kHz = myScan->ADC_frequency * 1000;
	myScan->actual_SW = ADC_frequency_kHz / (double) dec_amount;
	
	
	//Determine scan time, the total amount of time that data is collected in one scan cycle
	myScan->scan_time = (((double) myScan->num_points) / myScan->actual_SW);
	
	
	pb_set_num_points (myScan->num_points);
	pb_set_scan_segments(1);
	
	return 0;
}

int programBoard (SCANPARAMS * myScan){  
	if(!myScan->enable_rx && !myScan->enable_tx){
		return RX_AND_TX_DISABLED;
	}
	
	///
	/// Program frequency, phase and amplitude registers
	///
	
	int scan_loop_label;
	
	//Frequency	
  	pb_start_programming (FREQ_REGS);
  	pb_set_freq (myScan->SF * MHz);
  	pb_set_freq (checkUndersampling (myScan));
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
	pb_stop_programming ();
	
	//Amplitude
	pb_set_amp(myScan->amplitude , 0);
	
	
	///
	/// Specify pulse program
	///
	
	pb_start_programming (PULSE_PROGRAM);
	
		scan_loop_label =
			//De-blank amplifier for the blanking delay so that it can fully amplify a pulse
		 	//Initialize scan loop to loop for the specified number of scans
			//Reset phase so that the excitation pulse phase will be the same for every scan		
			pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, PHASE_RESET, 
				NO_TRIGGER, 0, 0, myScan->deblank_bit_mask, LOOP, myScan->num_scans, myScan->deblank_delay * ms); 
			
			//Transmit 90 degree pulse
		   	pb_inst_radio_shape (0, PHASE090, PHASE000, 0, myScan->enable_tx, NO_PHASE_RESET, 
				NO_TRIGGER, myScan->use_shape, 0, myScan->deblank_bit_mask, CONTINUE, 0, myScan->p90_time * us);
			
			//Wait for the transient to subside
		    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
				NO_TRIGGER, 0, 0, BLANK_PA, CONTINUE, 0, myScan->transient_delay * us);
			
			//Trigger acquisition
			pb_inst_radio_shape (1, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
				myScan->enable_rx, 0, 0, BLANK_PA, CONTINUE, 0, myScan->scan_time * ms);
			
			//Allow sample to relax before performing another scan cycle
			pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET, 
				NO_TRIGGER, 0, 0, BLANK_PA, END_LOOP, scan_loop_label, myScan->repetition_delay * 1000.0 * ms);
		
		//After all scans complete, stop the pulse program
		pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
			NO_TRIGGER, 0, 0, BLANK_PA, STOP, 0, 1.0 * us);

	pb_stop_programming ();

  return 0;
}


//
// File Writing
//

void createFelixTitleBlock(SCANPARAMS *myScan, char *title_string){
   //These variables are used for the Title Block in Felix
   char *program_type = "singlepulse_nmr";
   char buff_string[40];     
   
   //Create Title Block String
   strcpy (title_string,"Program = ");
   strcat (title_string,program_type);
   strcat (title_string,"\r\n\r\n90 Degree Pulse Time = ");
   sprintf(buff_string,"%f",myScan->p90_time);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nTransient Delay = ");
   sprintf(buff_string,"%f",myScan->transient_delay);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nRepetition Delay = ");
   sprintf(buff_string,"%f",myScan->repetition_delay);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\n# of Scans = ");
   sprintf(buff_string,"%d",myScan->num_scans);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nADC Freq = ");
   sprintf(buff_string,"%f",myScan->ADC_frequency);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nAmplitude = ");
   sprintf(buff_string,"%f",myScan->amplitude);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nEnable TX = ");
   sprintf(buff_string,"%d",(int)myScan->enable_tx);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nEnable RX = ");
   sprintf(buff_string,"%d",(int)myScan->enable_rx);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nBlanking Bit = ");
   sprintf(buff_string,"%d",myScan->deblank_bit);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nDe-blanking Delay = ");
   sprintf(buff_string,"%f",myScan->deblank_delay);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\n# of Points = ");
   sprintf(buff_string,"%d",myScan->num_points);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nSpectral Width = ");
   sprintf(buff_string,"%f",myScan->SW);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nSpectrometer Freq = ");
   sprintf(buff_string,"%f",myScan->SF);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nBypass FIR = ");
   sprintf(buff_string,"%d",myScan->bypass_fir);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nUse Shape = ");
   sprintf(buff_string,"%d",myScan->use_shape);
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

void make_shape_data (float *shape_array, void *arg, void (*shapefnc) (float *, void *)){
	shapefnc (shape_array, arg);
}

void shape_sinc (float *shape_data, void *nlobe){
	static double pi = 3.1415926;
	int i;
	int lobes = *((int *) nlobe);
	double x;
	double scale = (double) lobes * (2.0 * pi);
  	
	for (i = 0; i < 1024; i++){
		x = (double) (i - 512) * scale / 1024.0;
		if(x == 0.0){
			shape_data[i] = 1.0;
		}
		else{
			shape_data[i] = sin (x) / x;
		}
	}
}

double checkUndersampling (SCANPARAMS * myScan){
	int folding_constant;
	double folded_frequency;
	double adc_frequency = myScan->ADC_frequency;
	double spectrometer_frequency = myScan->SF;
	double nyquist_frequency = adc_frequency / 2.0;
	
	if (spectrometer_frequency > nyquist_frequency){
		if (((spectrometer_frequency / adc_frequency) -	(int) (spectrometer_frequency / adc_frequency)) >= 0.5){
	 		folding_constant = (int) ceil (spectrometer_frequency / adc_frequency);
	 	}
    	else{
    		folding_constant = (int) floor (spectrometer_frequency / adc_frequency);
    	}
		
		folded_frequency = fabs (spectrometer_frequency - ((double) folding_constant) * adc_frequency);
		
		printf("Undersampling Detected: Spectrometer Frequency (%.4lf MHz) is greater than Nyquist (%.4lf MHz).\n", spectrometer_frequency, nyquist_frequency);
		
		spectrometer_frequency = folded_frequency;
    	
    	printf ("Using Spectrometer Frequency: %lf MHz.\n\n", spectrometer_frequency);
	}
    
	return spectrometer_frequency;
}

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
