/* file T1_IR_sweep.c:   Last Edit 11/26/2013 10:56:00
 *
 *     Created by:
 *     Tycho Sleator 
 *     New York University
 *     Department of Physics
 *     4 Washington Place
 *     New York, NY 10027
 *     email:  tycho.sleator@nyu.edu. 
 *
 * Adapted from file: "Hahn_echo.c"
 *
 * See the accompanying batch file "T1_IR_sweep.bat" for instructions
 * on how to use this program.  
 */

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
 * \file CPMG.c
 * \brief CPMG Example Program
 * This program demonstrates the Carr-Purcell-Meiboom-Gill (CPMG) Pulse Program
 * on the SpinCore RadioProcessor boards.
 *
 * \ingroup RP
 */
 
// Units of various quantities
// MHz:    MyScan->SF;
// kHz:    MyScan->SW;
// Hz:     MyScan->actualSpectralWidth;
// us:     MyScan->P2_time;
// us:     MyScan->ringdown_time;
// degree: MyScan->P2_phase;
// degree: MyScan->P1_phase;
// us:     MyScan->tau;
// s:      MyScan->repetition_delay;
// MHz:    MyScan->adcFrequency;
// none:   MyScan->amplitude;
// ms:     MyScan->blankDelay;
// 

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "spinapi.h"
#include "T1_IR_sweep.h"


int
main (int argc, char **argv)
{
  SCANPARAMS *myScan;
  printf("%s\n", argv[0]);
  PB_OVERFLOW_STRUCT of;
//  int *real, *imag;
//  int cmd, dec_amount, scan_loop_label, echo_loop_label;
//  int num_points;
//
//  double scan_time;
//
//  char txt_fname[FNAME_SIZE];
//  char fid_fname[FNAME_SIZE];
//  
//  //These variables are used for the Title Block in Felix  
//  char title_string[412];
  
  //pb_set_debug(1);
  
  myScan = (SCANPARAMS *) malloc (sizeof (SCANPARAMS));
  memset ((void *) myScan, 0, sizeof (SCANPARAMS));
  printf("Using SpinAPI Version: %s\n\n",pb_get_version());

  if (processArguments (argc, argv, myScan) == 0)
  {
    if (myScan->debug)
		pb_set_debug(1);

    if (pb_count_boards () <= 0)
	{
       printf("No RadioProcessor boards were detected in your system.\n");
	   system("pause");
	   return BOARD_NOT_DETECTED;
    }


    //Here we start a loop to cycle through each of the values of tau
    for (myScan->i_tau = 0; myScan->i_tau < myScan->n_tau; myScan->i_tau++) // i goes from 0 to myScan->n_tau-1
    {
       myScan->tau = myScan->tau_min + myScan->i_tau * myScan->delta_tau;
       runPulseProgram (myScan);  
    }

     return 0;
   }
   else
     return -1;
 }
 
// Remove first character from a string.
// This is used to generate filenames 
char *truncStr (char *charBuffer) 
{
	char *str;
	if (strlen(charBuffer) == 0)
    	str = charBuffer;
  	else
		str = charBuffer + 1;
  	return str;
}


int 
runPulseProgram(SCANPARAMS * myScan)  
{
  int *real, *imag;
  int cmd, dec_amount, scan_loop_label;
  int num_points;

  double scan_time;

  char txt_fname[FNAME_SIZE];
  char fid_fname[FNAME_SIZE];
  char fnum[FNAME_SIZE];  // place to put the string that represents the file number.
  
  //These variables are used for the Title Block in Felix  
  char title_string[412];

  strncpy (txt_fname, myScan->fname, FNAME_SIZE);
  
  itoa (100 + myScan->i_tau, fnum, 10);  // convert the scan number (myScan->i_tau) to a string
  // remove the character "1" from the beginning of the string
  // and append what's left to the end of the filename
  // as set up now, this allows a maximum of 100 files (0 - 99)
  strncat (txt_fname, truncStr(fnum), FNAME_SIZE); 
  strncat (txt_fname, ".txt", FNAME_SIZE); // add ".txt" to the end of the string
  strncpy (fid_fname, myScan->fname, FNAME_SIZE);
  strncat (fid_fname, ".fid", FNAME_SIZE);

  pb_set_defaults ();
  pb_core_clock (myScan->adcFrequency);

  pb_overflow (1, 0);		// reset the overflow counters
  pb_scan_count (1);		// reset scan counter

  ///
  /// Set acquisition parameters
  ///
  if (myScan->bypass_fir)
    cmd = BYPASS_FIR;
  dec_amount = pb_setup_filters (myScan->SW/1000.0, myScan->num_scans, cmd);

  myScan->actualSpectralWidth = (myScan->adcFrequency * 1.0e6) / (double) dec_amount;
//  printf ("Actual SW used is %f kHz (desired was %f kHz)\n", myScan->actualSpectralWidth/1000.0, myScan->SW);

  // Duration of time over which data are collected.  
  // We set this to myScan->fid_time  
  scan_time = myScan->fid_time; 
  num_points = floor( ((scan_time)/1e6) * myScan->actualSpectralWidth);

  pb_set_num_points (num_points);
  pb_set_scan_segments (1);

  outputScanParams (myScan);
	
  // Initialize data arrays
  real = (int *)malloc(num_points * sizeof(int));
  imag = (int *)malloc(num_points * sizeof(int));

  ///
  /// Program frequency, phase and amplitude registers
  ///
  pb_start_programming (FREQ_REGS);
  pb_set_freq (myScan->SF);
  pb_stop_programming ();
	
  pb_start_programming (COS_PHASE_REGS);
  pb_set_phase (0.0);
  pb_set_phase (90.0);
  pb_set_phase (180.0);
  pb_set_phase (270.0);
  pb_stop_programming ();
	
  pb_start_programming (SIN_PHASE_REGS);
  pb_set_phase (0.0);
  pb_set_phase (90.0);
  pb_set_phase (180.0);
  pb_set_phase (270.0);
  pb_stop_programming ();
	
  pb_start_programming (TX_PHASE_REGS);
  pb_set_phase (myScan->p1_phase);
  pb_set_phase (myScan->p2_phase);
  pb_stop_programming ();
	
  pb_set_amp(myScan->amplitude , 0);
	
	
  ///
  /// Specify pulse program
  ///

//  pb_inst_radio (freq, cos_phase, sin_phase, tx_phase, tx_enable, phase_reset, 
//     trigger_scan, flags, inst, inst_data, length)

  pb_start_programming (PULSE_PROGRAM);

  // Reset phase initially, so that the phase of the excitation pulse will be
  // the same for every scan. This is the beginning of the scan loop
  // Warm-up PA before P1 pulse
  scan_loop_label =
  // Wait for transmitter to turn on (blanking delay)
    pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, PHASE_RESET,
	   NO_TRIGGER,0,0, myScan->blankMask, LOOP, myScan->num_scans, myScan->blankDelay * ms);

  // 1st (180 degree) pulse (P1)
  pb_inst_radio_shape (0, PHASE090, PHASE000, 1, TX_ENABLE, NO_PHASE_RESET,
    NO_TRIGGER,0,0, myScan->blankMask, CONTINUE, 0, myScan->p1_time * us);

  // Wait time tau
  pb_inst_radio_shape (0, PHASE090, PHASE000, 1, TX_DISABLE, NO_PHASE_RESET,
    NO_TRIGGER,0,0, myScan->blankMask, CONTINUE, 0, myScan->tau * us);

  // 2nd (90 degree) pulse (P2)    
  pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_ENABLE, NO_PHASE_RESET,
    NO_TRIGGER,0,0, myScan->blankMask, CONTINUE, 0, myScan->p2_time * us); 

  // Wait for for the transient to subside...
  pb_inst_radio_shape (0, PHASE090, PHASE000, 1, TX_DISABLE, NO_PHASE_RESET,
    NO_TRIGGER,0,0, myScan->blankMask, CONTINUE, 0, myScan->ringdown_time * us);

  // and then start scan and wait time myScan->fid_time).
  pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
    DO_TRIGGER,0,0, myScan->blankMask, CONTINUE, 0, 2 * myScan->fid_time * us);

  // At about this time the num_points data points have been scanned, 
  // so the scanning stops.  

  // Allow sample to relax before acuiring another scan
  pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
    NO_TRIGGER,0,0, 0x00, CONTINUE, 0, myScan->repetition_delay * 1000.0 * ms);

  // Loop back and do scan again. This will occur num_scans times
  pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, PHASE_RESET,
    NO_TRIGGER,0,0, 0x00, END_LOOP, scan_loop_label, 1.0 * us);

  // Then stop the pulse program
  pb_inst_radio_shape (0, PHASE090, PHASE000, 0, TX_DISABLE, NO_PHASE_RESET,
    NO_TRIGGER,0,0, 0x00, STOP, scan_loop_label, 1.0 * us);

  pb_stop_programming ();

  ///
  /// Trigger pulse program
  ///
  pb_reset();
  pb_start();

  //
  // Wait until scan is complete.
  //
  printf("\n");
  int scan_count = 0; // Scan count is not deterministic. Scans may be skipped or repeated

  while (pb_read_status () != 0x03)    //Wait for the board to complete execution.
  {      
//      pb_sleep_ms (totalTime/myScan->nScans);

    while( (pb_scan_count(0) <= scan_count)&& (pb_read_status () != 0x03) )
    {
      pb_sleep_ms(100);
    }

    if (pb_read_status () != 0x03) 
    {
      printf("Current Scan: %d\n", pb_scan_count(0));
    }
    scan_count++;
  }

  printf("\nDone \n\n");

  printTitleBlock(myScan, title_string);

  ///
  /// Read data out of the RAM
  ///
  pb_get_data (num_points, real, imag); // For PCI boards, can read any size <= 16384
  // Write the data to an ASCII file
  pb_write_ascii (txt_fname, num_points, myScan->actualSpectralWidth, real, imag);

//  Uncomment command below to output felix files
//	// Write the data to a Felix file
//	pb_write_felix (fid_fname, title_string, num_points, myScan->actualSpectralWidth, 
//					  myScan->SF, real, imag);

}

//////  Here we end the loop to cycle through each of the values of tau

//     return 0;
//   }
//   else
//     return -1;
// }
// 
//--------------------------------------------------------------------


int
processArguments (int argc, char *argv[], SCANPARAMS * scanParams)
{
  if (argc != NUM_ARGUMENTS + 1)
    {
      printProperUse ();
      system("pause");
      return INVALID_NUM_ARGUMENTS;
    }

  scanParams->fname = argv[1];
  scanParams->SF = atof (argv[2]);		  // MHz
  scanParams->SW = atof (argv[3]);		  // kHz
  scanParams->p1_time = atof (argv[4]);	  // us
  scanParams->p2_time = atof (argv[5]);	  // us
  scanParams->ringdown_time = atof (argv[6]); // us
  scanParams->p1_phase = atof (argv[7]);	  // degrees
  scanParams->p2_phase = atof (argv[8]);	  // degrees
  scanParams->fid_time = atof (argv[9]);		  // us
  scanParams->tau_min = atof (argv[10]);		  // us
  scanParams->delta_tau = atof (argv[11]);    // us
  scanParams->n_tau = atoi (argv[12]);
  scanParams->num_scans = atoi (argv[13]);
  scanParams->repetition_delay = atof (argv[14]); // s
  scanParams->amplitude = atof (argv[15]);  
  scanParams->blankDelay = atof (argv[16]);       // ms
  scanParams->bypass_fir = atoi (argv[17]);
  scanParams->adcFrequency = atof (argv[18]);	  // MHz
  scanParams->blankBit = atoi (argv[19]);
  scanParams->debug = atoi (argv[20]);
  scanParams->board_num = atoi (argv[21]);

  scanParams->blankMask = (1<<scanParams->blankBit);

  if (verifyArguments (scanParams))
    return INVALID_ARGUMENTS;

  return 0;

}

int
verifyArguments (SCANPARAMS * scanParams)
{
  if (pb_count_boards () > 0
      && scanParams->board_num > pb_count_boards () - 1)
  {
	  printf ("Error: Invalid board number. Use (0-%d).\n",pb_count_boards () - 1);
      return -1;
  }
    
  pb_select_board(scanParams->board_num);
  
  if (pb_init ())
  {
      printf ("Error initializing board: %s\n", pb_get_error ());
      return -1;
  }
  
  if (scanParams->amplitude < 0.0 || scanParams->amplitude > 1.0)
  {
	printf ("Error: Amplitude value out of range.\n");
      return -1;
  }

  if(scanParams->SF < 0.0 || scanParams->SF > 100.0)
  {
		printf("Spectrometer Freq. must be between 0 and 100 MHz\n");
		return -1;
  }

  if(scanParams->SW < 0.0 || scanParams->SW > 10000.0)
  {
		printf("Invalid Spectral Width\n");
		return -1;
  }

  if(scanParams->p1_time < 0.065)
  {
		printf("P1 time must be > 0.065 us\n");
		return -1;
  }

  if(scanParams->p2_time < 0.065)
  {
		printf("P2 time must be > 0.065 us\n");
		return -1;
  }

  if (scanParams->ringdown_time < 0.065)
  {
	printf ("Error: Transient time is too small to work with board.\n");
      return -1;
  }

  if(scanParams->fid_time < 0.065)
  {
		printf("fid_time must be > 0.065 us\n");
		return -1;
  }

  if(scanParams->tau_min < 0.065)
  {
		printf("tau_min must be > 0.065 us\n");
		return -1;
  }

  if(scanParams->delta_tau < 0.0)
  {
		printf("delta tau2 must be > 0.0 us\n");
		return -1;
  }

  if (scanParams->n_tau < 1)
  {
	printf ("Error: There must be at least one value of tau.\n");
      return -1;
  }

  if (scanParams->num_scans < 1)
  {
	printf ("Error: There must be at least one scan.\n");
      return -1;
  }

  if (scanParams->blankDelay < 0)
  {
        printf("Invalid blanking delay.\n");
  }
  
  if (scanParams->blankBit > 3 || scanParams->blankBit < 0)
  {
        printf("Invalid blanking bit. Value must be between 0 and 5.\n");
  }
  
  return 0;
}

void
outputScanParams (SCANPARAMS * myScan)
{
  printf ("=====================================\n");
  printf (" T1_IR_sweep\n");
  printf (" Experiment number  :%d of %d \n", 
            (int)(((myScan->tau - myScan->tau_min) / myScan->delta_tau)+1.5), 
            myScan->n_tau
          );
  printf ("-------------------------------------\n");
  printf (" root filename      :%s \n",    myScan->fname);
  printf (" tau                :%3.2f us\n",  myScan->tau);
  printf ("-------------------------------------\n");
  printf (" tau_min            :%3.2f us\n",  myScan->tau_min);
  printf (" delta_tau          :%3.2f us\n",  myScan->delta_tau);
  printf (" n_tau              :%d \n",    myScan->n_tau);
  printf (" number of averages :%d \n",	  myScan->num_scans);
  printf (" fid_time           :%3.2f us\n",  myScan->fid_time);
  printf ("-------------------------------------\n");
  printf (" Spectrometer freq. :%10.6f MHz\n", myScan->SF);
  printf (" Spectral width     :%6.2f kHz\n", myScan->SW);
  printf (" p1_time            :%6.2f us\n",  myScan->p1_time);
  printf (" p2_time            :%6.2f us\n",  myScan->p2_time);
  printf (" ringdown_time      :%6.2f us\n",  myScan->ringdown_time);
  printf (" p1_phase           :%6.2f us\n",  myScan->p1_phase);
  printf (" p2_phase           :%6.2f us\n",  myScan->p2_phase);
  printf (" repetition_delay   :%6.2f s\n",   myScan->repetition_delay);
  printf (" amplitude          :%6.2f \n",    myScan->amplitude);
  printf ("-------------------------------------\n");
  printf (" blank_delay        :%6.2f ms\n",  myScan->blankDelay);
  printf (" adc_frequency      :%6.2f MHz\n", myScan->adcFrequency);
  printf (" bypass fir         :%d \n", 	  myScan->bypass_fir);
  printf (" blank_bit          :%d \n",    myScan->blankBit);
  printf (" debug              :%d \n", 	  myScan->debug);
  printf (" board_num          :%d \n",    myScan->board_num);
  printf ("-------------------------------------\n");
  printf (" Actual SW used is %3.2f kHz \n Desired SW was    %3.2f kHz\n", 
            myScan->actualSpectralWidth/1000.0, myScan->SW);
  printf ("=====================================\n");

}

/*
void
outputScanParams (SCANPARAMS * myScan)
{
  printf ("root filename      :%s\n",     myScan->fname);
  printf ("Spectrometer freq. :%f MHz\n", myScan->SF);
  printf ("Spectral width     :%f kHz\n", myScan->SW);
  printf ("p1_time            :%f us\n",  myScan->p1_time);
  printf ("p2_time            :%f us\n",  myScan->p2_time);
  printf ("ringdown_time      :%f us\n",  myScan->ringdown_time);
  printf ("p1_phase           :%f degree\n", myScan->p1_phase);
  printf ("p2_phase           :%f degree\n", myScan->p2_phase);
  printf ("tau                :%f us\n",  myScan->tau);
  printf ("fid_time           :%f us\n",  myScan->fid_time);
  printf ("tau_min            :%f us\n",  myScan->tau_min);
  printf ("delta_tau          :%f us\n",  myScan->delta_tau);
  printf ("n_tau              :%d\n",     myScan->n_tau);
  printf ("num_scans          :%d\n",     myScan->num_scans);
  printf ("repetition_delay   :%f s\n",   myScan->repetition_delay);
  printf ("amplitude          :%f ms\n",  myScan->amplitude);
  printf ("blank_delay        :%f ms\n",  myScan->blankDelay);
  printf ("bypass fir         :%d\n",     myScan->bypass_fir);
  printf ("adc_frequency      :%f MHz\n", myScan->adcFrequency);
  printf ("blank_bit          :%d\n",     myScan->blankBit);
  printf ("debug              :%d\n",     myScan->debug);
  printf ("board_num          :%d\n",     myScan->board_num);
}
*/

static inline void
printProperUse ()
{
  printf ("Incorrect number of arguments, there should be %d. Syntax is:\n",
	  NUM_ARGUMENTS);
  printf ("--------------------------------------------\n");
  printf ("Variable                       Units\n");
  printf ("--------------------------------------------\n");
  printf ("Filename.......................Filename to store output\n");
  printf ("Spectrometer Frequency.........MHz\n");
  printf ("Spectral Width.................kHz\n");
  printf ("Pulse 1 Time...................us\n");
  printf ("Pulse 2 Time...................us\n");
  printf ("Ringdown Time..................us\n");
  printf ("Pulse 1 Phase..................degrees\n");
  printf ("Pulse 2 Phase..................degrees\n");
  printf ("fid_time.......................us\n");
  printf ("Tau_min........................us\n"); 
  printf ("Delta_Tau......................us\n"); 
  printf ("n_Tau..........................(1 or greater)\n"); 
  printf ("Number of Scans................(1 or greater)\n");
  printf ("Repetition Delay...............s\n");
  printf ("Amplitude......................Amplitude of excitation pulse (0.0 to 1.0)\n");
  printf ("Blanking Delay.................ms\n");
  printf ("Bypass FIR.....................(1 to bypass, or 0 to use)\n");
  printf ("ADC Frequency..................ADC sample frequency\n");
  printf ("Blanking Bit...................(0-5)\n");
  printf ("Debug Output...................(1 for enabled, 0 for disabled)\n");
  printf ("Board Number...................(0-%d)\n", pb_count_boards () - 1);
}

  
void printTitleBlock(SCANPARAMS *myScan, char *title_string)
{
   //These variables are used for the Title Block in Felix
   char *program_type = "T1_IR_sweep";
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
  strcat (title_string,"\r\np1 Time = ");
  sprintf(buff_string,"%f",myScan->p1_time);
  strcat (title_string,buff_string);
  strcat (title_string,"\r\nRingdown Time = ");
  sprintf(buff_string,"%f",myScan->ringdown_time);
  strcat (title_string,buff_string);
  strcat (title_string,"\r\np1 Phase = ");
  sprintf(buff_string,"%f",myScan->p1_phase);
  strcat (title_string,buff_string);
  strcat (title_string,"\r\np2 Phase = ");
  sprintf(buff_string,"%f",myScan->p2_phase);
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
  sprintf(buff_string,"%f",myScan->adcFrequency);
  strcat (title_string,buff_string);
  strcat (title_string,"\r\nRepetition Delay = ");
  sprintf(buff_string,"%f",myScan->repetition_delay);
  strcat (title_string,buff_string);
}  
  
