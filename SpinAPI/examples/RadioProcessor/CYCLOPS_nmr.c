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
 * CYCLOPS_nmr.c
 * This program is used to control the RadioProcessor series of boards.
 *
 * SpinCore Technologies, Inc.
 * www.spincore.com
 * $Date: 2009/07/23 15:06:02 $
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "spinapi.h"
#include "CYCLOPS_nmr.h"

#ifdef _MSC_VER
#define inline __inline
#endif

inline void printProperUse(); //Prints out the usage data for the executable

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
   SCANPARAMS *myScan;
   CYCLOPSPARAMS *cycScan;
   
   int i;
   double resFreq, totalTime;
   int *real, *imag;
   
   char title_string[412];  
   char fid_fname[FNAME_SIZE];
   char jcamp_fname[FNAME_SIZE];
   char ascii_fname[FNAME_SIZE];

   myScan = (SCANPARAMS *) malloc (sizeof (SCANPARAMS));
   memset ((void *) myScan, 0, sizeof (SCANPARAMS));
   cycScan = (CYCLOPSPARAMS *) malloc (sizeof (CYCLOPSPARAMS));
   memset ((void *) cycScan, 0, sizeof (CYCLOPSPARAMS));
  
  // Uncommenting the line below will generate a log.txt in your current directory
  // that can help us debug any problems that you may be experiencing   
  //pb_set_debug(1);
  
   printf("Using SpinAPI Version: %s\n\n",pb_get_version());
   if (processArguments (argc, argv, myScan, cycScan) == 0)
   {
      if (pb_count_boards () <= 0)
      {
         if (myScan->verbose)
            printf("No RadioProcessor boards were detected in your system.\n");
         pause();
	     return BOARD_NOT_DETECTED;
      }

      // Initialize data arrays
      real = (int *)malloc(myScan->nPoints * sizeof(int));
      imag = (int *)malloc(myScan->nPoints * sizeof(int));
   
      if (myScan->verbose)
         outputScanParams (myScan);

      // Setup output file names
      strncpy (fid_fname, myScan->outputFilename, FNAME_SIZE);
      strncat (fid_fname, ".fid", FNAME_SIZE);
      strncpy (jcamp_fname, myScan->outputFilename, FNAME_SIZE);
      strncat (jcamp_fname, ".jdx", FNAME_SIZE);
      strncpy (ascii_fname, myScan->outputFilename, FNAME_SIZE);
      strncat (ascii_fname, ".txt", FNAME_SIZE);

      if (configureBoard (myScan) < 0)	//Set board defaults.
         return -1;

      if (programBoard(myScan,cycScan) != 0)	//Program the board.
      {
         if (myScan->verbose)
     	    printf ("Error: Failed to program board.\n");
         pause();
	     return PROGRAMMING_FAILED;
      }

      pb_reset();
      pb_start ();

      totalTime = (myScan->wait_time + (myScan->repetitionDelay * 1000))*myScan->nScans;
      
      if (myScan->verbose)
      {
         if(totalTime < 1000)
            printf ("Total Experiment Time   : %lf ms\n\n", totalTime);
         else if(totalTime < 60000)
            printf ("Total Experiment Time   : %lf s\n\n", totalTime/1000);
         else if(totalTime < 3600000)
            printf ("Total Experiment Time   : %lf minutes\n\n", totalTime/60000);
         else
            printf ("Total Experiment Time   : %lf hours\n\n", totalTime/3600000);
         
         printf ("Waiting for the data acquisition to complete...\n");
      }
        
      while (pb_read_status () != BOARD_STATUS_IDLE)	//Wait for the board to complete execution.
      {
         if(totalTime/myScan->nScans < 600)
            pb_sleep_ms (1000);
         else      
	        pb_sleep_ms (totalTime/myScan->nScans);
         printf("Current Scan: %d\n",pb_scan_count(0));
	  }

      if (myScan->enable_rx)
	  {
	     pb_get_data (myScan->nPoints, real, imag);

         if(myScan->nPoints > MAX_FFT)
         {
            int t_real[MAX_FFT];
            int t_imag[MAX_FFT];
            
            for(i=0;i<MAX_FFT;i++)
            {
               t_real[i] = real[i];
               t_imag[i] = imag[i];
            }
            resFreq = pb_fft_find_resonance(MAX_FFT, ((myScan->spectrometerFrequency)*1e6), 
                       myScan->actualSpectralWidth, t_real, t_imag);
         }
         else
         {
            
            resFreq = pb_fft_find_resonance(myScan->nPoints, ((myScan->spectrometerFrequency)*1e6), 
                       myScan->actualSpectralWidth, real, imag);
         }        
               
         printf("\nResonance Frequency: %lf MHz\n\n", resFreq/1e6);
      
         printTitleBlock(myScan, title_string);
      
	     pb_write_felix (fid_fname, title_string, myScan->nPoints, myScan->actualSpectralWidth, 
                      myScan->spectrometerFrequency, real, imag);
	     pb_write_ascii_verbose (ascii_fname, myScan->nPoints,
				  myScan->actualSpectralWidth,
				  myScan->spectrometerFrequency, real, imag);
	     pb_write_jcamp (jcamp_fname, myScan->nPoints,
			  myScan->actualSpectralWidth,
			  myScan->spectrometerFrequency, real, imag);
      } // End if(enable_rx)
   
      pb_close ();

   } // End if(processArguements(...)

  free (myScan);

  return 0;
  
} // End main()


//--------------------------------------------------------------------
int
processArguments (int argc, char *argv[], SCANPARAMS * scanParams, CYCLOPSPARAMS * cyclopsParams)
{
  if (argc != NUM_ARGUMENTS + 1)
    {
      printf("The number of arguments is: %d\n\n",argc-1);
      printProperUse ();
      pause();
      return INVALID_NUM_ARGUMENTS;
    }

  scanParams->board_num = atoi (argv[1]);
  scanParams->nPoints = atoi (argv[2]);
  scanParams->spectrometerFrequency = atof (argv[3]);
  scanParams->spectralWidth = atof (argv[4]);
  scanParams->pulseTime = atof (argv[5]);
  scanParams->transTime = atof (argv[6]);
  scanParams->repetitionDelay = atof (argv[7]);
  scanParams->nScans = atoi (argv[8]);
  scanParams->tx_phase = atof (argv[9]);
  scanParams->outputFilename = argv[10];
  scanParams->bypass_fir = (unsigned short) atoi (argv[11]);
  scanParams->adcFrequency = atof (argv[12]);
  scanParams->use_shape = (unsigned short) atoi (argv[13]);
  scanParams->amplitude = atof (argv[14]);
  scanParams->enable_tx = atof (argv[15]);
  scanParams->enable_rx = atof (argv[16]);
  scanParams->verbose = atof (argv[17]);
  scanParams->blankingEnable = atoi (argv[18]);
  scanParams->blankingBit = atoi (argv[19]);
  scanParams->blankingDelay = atof (argv[20]);
  
  cyclopsParams->add_sub_re_0 = atoi (argv[21]);
  cyclopsParams->add_sub_im_0 = atoi (argv[22]);
  cyclopsParams->swap_0 = atoi (argv[23]);
  cyclopsParams->add_sub_re_1 = atoi (argv[24]);
  cyclopsParams->add_sub_im_1 = atoi (argv[25]);
  cyclopsParams->swap_1 = atoi (argv[26]);
  cyclopsParams->add_sub_re_2 = atoi (argv[27]);
  cyclopsParams->add_sub_im_2 = atoi (argv[28]);
  cyclopsParams->swap_2 = atoi (argv[29]);
  cyclopsParams->add_sub_re_3 = atoi (argv[30]);
  cyclopsParams->add_sub_im_3 = atoi (argv[31]);
  cyclopsParams->swap_3 = atoi (argv[32]);
  scanParams->debug = atoi(argv[33]);
  
  if (verifyArguments (scanParams, scanParams->verbose) != 0)
    return INVALID_ARGUMENTS;

  return 0;

}

int
verifyArguments (SCANPARAMS * scanParams, int verbose)
{
  int fw_id;
  
  if (pb_count_boards () > 0
      && scanParams->board_num > pb_count_boards () - 1)
    {
      if (verbose)
	printf ("Error: Invalid board number. Use (0-%d).\n",
		pb_count_boards () - 1);
      return -1;
    }
  
  pb_select_board(scanParams->board_num);
  
  if (pb_init ())
    {
      printf ("Error initializing board: %s\n", pb_get_error ());
      return -1;
    }
  
  fw_id = pb_get_firmware_id();
  if ((fw_id > 0xA00 && fw_id < 0xAFF) || (fw_id > 0xF00 && fw_id < 0xFFF))
  {
      if (scanParams->nPoints > 16*1024 || scanParams->nPoints < 1)
      {
          if (verbose)
    	     printf ("Error: Maximum number of points for RadioProcessorPCI is 16384.\n");
          return -1;
      }
  }    
  else if(fw_id > 0xC00 && fw_id < 0xCFF)
  {
      if (scanParams->nPoints > 256*1024 || scanParams->nPoints < 1)
      {
          if (verbose)
    	     printf ("Error: Maximum number of points for RadioProcessorUSB is 256k.\n");
          return -1;
      }
  }
  
  if (scanParams->nScans < 1)
    {
      if (verbose)
	printf ("Error: There must be at least one scan.\n");
      return -1;
    }
     else if (scanParams->nScans%4!=0 && scanParams->nScans!=1)
  	 {
	 	 if(verbose)
	 	   printf("Error: To run CYCLOPS with multiple scans, the Number of Scans must be a mulitple of 4\n");
	 	   return -1;
    }

  if (scanParams->pulseTime < 0.065)
    {
      if (verbose)
	printf ("Error: Pulse time is too small to work with board.\n");
      return -1;
    }

  if (scanParams->transTime < 0.065)
    {
      if (verbose)
	printf ("Error: Transient time is too small to work with board.\n");
      return -1;
    }

  if (scanParams->amplitude < 0.0 || scanParams->amplitude > 1.0)
    {
      if (verbose)
	printf ("Error: Amplitude value out of range.\n");
      return -1;
    }

  return 0;
}

inline void
printProperUse ()
{
  printf ("Incorrect number of arguments, there should be %d. Syntax is:\n",
	  NUM_ARGUMENTS);
  printf ("--------------------------------------------\n");
  printf ("Variable                       Units\n");
  printf ("--------------------------------------------\n");
  printf ("Board Number..................(0-%d)\n", pb_count_boards () - 1);
  printf ("Number of Points..............(1-16384)\n");
  printf ("Spectrometer Frequency........MHz\n");
  printf ("Spectral Width................kHz\n");
  printf ("Pulse Time....................us\n");
  printf ("Transient Time................us\n");
  printf ("Repetition Delay..............s\n");
  printf ("Number of Scans...............(1 or greater)\n");
  printf ("TX Phase......................degrees\n");
  printf ("Filename......................Filename to store output\n");
  printf ("Bypass FIR....................(1 to bypass, or 0 to use)\n");
  printf ("ADC Frequency.................ADC sample frequency\n");
  printf
    ("Shaped Pulse..................(1 to output shaped pulse, 0 otherwise)\n");
  printf
    ("Amplitude.....................Amplitude of excitation pulse (0.0 to 1.0)\n");
  printf
    ("Enable Transmitter Stage......(1 turns transmitter on, 0 turns transmitter off)\n");
  printf
    ("Enable Receiver Stage.........(1 turns receiver on, 0 turns receiver off)\n");
  printf
    ("Enable Verbose Output.........(1 enables verbose output, 0 suppresses output)\n");
  printf
    ("Use TTL Blanking..............(1 enables blanking, 0 disables blanking)\n");
  printf
    ("Blanking TTL Flag Bits........TTL Flag Bit(s) used in the blanking\n");
  printf
    ("Blanking Delay................Delay between de-blanking and the TX Pulse (ms)\n");
  printf
    ("Debugging Output...............(1 enables debugging output logfile, 0 disables)\n");
}

void
outputScanParams (SCANPARAMS * myScan)
{
  printf ("Filename                : %s\n", myScan->outputFilename);
  printf ("Board Number            : %d\n", myScan->board_num);
  printf ("Number of Points        : %d\n", myScan->nPoints);
  printf ("Number of Scans         : %d\n", myScan->nScans);
  printf ("Use shape               : %d\n", myScan->use_shape);
  printf ("Bypass FIR              : %d\n", myScan->bypass_fir);
  printf ("Amplitude               : %lf\n", myScan->amplitude);
  printf ("Spectrometer Frequency  : %lf MHz\n", myScan->spectrometerFrequency);
  printf ("Spectral Width          : %lf kHz\n", myScan->spectralWidth);
  printf ("TX Phase                : %lf degrees\n", myScan->tx_phase);
  printf ("Pulse Time              : %lf us\n", myScan->pulseTime);
  printf ("Trans Time              : %lf us\n", myScan->transTime);
  printf ("Repetition Delay        : %lf s\n", myScan->repetitionDelay);
  printf ("ADC Frequency           : %lf MHz\n", myScan->adcFrequency);
  printf ("Enable Transmitter      : %d\n", myScan->enable_tx);
  printf ("Enable Receiver         : %d\n", myScan->enable_rx);
  printf ("Use TTL Blanking        : %d\n", myScan->blankingEnable);
  printf ("Blanking TTL Flag Bits  : 0x%x\n", myScan->blankingBit);
  printf ("Blanking Delay          : %lf ms\n", myScan->blankingDelay);
  printf ("Debugging               : %s\n", ((myScan->debug!=0)?"Enabled":"Disabled"));
}

void
make_shape_data (float *shape_array, void *arg,
		 void (*shapefnc) (float *, void *))
{
  shapefnc (shape_array, arg);
}

void
shape_sinc (float *shape_data, void *nlobe)
{
  static double pi = 3.1415926;
  int i;
  int lobes = *((int *) nlobe);
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

int
configureBoard (SCANPARAMS * myScan)
{
  float shape_data[1024];

  double actual_SW;
  double wait_time;
  double spectralWidth_MHZ = myScan->spectralWidth / 1000.0;

  int dec_amount;
  int cmd = 0;
  int num_lobes = 3;

  pb_set_defaults ();
  pb_core_clock (myScan->adcFrequency);

  pb_overflow (1, 0);		// reset the overflow counters
  pb_scan_count (1);		// reset scan counter


  // Load the shape parameters
  make_shape_data (shape_data, (void *) &num_lobes, shape_sinc);
  pb_dds_load (shape_data, DEVICE_SHAPE);
  pb_set_amp (((myScan->enable_tx) ? myScan->amplitude : 0), 0);

  //
  /// Set acquisition parameters
  ///
  if (myScan->bypass_fir)
    {
      cmd = BYPASS_FIR;
    }

  dec_amount = pb_setup_filters (spectralWidth_MHZ, myScan->nScans, cmd);
  pb_set_num_points (myScan->nPoints);

  if (dec_amount <= 0)
    {
      if (myScan->verbose)
	printf
	  ("\n\nError: Invalid data returned from pb_setup_filters(). Please check your board.\n\n");
      return INVALID_DATA_FROM_BOARD;
    }

  actual_SW = (myScan->adcFrequency * 1e6) / (double) dec_amount;
  myScan->actualSpectralWidth = actual_SW;
  printf ("Actual Spectral Width   : %f Hz\n", myScan->actualSpectralWidth);

  wait_time = 1000.0 * (((double) myScan->nPoints) / actual_SW);	// time in ms
  myScan->wait_time = wait_time;
  printf ("Acquisition Time        : %lf ms\n\n", wait_time);
  
  return 0;
}

int
programBoard (SCANPARAMS * myScan, CYCLOPSPARAMS * cycScan)
{
  int start, rx_start, tx_start, nLoop;

  pb_start_programming (FREQ_REGS);
  pb_set_freq (0);		//Program Frequency Register 0 to 0
  pb_set_freq (myScan->spectrometerFrequency * MHz);	//Register 1
  pb_set_freq (checkUndersampling (myScan, myScan->verbose));	//Register 2
  pb_stop_programming ();


  // control phases for REAL channel
  pb_start_programming (COS_PHASE_REGS);
  pb_set_phase (00.0);
  pb_set_phase (90.0);
  pb_set_phase (180.0);
  pb_set_phase (270.0);
  pb_stop_programming ();

  // control phases for IMAG channel
  pb_start_programming (SIN_PHASE_REGS);
  pb_set_phase (0.0);
  pb_set_phase (90.0);
  pb_set_phase (180.0);
  pb_set_phase (270.0);
  pb_stop_programming ();

  // control phases for output channel
  pb_start_programming (TX_PHASE_REGS);
  pb_set_phase (myScan->tx_phase);
  pb_set_phase (myScan->tx_phase + 90.0);
  pb_set_phase (myScan->tx_phase + 180.0);
  pb_set_phase (myScan->tx_phase + 270.0);
  pb_stop_programming ();

  ///
  /// Specify pulse program
  ///

  pb_start_programming (PULSE_PROGRAM);
  nLoop = myScan->nScans/4;

if(myScan->nScans >= 4)
{

  //If we have the transmitter enabled, we must include the pulse program to generate the RF pulse.
  if (myScan->enable_tx)
    {
      // Reset phase initially, so that the phase of the excitation pulse will be the same for every scan.
      if(pb_inst_radio_shape_cyclops (1, PHASE000, PHASE090, PHASE000, TX_DISABLE, PHASE_RESET,
			   NO_TRIGGER, myScan->use_shape, myScan->amplitude,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0,
			   0x00, CONTINUE, 0, 1.0 * us) < 0)
		{
			printf("Your board does not support CYCLOPS!\n\n");
			exit(1);
		}
	


/********************  BEGIN SCAN #0  **********************************************/
      //If blanking is enabled, we must add an additional pulse program interval to compesate for the time the power amplifier needs to "warm up" before we can generate the RF pulse.
      if (myScan->blankingEnable)
	{
	  tx_start =
	    pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE000, TX_DISABLE,
				 NO_PHASE_RESET, NO_TRIGGER, 0, 0,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0,
				 (1 << myScan->blankingBit), LOOP, nLoop
				 , myScan->blankingDelay * ms);

	  pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE000, TX_ENABLE,
			       NO_PHASE_RESET, NO_TRIGGER, myScan->use_shape,
			       0,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0, (1 << myScan->blankingBit), CONTINUE, 0,
			       myScan->pulseTime * us);
	}
      else
	{
	  tx_start =
	    pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE000, TX_ENABLE,
				 NO_PHASE_RESET, NO_TRIGGER,
				 myScan->use_shape, 0,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0, 0, LOOP,
				 nLoop, myScan->pulseTime * us);
	}

      // Output nothing for the transient time.
      pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE000, TX_DISABLE,
			   NO_PHASE_RESET, NO_TRIGGER, 0, 0,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0, 0x00, CONTINUE,
			   0, myScan->transTime * us);
    }

  //If we are enabling the receiver, we must wait for the scan to complete.
  if (myScan->enable_rx)
    {
      rx_start =
	pb_inst_radio_shape_cyclops (2, PHASE090, PHASE000, PHASE000, TX_DISABLE,
			     NO_PHASE_RESET, DO_TRIGGER, 0, 0,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0, 0, LONG_DELAY,
			     8, ((myScan->wait_time)*ms/8));
    }

  //If the transmitter is enabled, we start from the TX section of the pulse program.
  if (myScan->enable_tx)
    start = tx_start;
  else if (myScan->enable_rx)
    start = rx_start;
  else
    return RX_AND_TX_DISABLED; 

  // Now wait the repetition delay, then loop back to the beginning. Also reset the phase in anticipation of the next scan
  pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE000, TX_DISABLE, PHASE_RESET,
		       NO_TRIGGER, 0, 0,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0, 0x00, CONTINUE, 0,
 		       myScan->repetitionDelay * 1000.0 * ms);
	
/*****************  END SCAN #0  ***********************************/


/*****************  BEGIN SCAN #1  *************************************/

if (myScan->enable_tx)
    {
      //If blanking is enabled, we must add an additional pulse program interval to compensate for the time the power amplifier needs to "warm up" before we can generate the RF pulse.
      if (myScan->blankingEnable)
	{
	    pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE090, TX_DISABLE,
				 NO_PHASE_RESET, NO_TRIGGER, 0, 0,cycScan->add_sub_re_1,cycScan->add_sub_im_1,cycScan->swap_1,
				 (1 << myScan->blankingBit), CONTINUE,
				 0, myScan->blankingDelay * ms);

	  pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE090, TX_ENABLE,
			       NO_PHASE_RESET, NO_TRIGGER, myScan->use_shape,
			       0,cycScan->add_sub_re_1,cycScan->add_sub_im_1,cycScan->swap_1, (1 << myScan->blankingBit), CONTINUE, 0,
			       myScan->pulseTime * us);
	}
      else
	{

	    pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE090, TX_ENABLE,
				 NO_PHASE_RESET, NO_TRIGGER,
				 myScan->use_shape, 0,cycScan->add_sub_re_1,cycScan->add_sub_im_1,cycScan->swap_1, 0, CONTINUE,
				 0, myScan->pulseTime * us);
	}

      // Output nothing for the transient time.
      pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE090, TX_DISABLE,
			   NO_PHASE_RESET, NO_TRIGGER, 0, 0,cycScan->add_sub_re_1,cycScan->add_sub_im_1,cycScan->swap_1, 0x00, CONTINUE,
			   0, myScan->transTime * us);
    }

  //If we are enabling the receiver, we must wait for the scan to complete.
  if (myScan->enable_rx)
    {
	pb_inst_radio_shape_cyclops (2, PHASE090, PHASE000, PHASE090, TX_DISABLE,
			     NO_PHASE_RESET, DO_TRIGGER, 0, 0,cycScan->add_sub_re_1,cycScan->add_sub_im_1,cycScan->swap_1, 0, LONG_DELAY,
			     8, ((myScan->wait_time)*ms/8));
    }

  //If the transmitter is enabled, we start from the TX section of the pulse program.


  // Now wait the repetition delay, then loop back to the beginning. Also reset the phase in anticipation of the next scan
  pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE180, TX_DISABLE, PHASE_RESET,
		       NO_TRIGGER, 0, 0,cycScan->add_sub_re_1,cycScan->add_sub_im_1,cycScan->swap_1, 0x00, CONTINUE, 0,
		       myScan->repetitionDelay * 1000.0 * ms);

	   
/******************  END SCAN #1  ***********************************************/




/******************  BEGIN SCAN #2  ****************************************************/

if (myScan->enable_tx)
    {
      //If blanking is enabled, we must add an additional pulse program interval to compesate for the time the power amplifier needs to "warm up" before we can generate the RF pulse.
      if (myScan->blankingEnable)
	{
	    pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE180, TX_DISABLE,
				 NO_PHASE_RESET, NO_TRIGGER, 0, 0,cycScan->add_sub_re_2,cycScan->add_sub_im_2,cycScan->swap_2,
				 (1 << myScan->blankingBit), CONTINUE,0, myScan->blankingDelay * ms);

	  pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE180, TX_ENABLE,
			       NO_PHASE_RESET, NO_TRIGGER, myScan->use_shape,
			       0,cycScan->add_sub_re_2,cycScan->add_sub_im_2,cycScan->swap_2, (1 << myScan->blankingBit), CONTINUE, 0,
			       myScan->pulseTime * us);
	}
      else
	{
	    pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE180, TX_ENABLE,
				 NO_PHASE_RESET, NO_TRIGGER,
				 myScan->use_shape, 0,cycScan->add_sub_re_2,cycScan->add_sub_im_2,cycScan->swap_2, 0, CONTINUE,
				 0, myScan->pulseTime * us);
	}

      // Output nothing for the transient time.
      pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE180, TX_DISABLE,
			   NO_PHASE_RESET, NO_TRIGGER, 0, 0,cycScan->add_sub_re_2,cycScan->add_sub_im_2,cycScan->swap_2, 0x00, CONTINUE,
			   0, myScan->transTime * us);
    }

  //If we are enabling the receiver, we must wait for the scan to complete.
  if (myScan->enable_rx)
    {
	pb_inst_radio_shape_cyclops (2, PHASE090, PHASE000, PHASE180, TX_DISABLE,
			     NO_PHASE_RESET, DO_TRIGGER, 0, 0,cycScan->add_sub_re_2,cycScan->add_sub_im_2,cycScan->swap_2, 0, LONG_DELAY,
			     8, ((myScan->wait_time)*ms/8));
    }

  // Now wait the repetition delay, then loop back to the beginning. Also reset the phase in anticipation of the next scan
  pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE270, TX_DISABLE, PHASE_RESET,
		       NO_TRIGGER, 0, 0,cycScan->add_sub_re_2,cycScan->add_sub_im_2,cycScan->swap_2, 0x00, CONTINUE, 0,
		       myScan->repetitionDelay * 1000.0 * ms);


/**********************  END SCAN #2  *******************************/



/**********************  BEGIN SCAN #3  ***********************************/

if (myScan->enable_tx)
{
      //If blanking is enabled, we must add an additional pulse program interval to compesate for the time the power amplifier needs to "warm up" before we can generate the RF pulse.
    if (myScan->blankingEnable)
	{
	    pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE270, TX_DISABLE,
				 NO_PHASE_RESET, NO_TRIGGER, 0, 0,cycScan->add_sub_re_3,cycScan->add_sub_im_3,cycScan->swap_3,
				 (1 << myScan->blankingBit), CONTINUE,0, myScan->blankingDelay * ms);

	  pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE270, TX_ENABLE,
			       NO_PHASE_RESET, NO_TRIGGER, myScan->use_shape,
			       0,cycScan->add_sub_re_3,cycScan->add_sub_im_3,cycScan->swap_3, (1 << myScan->blankingBit), CONTINUE, 0,
			       myScan->pulseTime * us);
	}
    else
	{
	    pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE270, TX_ENABLE,
				 NO_PHASE_RESET, NO_TRIGGER,
				 myScan->use_shape, 0,cycScan->add_sub_re_3,cycScan->add_sub_im_3,cycScan->swap_3, 0x00, CONTINUE,
				 0, myScan->pulseTime * us);
	}

      // Output nothing for the transient time.
      pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE270, TX_DISABLE,
			   NO_PHASE_RESET, NO_TRIGGER, 0, 0,cycScan->add_sub_re_3,cycScan->add_sub_im_3,cycScan->swap_3, 0x00, CONTINUE,
			   0, myScan->transTime * us);
}

  //If we are enabling the receiver, we must wait for the scan to complete.
  if (myScan->enable_rx)
  {
	pb_inst_radio_shape_cyclops (2, PHASE090, PHASE000, PHASE270, TX_DISABLE,
			     NO_PHASE_RESET, DO_TRIGGER, 0, 0,cycScan->add_sub_re_3,cycScan->add_sub_im_3,cycScan->swap_3, 0x00, LONG_DELAY,
			     8, ((myScan->wait_time)*ms/8));
  }

  // Now wait the repetition delay, then loop back to the beginning. Also reset the phase in anticipation of the next scan
  pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE270, TX_DISABLE, PHASE_RESET,
		       NO_TRIGGER, 0, 0,cycScan->add_sub_re_3,cycScan->add_sub_im_3,cycScan->swap_3, 0x00, END_LOOP, start,
		       myScan->repetitionDelay * 1000.0 * ms);

/****************  END SCAN #3  *************************************/
}
else
{
//If we have the transmitter enabled, we must include the pulse program to generate the RF pulse.
  if (myScan->enable_tx)
    {
      // Reset phase initially, so that the phase of the excitation pulse will be the same for every scan.
      pb_inst_radio_shape_cyclops (1, PHASE000, PHASE090, PHASE000, TX_DISABLE, PHASE_RESET,
			   NO_TRIGGER, myScan->use_shape, myScan->amplitude,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0, 0x00, CONTINUE, 0, 1.0 * us);
	
      //If blanking is enabled, we must add an additional pulse program interval to compesate for the time the power amplifier needs to "warm up" before we can generate the RF pulse.
    if (myScan->blankingEnable)
	{
	  tx_start =
	    pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE000, TX_DISABLE,
				 NO_PHASE_RESET, NO_TRIGGER, 0, 0,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0,(1 << myScan->blankingBit), CONTINUE, 
                 0, myScan->blankingDelay * ms);

	  pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE000, TX_ENABLE,
			       NO_PHASE_RESET, NO_TRIGGER, myScan->use_shape, 0,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0, 
                   (1 << myScan->blankingBit), CONTINUE, 0, myScan->pulseTime * us);
	}
    else
	{
	  tx_start =
	    pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE000, TX_ENABLE,
				 NO_PHASE_RESET, NO_TRIGGER, myScan->use_shape, 0,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0, 0, CONTINUE,
				 0, myScan->pulseTime * us);
	}

      // Output nothing for the transient time.
      pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE000, TX_DISABLE,
			   NO_PHASE_RESET, NO_TRIGGER, 0, 0,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0,0x00, CONTINUE,
			   0, myScan->transTime * us);
    }

  //If we are enabling the receiver, we must wait for the scan to complete.
  if (myScan->enable_rx)
    {
      rx_start =
	pb_inst_radio_shape_cyclops (2, PHASE090, PHASE000, PHASE000, TX_DISABLE,
			     NO_PHASE_RESET, DO_TRIGGER, 0, 0,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0, 0, LONG_DELAY,
			     8, ((myScan->wait_time)*ms/8));
    }

  //If the transmitter is enabled, we start from the TX section of the pulse program.
  if (myScan->enable_tx)
    start = tx_start;
  else if (myScan->enable_rx)
    start = rx_start;
  else
    return RX_AND_TX_DISABLED; 

  // Now wait the repetition delay, then loop back to the beginning. Also reset the phase in anticipation of the next scan
  pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE000, TX_DISABLE, PHASE_RESET,
		       NO_TRIGGER, 0, 0,cycScan->add_sub_re_0,cycScan->add_sub_im_0,cycScan->swap_0, 0x00, CONTINUE, 0,
 		       myScan->repetitionDelay * 1000.0 * ms);
}
			   
  // Stop execution of program.
  pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE270, TX_DISABLE, NO_PHASE_RESET,
		       NO_TRIGGER, 0, 0,cycScan->add_sub_re_3,cycScan->add_sub_im_3,cycScan->swap_3, 0x00, CONTINUE, 0, 1.0 * us);
  pb_inst_radio_shape_cyclops (1, PHASE090, PHASE000, PHASE270, TX_DISABLE, NO_PHASE_RESET,
		       NO_TRIGGER, 0, 0,cycScan->add_sub_re_3,cycScan->add_sub_im_3,cycScan->swap_3, 0x00, STOP, 0, 1.0 * us);

  pb_stop_programming ();

  return 0;
}

double
checkUndersampling (SCANPARAMS * myScan, int verbose)
{
  int folding_constant;
  double folded_frequency;
  double adc_frequency = myScan->adcFrequency;
  double spectrometer_frequency = myScan->spectrometerFrequency;
  double nyquist_frequency = adc_frequency / 2.0;

  if (verbose)
    printf ("Specified Spectrometer Frequency : %f MHz\n", spectrometer_frequency);

  if (spectrometer_frequency > nyquist_frequency)
    {
      if (((spectrometer_frequency / adc_frequency) -
	   (int) (spectrometer_frequency / adc_frequency)) >= 0.5)
	folding_constant =
	  (int) ceil (spectrometer_frequency / adc_frequency);
      else
	folding_constant =
	  (int) floor (spectrometer_frequency / adc_frequency);

      folded_frequency =
	fabs (spectrometer_frequency -
	      ((double) folding_constant) * adc_frequency);

      if (verbose)
	printf
	  ("Undersampling Detected: Spectrometer Frequency (%.4lf MHz) is greater than Nyquist (%.4lf MHz).\n",
	   spectrometer_frequency, nyquist_frequency);

      spectrometer_frequency = folded_frequency;
    }

  if (verbose)
    printf ("Using Spectrometer Frequency: %lf MHz.\n\n",
	    spectrometer_frequency);

  return spectrometer_frequency;
}

void printTitleBlock(SCANPARAMS *myScan, char *title_string)
{
   //These variables are used for the Title Block in Felix
   char *program_type = "cyclops_nmr";
   char buff_string[40];     
   
   //Create Title Block String
   strcpy (title_string,"Program = ");
   strcat (title_string,program_type);
   strcat (title_string,"\r\n\r\nPulse Time = ");
   sprintf(buff_string,"%f",myScan->pulseTime);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nTransient Time = ");
   sprintf(buff_string,"%f",myScan->transTime);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nRepetition Delay = ");
   sprintf(buff_string,"%f",myScan->repetitionDelay);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\n# of Scans = ");
   sprintf(buff_string,"%d",myScan->nScans);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nADC Freq = ");
   sprintf(buff_string,"%f",myScan->adcFrequency);
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
   strcat (title_string,"\r\nVerbose = ");
   sprintf(buff_string,"%d",(int)myScan->verbose);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nBlanking Enable = ");
   sprintf(buff_string,"%d",myScan->blankingEnable);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nBlanking Bit = ");
   sprintf(buff_string,"%d",myScan->blankingBit);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nBlanking Delay = ");
   sprintf(buff_string,"%f",myScan->blankingDelay);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\n# of Points = ");
   sprintf(buff_string,"%d",myScan->nPoints);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nSpectral Width = ");
   sprintf(buff_string,"%f",myScan->spectralWidth);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nSpectrometer Freq = ");
   sprintf(buff_string,"%f",myScan->spectrometerFrequency);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nBypass FIR = ");
   sprintf(buff_string,"%d",myScan->bypass_fir);
   strcat (title_string,buff_string);
   strcat (title_string,"\r\nUse Shape = ");
   sprintf(buff_string,"%d",myScan->use_shape);
   strcat (title_string,buff_string);
}
     
