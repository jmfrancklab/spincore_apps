#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
 
#ifndef SPINCORE_LINUX
	#include <Windows.h>
#endif

#include "FTD2XX.h"

#include "debug.h"
#include "spinapi.h"
#include "driver-os.h"
#include "driver-usb.h"
#include "util.h"
#include "caps.h"
#include "if.h"
#include "usb.h"

// Since not all users define these at compile time
#ifndef VER_STRING_API
#define VER_STRING_API "custom"
#endif

/*
*
*
*  SpinPTS Includes & Defines
*
*
*/
#define _PTS_SET_NUM_DATA	3
#define ERROR_STR_SIZE	    25

static char *spinpts_version = VER_STRING_API;
static int  spinpts_err = -1;
static char spinpts_err_buf[ERROR_STR_SIZE];

int __set_pts_(int pts_index, BCDFREQ freq, int phase );
BCDFREQ* freq_double_to_bcd( double freq, BCDFREQ* bcdfreq, int is3200 );
/*
*
*
*  End of SpinPTS Includes & Defines
*
*
*/

//Need this char array to display status message
char status_message[120];

// Contains current number of instructions in pulse program
int num_instructions = 0;
extern int shape_period_array[2][7];

//default portbase supplied to backwards compatibility
static int port_base = 0;

//default is pb_only with 24 output bits
static int ISA_BOARD = 0;

// FIXME: this should go in board_info
static int MAX_FLAG_BITS = 0xFFFFFF;

//2^32
double pow232 = 4294967296.0;

double last_rounded_value;

// The number of the currently selected board.
int cur_board = 0;
// Number of boards present in system. -1 indicates we havent counted them yet
//static int num_boards = -1;
static int num_pci_boards = -1;
static int num_usb_devices = -1;
int cur_dds = 0;

// This array holds the capabilties info on each board
BOARD_INFO board[MAX_NUM_BOARDS];

static int cur_device = -1;
static int cur_device_addr = 0;

//version of the DLL
char *version = VER_STRING_API;

int do_os_init (int board);
int do_os_close (int board);

/**
 * \mainpage SpinAPI Documentation
 *
 * This document describes the API used to control SpinCore Technologies, Inc.
 * products and is intended to serve primarily as a reference document. Please
 * see the manuals and example programs to see how the API is used in practice
 * to control the boards.
 *
 * \see spinapi.h for a complete listing of SpinAPI functions.
 * \see http://www.spincore.com/support to download the latest version of SpinAPI
 * \see http://www.spincore.com for information on our products.
 */

/**
 *\file spinapi.c
 *\brief General functions for use with all boards.
 *
 * This page describes functions which are used with all products. It also includes
 * several functions for use with DDS enabled boards that are not relevant to digital-only
 * PulseBlaster cards. For a complete
 * list of spinapi functions, including those which are used only with RadioProcessor
 * boards, please see the spinapi.h page.
 *
 */

SPINCORE_API int
pb_count_boards (void)
{

  num_pci_boards = os_count_boards (VENDID);

  if (num_pci_boards < 0)
    {
      debug (DEBUG_ERROR, "pb_count_boards(): error counting PCI boards. "
             "Please check to make sure WinDriver is properly installed.");
      num_pci_boards = 0;
    }

  num_usb_devices = os_usb_count_devices (0);

  if (num_usb_devices < 0)
    {
      debug (DEBUG_ERROR, "pb_count_boards(): error counting USB boards.");
      num_usb_devices = 0;
    }

  if (num_pci_boards + num_usb_devices > MAX_NUM_BOARDS)
    {
      debug(DEBUG_ERROR, "Detected more boards than the driver can handle");
      return -1;
    }

  debug (DEBUG_INFO, "pb_count_boards(): Detected %d boards in your system.",
         num_pci_boards + num_usb_devices);

  return num_pci_boards + num_usb_devices;
}

SPINCORE_API int
pb_select_board (int board_num)
{
  int num_boards = num_pci_boards + num_usb_devices;

  if (num_boards < 0)
    {
      num_boards = pb_count_boards ();
      if (num_boards < 0) {
          return -1;
      }
    }

  if (board_num < 0 || board_num >= num_boards)
    {
      debug (DEBUG_ERROR, "pb_select_board(..):  Board number out of range (num_boards=%d)", num_boards);
      return -1;
    }

  if (board_num >= num_pci_boards)	//Set current USB Device
    {
      debug (DEBUG_INFO, "pb_select_board(..): Selecting usb board: %d",
	    board_num - num_pci_boards);
      usb_set_device (board_num - num_pci_boards);
    }

  cur_board = board_num;

  return 0;
}

SPINCORE_API int
pb_init (void)
{
 // int dac_control;
//  int adc_control;

  int dev_id;

  debug (DEBUG_INFO, "Entering pb_init. cur_board = %d", cur_board);

  if (board[cur_board].did_init == 1)
    {
      debug (DEBUG_ERROR, "pb_init: Board already initialized. Only call pb_init() once.", );
      return -1;
    }

  if (pb_count_boards () > 0)
    {
      dev_id = do_os_init (cur_board);

      if (dev_id == -1)
        {
          debug (DEBUG_WARNING, "pb_init error (os_init failed)",);
          return -1;
        }

      // Figure out what the capabilities of this board is
      if (get_caps (&(board[cur_board]), dev_id) < 0)
        {
          debug (DEBUG_ERROR, "pb_init error (get_caps failed)",);
          return -1;
        }

      // MOVED TO PB_SET_DEFAULTS() IN if.c
      // If this is a RadioProcessor, set ADC and DAC defaults. This is done
      // here instead of pb_set_defaults() because the user should not ever
      // change these values.
      // if (board[cur_board].is_radioprocessor)
        // {
          // adc_control = 3;
          // dac_control = 0;
          // pb_set_radio_hw (adc_control, dac_control);
        // }

      board[cur_board].did_init = 1;
    }
  else
    {                         
      debug (DEBUG_ERROR, "pb_init(): No board selected: No PulseBlaster Board found!");
      return -1;
    }

  return 0;
}

SPINCORE_API void
pb_core_clock (double clock_freq)
{
  board[cur_board].clock = clock_freq / 1000.0;	// Put in GHz (for ns timescale)
}

SPINCORE_API void
pb_set_clock (double clock_freq)
{
	pb_core_clock(clock_freq);
}

SPINCORE_API int
pb_close (void)
{
  if (board[cur_board].did_init == 0)
    {
      debug (DEBUG_ERROR, "pb_close: Board is already closed",);
      return -1;
    }

  board[cur_board].did_init = 0;
  return do_os_close (cur_board);
}

SPINCORE_API int
pb_start_programming (int device)
{
  int return_value;

  debug (DEBUG_INFO, "pb_start_programming (device=%d)", device);

  // pb_stop_programming() didnt get called. some older code doesnt call
  // pb_stop_programming() properly, so ignore this error and continue anyway
  if (cur_device != -1)
    {
		debug(DEBUG_WARNING, "pb_start_programming: WARNING: pb_start_programming() called without previous stop", );
    }

  if (board[cur_board].usb_method == 2)
    {
      debug (DEBUG_INFO, "pb_start_programming: Using new programming method.", device);

      if (device == PULSE_PROGRAM)
        {
          num_instructions = 0;	// Clear number of instructions  
          usb_write_address (0x80000);	//Write the address register with the start of the PB core memory.
        }
      if (device == FREQ_REGS)
        {
          usb_write_address (board[cur_board].dds_address[cur_dds] + 0x0000);
        }
      if (device == TX_PHASE_REGS)
        {
          if(board[cur_board].firmware_id == 0x0C13 || board[cur_board].firmware_id == 0x0E03) //These designs have different Register Base Addresses
            {
              usb_write_address (board[cur_board].dds_address[cur_dds] + 0x2000);
            }
          else
            {
              usb_write_address (board[cur_board].dds_address[cur_dds] + 0x0400);
            }
        }
  }
  else if (board[cur_board].is_pcie)
    {
	  if (device == PULSE_PROGRAM)
        {
          num_instructions = 0; // Clear number of instructions
	  
	      // reset
          return_value = pb_outw (0, 0);
          if (return_value)
            {
              debug(DEBUG_ERROR, "pb_start_programming: Failed to reset PCIe device.", );
              return return_value;
            }
      
          // reset counter
          return_value = pb_outw (0x4 << 2, 0);
          if (return_value)
            {
              debug(DEBUG_ERROR, "pb_start_programming: Failed to reset PCIe memory counter.", );
              return return_value;
            } 
        }
    }
  else
    {
      // Dont reset PulseBlaster if this is a new style DDS program
      if ((board[cur_board].dds_prog_method == DDS_PROG_OLDPB 
          || device == PULSE_PROGRAM) && board[cur_board].is_radioprocessor != 2) 
        {
          debug (DEBUG_INFO, "pb_start_programming: reset");

          return_value = pb_outp (port_base + 0, 0);	// Reset PulseBlasterDDS
          if (return_value != 0 && (!(ISA_BOARD)))
            {
              debug (DEBUG_ERROR, "pb_start_programming: initial reset failed", );
              return return_value;
            }
        }
      
      if (device == PULSE_PROGRAM)
        {
          num_instructions = 0;	// Clear number of instructions

          if (board[cur_board].is_radioprocessor == 2)
            {
              reg_write(0, 0); // set IMW_ADDR to 0
            }
          else
            {
              if (board[cur_board].firmware_id == 0xa13 || board[cur_board].firmware_id == 0xC10)	//Fix me.
                {
                  //For 0x0a13, the IMW size is 88 bits. (11x8=88)
                  return_value = pb_outp (port_base + 2, 11);	// This is an instruction, therefore Bytes Per Word (BPW) = 11
                }
              else if (board[cur_board].firmware_id == 0x0908)	//Fix me.
                {
                  //For 0x0908, the IMW size is 64 bits. (8x8=64)
                  return_value = pb_outp (port_base + 2, 8);	// This is an instruction, therefore Bytes Per Word (BPW) = 8
                }
              else if (board[cur_board].firmware_id == 0x1105 || board[cur_board].firmware_id == 0x1106 || board[cur_board].firmware_id == 0x1107)	//Fix me.
                {
                  //For 0x1105, the IMW size is 32 bits. (4x8=64)
                  return_value = pb_outp (port_base + 2, 4);	// This is an instruction, therefore Bytes Per Word (BPW) = 4
                }
              else
                {
                  return_value = pb_outp (port_base + 2, 10);	// This is an instruction, therefore Bytes Per Word (BPW) = 10
                }

              if (return_value != 0 && (!(ISA_BOARD)))
                {
                  debug (DEBUG_ERROR, "pb_start_programming: BPW=10 write failed",);
                  return return_value;
                }

              return_value = pb_outp (port_base + 3, device);	// Device = RAM
              if (return_value != 0 && (!(ISA_BOARD)))
                {
                  debug (DEBUG_ERROR, "pb_start_programming: Device=RAM write failed", );
                  return return_value;
                }

              return_value = pb_outp (port_base + 4, 0);	// Reset mem counter
              if (return_value != 0 && (!(ISA_BOARD)))
                {
                  debug (DEBUG_ERROR, "pb_start_programming: mem counter write failed (PULSE_PROGRAM)", );
                  return return_value;
                }
            }
        }
      else if (device == FREQ_REGS || device == TX_PHASE_REGS
	       || device == RX_PHASE_REGS)
        {
          // We only need to do anything here if this the old style dds interface
          if (board[cur_board].dds_prog_method == DDS_PROG_OLDPB)
            {
              return_value = pb_outp (port_base + 2, 4);	// This is a DDS reg, therefore BPW = 4
              if (return_value != 0 && (!(ISA_BOARD)))
                {
                  debug(DEBUG_ERROR, "pb_start_programming: BPW=4 write failed", );
                  return return_value;
                }

              return_value = pb_outp (port_base + 3, device);	// Device = FREQ_REGS, TX_PHASE_REGS, or RX_PHASE_REGS
              if (return_value != 0 && (!(ISA_BOARD)))
                {
                  debug(DEBUG_ERROR, "pb_start_programming: Device=XXX_REGS write failed", );
                  return return_value;
                }

              return_value = pb_outp (port_base + 4, 0);	// Reset mem counter
              if (return_value != 0 && (!(ISA_BOARD)))
                {
                  debug (DEBUG_ERROR, "pb_start_programming: mem counter write failed (REGS)", );
                  return return_value;
                }
            }
        }
    }
  cur_device = device;
  cur_device_addr = 0;

  return 0;
}

SPINCORE_API int
pb_stop_programming (void)
{
  int return_value;

  debug (DEBUG_INFO, "pb_stop_programming: (device=%d)", cur_device);

  if (board[cur_board].is_pcie)
    {
      NULL;
    }
  else if (board[cur_board].usb_method != 2)
    {
      if (!(board[cur_board].is_radioprocessor == 2))
        {
          return_value = pb_outp (port_base + 7, 0);
        
          if (return_value != 0 && (!(ISA_BOARD)))
            {
              return return_value;
            }
        }
    }
  else
    {
      if (cur_device == PULSE_PROGRAM)
        {
          if (board[cur_board].firmware_id == 0x0C13)
            {
              debug (DEBUG_INFO, "pb_stop_programming(PULSE_PROGRAM): Writing shape period information to DDS-I board");
              usb_write_address(board[cur_board].dds_address[0] + 0x6000);
              usb_write_data(shape_period_array[0], 7);
            }
          else if (board[cur_board].firmware_id == 0x0E03)
            {
              debug (DEBUG_INFO, "pb_stop_programming(PULSE_PROGRAM): Writing shape period information to DDS-II board");
              usb_write_address (board[cur_board].dds_address[0] + 0x6000);
              usb_write_data (shape_period_array[0], 7);
              usb_write_address (board[cur_board].dds_address[1] + 0x6000);
              usb_write_data (shape_period_array[1], 7);
            }
          else
            {
              debug (DEBUG_INFO, "pb_stop_programming(PULSE_PROGRAM): Writing shape period information to DDS-II board");
              usb_write_address (board[cur_board].dds_address[0] + 0x0C00);
              usb_write_data (shape_period_array[0], 7);
              usb_write_address (board[cur_board].dds_address[1] + 0x0C00);
              usb_write_data (shape_period_array[1], 7);
            }
        }
        usb_write_address (0);
    }

  cur_device = -1;
  cur_device_addr = 0;

  return 0;
}

SPINCORE_API int
pb_start (void)
{
  int return_value = 0;

  debug(DEBUG_INFO, "pb_start():");
 
  if (board[cur_board].usb_method == 2)
    {
      int start_flag = 0x01;
      usb_write_address (board[cur_board].pb_base_address + 0x00);
      usb_write_data (&start_flag, 1);
    }
  else if (board[cur_board].is_radioprocessor == 2)
    {
      reg_write (board[cur_board].status_reg, 0x01); // trigger
    }
  else if (board[cur_board].is_pcie)
    {
      return_value = pb_outw (1 << 2, 1);
    }
  else
    {
      return_value = pb_outp (port_base + 1, 0);
      if (return_value != 0 && (!(ISA_BOARD)))
        {
          debug(DEBUG_ERROR, "+1 write failed", );
        }
    }

  return return_value;
}

SPINCORE_API int
pb_stop (void)
{
  int return_value = 0;

  debug(DEBUG_INFO, "pb_stop():");
  
  if (board[cur_board].usb_method == 2)
    {
      int stop_flag = 0x02;
      usb_write_address (board[cur_board].pb_base_address + 0x00);
      usb_write_data (&stop_flag, 1);
    }
  else if (board[cur_board].is_radioprocessor == 2)
    {
      reg_write (board[cur_board].status_reg, 0x02); // reset
    }
  else if (board[cur_board].is_pcie)
    {
      // reset
      return_value = pb_outw (0, 1);
    }
	else
    {
      return_value = pb_outp (port_base + 0, 0);
      if (return_value != 0 && (!(ISA_BOARD)))
        {
          return return_value;
        }
      
       return_value = pb_outp (port_base + 2, 0xFF);
      if (return_value != 0 && (!(ISA_BOARD)))
        {
          debug(DEBUG_ERROR, "+2 write failed", );
          return return_value;
        }

      return_value = pb_outp (port_base + 3, 0xFF);
      if (return_value != 0 && (!(ISA_BOARD)))
        {
          debug(DEBUG_ERROR, "+3 write failed", );
          return return_value;
        }

      return_value = pb_outp (port_base + 4, 0xFF);
      if (return_value != 0 && (!(ISA_BOARD)))
        {
          debug(DEBUG_ERROR, "+4 write failed", );
          return return_value;
        }

      return_value = pb_outp (port_base + 7, 0);
      if (return_value != 0 && (!(ISA_BOARD)))
        {
          debug (DEBUG_ERROR, "+7 write failed", );
          return return_value;
        }
    }
   
  return 0;
}

SPINCORE_API int
pb_reset (void)
{
  int return_value = 0;

  debug(DEBUG_INFO, "pb_reset():"); 
  
  if (board[cur_board].usb_method == 2)
    {
      /* Equivalent to pb_stop() for PBDDS-II Boards */
      int stop_flag = 0x02;
      usb_write_address (board[cur_board].pb_base_address + 0x00);
      usb_write_data (&stop_flag, 1);
    }
  else if (board[cur_board].is_radioprocessor == 2)
    {
      reg_write (board[cur_board].status_reg, 0x02); // reset
    }
  else if (board[cur_board].is_pcie)
    {
      // reset
      return_value = pb_outw (0, 1);
    }
  else
    {
      return_value = pb_outp (port_base + 0, 0); /* Software Reset */
      if (return_value != 0 && (!(ISA_BOARD)))
        {
          debug(DEBUG_ERROR, "+0 write failed", );
          return return_value;
        }

      return_value = pb_outp (port_base + 2, 0xFF); /* Latch # Bytes per Instruction Memory Word */
      if (return_value != 0 && (!(ISA_BOARD)))
        {
          debug (DEBUG_ERROR, "+2 write failed", );
          return return_value;
        }

      return_value = pb_outp (port_base + 3, 0xFF); /* Latch Memory Device Number */
      if (return_value != 0 && (!(ISA_BOARD)))
        {
          debug (DEBUG_ERROR, "+3 write failed", );
          return return_value;
        }

      return_value = pb_outp (port_base + 4, 0xFF); /* Reset the Address Counter */
      if (return_value != 0 && (!(ISA_BOARD)))
        {
          debug (DEBUG_ERROR, "+4 write failed", );
          return return_value;
        }

      return_value = pb_outp (port_base + 7, 0); /* Signal Programming Finished */
      if (return_value != 0 && (!(ISA_BOARD)))
        {
          debug (DEBUG_ERROR, "+7 write failed", );
          return return_value;
        }
    }
    
  return return_value;
}

SPINCORE_API int
pb_inst_tworf (int freq, int tx_phase, int tx_output_enable, int rx_phase,
	       int rx_output_enable, int flags, int inst, int inst_data,
	       double length)
{
  unsigned int flag_word;

  // 
  // FIXME: this should check against the values on the BOARD_INFO structure instead
  // of predefined values
  //

  //Check for valid passed parameters
  if (freq < 0 || freq >= board[cur_board].num_freq0)
    {
      debug (DEBUG_ERROR, "pb_inst_tworf: Frequency register out of range.");
      return -99;
    }

  if (tx_phase < 0 || tx_phase >= board[cur_board].num_phase2)
    {
      debug (DEBUG_ERROR, "pb_inst_tworf: TX phase register out of range");
      return -98;
    }
  if (tx_output_enable != ANALOG_OFF)
    {
      tx_output_enable = ANALOG_ON;
    }
  if (rx_phase < 0 || rx_phase >= board[cur_board].num_phase2)
    {
      debug (DEBUG_ERROR, "pb_inst_tworf: RX phase register out of range");
      return -96;
    }
  if (rx_output_enable != ANALOG_OFF)
    {
      rx_output_enable = ANALOG_ON;
    }

  flag_word = (freq << 20) |
    (tx_phase << 16) |
    (!(tx_output_enable) << 11) |
    (rx_phase << 12) | (!(rx_output_enable) << 10) | (flags & MAX_FLAG_BITS);

  debug (DEBUG_INFO, "pb_inst_tworf: using standard PB flag_word partitioning scheme");

  if (board[cur_board].custom_design != 0) {
    debug(DEBUG_WARNING, "WARNING 001: You are using the wrong instruction(i.e. pb_inst_onerf, pb_inst_radio, etc), Please refer to your manual.");
  }

  return pb_inst_pbonly (flag_word, inst, inst_data, length);
}

SPINCORE_API int
pb_inst_onerf (int freq, int phase, int rf_output_enable, int flags, int inst,
	       int inst_data, double length)
{
  return pb_inst_tworf (freq, phase, rf_output_enable, 0, 1, flags, inst, inst_data, length);
}

SPINCORE_API int 
pb_4C_inst(int flag, double length)
{    
    debug(DEBUG_INFO, "Firmware ID: 0x%x\n", board[cur_board].firmware_id);  
      
    if(board[cur_board].firmware_id == 0x1105 || board[cur_board].firmware_id == 0x1106 || board[cur_board].firmware_id == 0x1107)
    {
        int temp = 0;
        int return_value;
        double pb_clock = board[cur_board].clock * board[cur_board].pb_clock_mult;

        unsigned int delay = round_uint ((length * pb_clock) - 1.0);	//(Assumes clock in GHz and length in ns)
        
        if(delay > 0x3FFFFFFF || delay < 2)
        {
             debug (DEBUG_ERROR, "pb_4C_inst:Instruction delay will not work with your board", );
             return -91;
        }

        //writing instruction to memory in this format:
        //  |  31 | 30       | 29 .. 0 |
        //  |Flag | Op-Code  | Delay   |
        // write 8-bits at a time
		temp = 0;
        temp += (flag << 7); // put flag bit in most significant location of byte     
        temp += ((0x3F000000 & delay) >> 24);       // put 3 MSBits of the delay in correct location of byte
        return_value = pb_outp(port_base + 6, temp);

        if (return_value != 0 && (!(ISA_BOARD)))
	    {
	      debug (DEBUG_ERROR, "pb_4C_inst: Communications error (loop 1) : %d", return_value);
	      return return_value;
	    }
	    
        temp = 0;
        temp = ((0x00FF0000 & delay) >> 16);
        return_value = pb_outp(port_base + 6, temp);
        if (return_value != 0 && (!(ISA_BOARD)))
	    {
	      debug (DEBUG_ERROR, "pb_4C_inst: Communications error (loop 2): %d", return_value);
	      return return_value;
	    }
		
	    temp = 0;
        temp = ((0x0000FF00 & delay) >> 8);
        return_value = pb_outp(port_base + 6, temp);
        if (return_value != 0 && (!(ISA_BOARD)))
	    {
	      debug (DEBUG_ERROR, "pb_4C_inst: Communications error (loop 3): %d", return_value);
	      return return_value;
	    }
		
	    temp = 0;
        temp = (0x000000FF & delay);
        return_value = pb_outp(port_base + 6, temp);
        if (return_value != 0 && (!(ISA_BOARD)))
	    {
	      debug (DEBUG_ERROR, "pb_4C_inst: Communications error (loop 4): %d", return_value);
	      return return_value;
	    }
		
		
    }
	else {
		return pb_inst_pbonly(flag, CONTINUE, 0, length);
	}

	return 0;
}

SPINCORE_API int
pb_4C_stop(void)
{
    if(board[cur_board].firmware_id == 0x1105 || board[cur_board].firmware_id == 0x1106 || board[cur_board].firmware_id == 0x1107)
    {
        int temp = 0;
        int return_value;
        double pb_clock = board[cur_board].clock * board[cur_board].pb_clock_mult;

        unsigned int delay = round_uint ((30.0*ns * pb_clock) - 1.0);	//(Assumes clock in GHz and length in ns)
        if(delay > 0x3FFFFFFF || delay < 2)
        {
             debug (DEBUG_ERROR, "pb_4C_inst: Instruction delay will not work with your board", );
             return -91;
        }

        //writing instruction to memory in this format:
        //  |  31 | 30  | 29 .. 0 |
        //  |Flag | Op-Code  | Delay   |
        // write 8-bits at a time    
		
		temp = 0;
        temp += (1 << 6);  // put opcode in correct location
        temp += ((0x3F000000 & delay) >> 24);       // put MSBits of the delay in correct location of byte
        return_value = pb_outp(port_base + 6, temp);
        if (return_value != 0 && (!(ISA_BOARD)))
	    {
	      debug (DEBUG_ERROR, "pb_4C_stop: Communications error (loop 1): %d", return_value);
	      return return_value;
	    }
	    
        temp = 0;
        temp = ((0x00FF0000 & delay) >> 16);
        return_value = pb_outp(port_base + 6, temp);
        if (return_value != 0 && (!(ISA_BOARD)))
	    {
	      debug (DEBUG_ERROR, "pb_4C_stop: Communications error (loop 2): %d", return_value);
	      return return_value;
	    }
		
	    temp = 0;
        temp = ((0x0000FF00 & delay) >> 8);
        return_value = pb_outp(port_base + 6, temp);
        if (return_value != 0 && (!(ISA_BOARD)))
	    {
	      debug (DEBUG_ERROR, "pb_4C_stop: Communications error (loop 3): %d", return_value);
	      return return_value;
	    }

	    temp = 0;
        temp = (0x000000FF & delay);
        return_value = pb_outp(port_base + 6, temp);
        if (return_value != 0 && (!(ISA_BOARD)))
	    {
	      debug (DEBUG_ERROR, "pb_4C_stop: Communications error (loop 4): %d", return_value);
	      return return_value;
	    }

    }
	else {
		return pb_inst_pbonly(0, STOP, 0, 25 * ns);
	}

	return 0;
}

SPINCORE_API int
pb_inst_pbonly (unsigned int flags, int inst, int inst_data, double length)
{
	__int64 flags64 = flags;
	return pb_inst_pbonly64(flags64, inst, inst_data, length);
}

SPINCORE_API int
pb_inst_pbonly64 (__int64 flags, int inst, int inst_data, double length)
{
  unsigned int delay;
  double pb_clock, clock_period;

  pb_clock = board[cur_board].clock * board[cur_board].pb_clock_mult;
  clock_period = 1.0 / pb_clock;

  delay = round_uint ((length * pb_clock) - 3.0);	//(Assumes clock in GHz and length in ns)

  debug (DEBUG_INFO, "pb_inst_pbonly: inst=%lld, inst_data=%d,length=%f, flags=0x%.8x", inst, inst_data,
	 length, flags);

  // make sure delay was not made based on a negative number
  if (delay < 2 || length*pb_clock <= 3)
    {
      debug (DEBUG_ERROR, "pb_inst_pbonly: Instruction delay is too small to work with your board", );
      return -91;
    }

  if (inst == LOOP)
    {
      if (inst_data == 0)
	{
	  debug (DEBUG_ERROR, "pb_inst_pbonly: Number of loops must be 1 or more");
	  return -1;
	}
      inst_data -= 1;
    }
  if (inst == LONG_DELAY)
    {
      if (inst_data == 0 || inst_data == 1)
	{
	  debug (DEBUG_ERROR, "pb_inst_pbonly: Number of repetitions must be 2 or more");
	  return -1;
	}
      inst_data -= 2;
    }

  //-------------------PB CORE counter issue--------------------------------------------------------------------------------------------------------------------------------------------------
  //An extra clock cycle must be subtracted from all instructions that result in a value ending in 0xFF being sent to the core counter (with the exception of 0x0FF).
  //Boards which have been fixed (and which have readable firmware IDs) do not require this and will bypass the following software fix.
  //
  //For boards which have been fixed but do not have firmware registers, there is no way for spinapi to know whether or not the fault has been corrected.
  //Therefore, on all generic PulseBlaster boards and also on the older PBESR boards (boards using AMCC_DEVID and PBESR_PRO_DEVID) the 'FF' fix will
  //be applied by default.  If you wish to bypass this fix, please use:
  //      pb_bypass_FF_fix (1);     //bypass the fix below - no extra clock cycle will be subtracted ( board[cur_board].has_FF_fix will be set to 1 )
  //      pb_bypass_FF_fix(0):    //turn on the software fix - ( board[cur_board].has_FF_fix will be set to 0 )
  //
  if (board[cur_board].has_FF_fix != 1)
    {
      if (((delay & 0xFF) == 0xFF) && (delay > 0xFF))
	{
	  delay--;
	  debug (DEBUG_ERROR, "pb_inst_pbonly: __ONE CLOCK CYCLE SUBTRACTED__",);
	}
    }
  //_______________________________________________________________________________________________________________

  //------------------------
  // SP16 Designs 15-1, 15-2, and 15-3 have Flag0 and Flag1 reversed in Firmware
  if( (board[cur_board].firmware_id > 0xF0) && (board[cur_board].firmware_id <= 0xF3) )
      flags = (flags & 0xFFFFFFFC) + ((flags & 0x01) << 1) + ((flags & 0x02) >> 1);

  return pb_inst_direct (((int*)&flags), inst, inst_data, delay);
}

SPINCORE_API int
pb_inst_dds2 (int freq0, int phase0, int amp0, int dds_en0, int phase_reset0,
	      int freq1, int phase1, int amp1, int dds_en1, int phase_reset1,
	      int flags, int inst, int inst_data, double length)
{
  if (board[cur_board].firmware_id != 0xe01 && board[cur_board].firmware_id != 0xe02 && board[cur_board].firmware_id != 0x0E03 && board[cur_board].firmware_id != 0x0C13)
    {
      debug(DEBUG_ERROR, "pb_inst_dds2: Your current board does not support this function. Please check your manual.");
      return 0;

    }

  if (freq0 >= (int)board[cur_board].dds_nfreq[0] || freq0 < 0)
    {
      debug (DEBUG_ERROR, "pb_inst_dds2: Frequency register select 0 out of range", );
      return -1;
    }

  if (freq1 >= (int)board[cur_board].dds_nfreq[1] || freq1 < 0)
    {
      debug (DEBUG_ERROR, "pb_inst_dds2: Frequency register select 1 out of range", );
      return -1;
    }

  if (phase0 >= (int)board[cur_board].dds_nphase[0] || phase0 < 0)
    {
      debug (DEBUG_ERROR, "pb_inst_dds2: TX phase register select 0 out of range", );
      return -1;
    }

  if (phase1 >= (int)board[cur_board].dds_nphase[1] || phase1 < 0)
    {
      debug (DEBUG_ERROR, "pb_inst_dds2: TX phase register select 1 out of range", );
      return -1;
    }

  if (amp0 >= (int)board[cur_board].dds_namp[0] || amp0 < 0)
    {
      debug (DEBUG_ERROR, "pb_inst_dds2: Amplitude register select 0 out of range", );
      return -1;
    }

  if (amp1 >= (int)board[cur_board].dds_namp[1] || amp1 < 0)
    {
      debug (DEBUG_ERROR, "pb_inst_dds2: Amplitude register select 1 out of range", );
      return -1;
    }

  debug(DEBUG_INFO, "pb_inst_dds2: using DDS 96 bit partitioning scheme(no shape support)", inst, inst_data, length);

  unsigned int delay;
  double pb_clock, clock_period;

  pb_clock = board[cur_board].clock * board[cur_board].pb_clock_mult;
  clock_period = 1.0 / pb_clock;

  delay = round_uint ((length * pb_clock) - 3.0);	//(Assumes clock in GHz and length in ns)

  debug(DEBUG_INFO, "pb_inst_dds2: using DDS 96 bit partitioning scheme(no shape support)", inst, inst_data, length);
  debug (DEBUG_INFO, "pb_inst_dds2: inst=%d, inst_data=%d,length=%f", inst, inst_data, length);
  debug (DEBUG_INFO, "pb_inst_dds2: freq0=0x%X, phase0=0x%X, amp0=0x%X, freq1=0x%X, phase1=0x%X, amp1=0x%X",freq0,phase0,amp0,freq1,phase1,amp1);

  // make sure delay was not made based on a negative number
  if (delay < 2 || length*pb_clock <= 3)
    {
      debug (DEBUG_ERROR, "pb_inst_dds2: Instruction delay is too small to work with your board", );
      return -91;
    }

  if (inst == LOOP)
    {
      if (inst_data == 0)
		{
		 debug (DEBUG_ERROR, "pb_inst_dds2: Number of loops must be 1 or more", );
		  return -1;
		}
      inst_data -= 1;
    }

  if (inst == LONG_DELAY)
    {
      if (inst_data == 0 || inst_data == 1)
	{
	  debug (DEBUG_ERROR, "pb_inst_dds2: Number of repetitions must be 2 or more",);
	  return -1;
	}
      inst_data -= 2;
    }
  int flag_word[3];

  flag_word[0] = flag_word[1] = flag_word[2] = 0;
  
  if(board[cur_board].firmware_id == 0x0C13)
  {
	  flag_word[0] |= (flags & 0xF) << 0;        // 4 Flag Bits
	  flag_word[0] |= (dds_en0 & 0x1) << 4;      // DDS Tx Enable
	  flag_word[0] |= (phase_reset0 & 0x1) << 5; // Phase Reset
	  flag_word[0] |= (freq0 & 0x3FF) << 6;      // 10 Frequency Select Bits (1024 Freq. Registers)
	  flag_word[0] |= (phase0 & 0x7F) << 16;     // 7 Phase Select Bits (128 Phase Registers)
	  flag_word[0] |= (amp0 & 0x1FF) << 23;      // lower 9 of 10 Amp. Select Bits
	  
	  flag_word[1] |= (amp0 & 0x200) >> 9;       // upper 1 of 10 Amp. Select Bits.
  }
  else if(board[cur_board].firmware_id == 0x0E03)
  {
    flag_word[0] |= (flags & 0xF) << 0;           // 4 Flag Bits
    flag_word[0] |= (dds_en0 & 0x1) << 4;         // DDS1 Tx Enable
    flag_word[0] |= (dds_en1 & 0x1) << 5;         // DDS2 Tx Enable
    flag_word[0] |= (phase_reset0 & 0x1) << 6;    // DDS1 Phase Reset
    flag_word[0] |= (phase_reset1 & 0x1) << 7;    // DDS2 Phase Reset
    flag_word[0] |= (freq0 & 0x3FF) << 8;         // DDS1 Frequency Select Bits (1024 Freq. Registers)
    flag_word[0] |= (freq1 & 0x3FF) << 18;        // DDS2 Frequency Select Bits (1024 Freq. Registers)
    flag_word[0] |= (phase0 & 0xF) << 28;         // Lower 4 DDS1 Phase Select Bits (128 Phase Registers)

    flag_word[1] |= (phase0 & 0x70) >> 4;         // Upper 3 DDS1 Phase Select Bits
	flag_word[1] |= (phase1 & 0x7F) << 3;         // DDS2 Phase Select Bits (128 Phase Registers)
    flag_word[1] |= (amp0 & 0x3FF) << 10;         // DDS1 Amplitude Select Bits (1024 Amp. Registers)
    flag_word[1] |= (amp1 & 0x3FF) << 20;         // DDS2 Amplitude Select Bits (1024 Amp. Registers)
  }
  else
  {
    flag_word[0] |= (flags & 0xFFF) << 0;
    flag_word[0] |= (dds_en0 & 0x1) << 12;
    flag_word[0] |= (dds_en1 & 0x1) << 13;
    flag_word[0] |= (phase_reset0 & 0x1) << 14;
    flag_word[0] |= (phase_reset1 & 0x1) << 15;
    flag_word[0] |= (freq0 & 0xF) << 16;
    flag_word[0] |= (freq1 & 0xF) << 20;
    flag_word[0] |= (phase0 & 0x7) << 24;
    flag_word[0] |= (phase1 & 0x7) << 27;
    flag_word[0] |= (amp0 & 0x3) << 30;

    flag_word[1] |= (amp1 & 0x3) << 0;
  }

  return pb_inst_direct(flag_word, inst, inst_data, delay);
}

SPINCORE_API int
pb_inst_direct (const int *pflags, int inst, int inst_data_direct, int length)
{
  int instruction[8];
  int i;
  int flags;
  int return_value;
  unsigned int temp_byte;
  unsigned int BIT_MASK = 0xFF0000;
  unsigned int OCW = 0;
  unsigned int OPCODE = 0;
  unsigned int DELAY = 0;

  if (board[cur_board].usb_method == 2)
    {
      instruction[0] = length;
      instruction[1] = (0xF & inst) | ((0xFFFFF & inst_data_direct) << 4) | ((0xFF & pflags[0]) <<24);
      instruction[2] = ((0xFFFFFF & (pflags[0] >> 8)) << 0) | ((pflags[1] & 0xFF) << 24);
      instruction[3] = ((0xFFFFFF & (pflags[1] >> 8)) << 0) | ((pflags[2] & 0xFF) << 24);
      instruction[4] = 0;
      instruction[5] = 0;
      instruction[6] = 0;
      instruction[7] = 0;

      debug (DEBUG_INFO, "pb_inst_direct: Programming DDS2 IMW: 0x%X %X %X %X.\n", instruction[3], instruction[2], instruction[1], instruction[0]);

      if(board[cur_board].firmware_id == 0x0E03)
        usb_write_data (instruction, 8);
      else
        usb_write_data (instruction, 4);
    }
  else
    {
      // Make sure the different fields of the instruction are within 
      // the proper range
      if (board[cur_board].firmware_id == 0xa13 || board[cur_board].firmware_id == 0xC10)
        {  //Need to replace this asap.
          flags = pflags[0];
          if (flags != (flags & 0x0FFFFFFFF))
            {
              debug (DEBUG_ERROR, "Flag word is limited to 32 bits", );
              return -1;
            }
        }
      else {
        flags = pflags[0];
        if (flags != (flags & 0x0FFFFFF)) {
					debug (DEBUG_ERROR, "pb_inst_direct: Flag word is limited to 24 bits", );
          return -1;
        }
      }

      if (inst > 8) {
					debug (DEBUG_ERROR, "pb_inst_direct: Invalid opcode",);
          return -1;
      }
      
			if (inst_data_direct != (inst_data_direct & 0x0FFFFF)) {
					debug (DEBUG_ERROR, "Invalid opcode",);
          return -1;
      }

      OPCODE = (inst) | (inst_data_direct << 4);
      OCW = flags;
      DELAY = length;

			debug (DEBUG_INFO, "pb_inst_direct: OPCODE=0x%x, flags=0x%.8x, delay=%d", OPCODE, OCW, DELAY);

      if (board[cur_board].firmware_id == 0xa13 || board[cur_board].firmware_id == 0xC10) { 
        for (i = 0; i < 4; i++) {
          temp_byte = 0xFF000000 & OCW;
          temp_byte >>= 24;
          return_value = pb_outp (port_base + 6, temp_byte);
					
          if (return_value != 0 && (!(ISA_BOARD))) {
						debug (DEBUG_ERROR, "pb_inst_direct: Communications error (loop 1): %d", return_value);
            return return_value;
          }
          OCW <<= 8;
        }
      }
      else if (board[cur_board].firmware_id == 0x0908) {  
        temp_byte = 0xFF & OCW;
        return_value = pb_outp (port_base + 6, temp_byte);
        if (return_value != 0 && (!(ISA_BOARD))) {
					debug (DEBUG_ERROR, "pb_inst_direct: Communications error (loop 1): %d", return_value);
          return return_value;
        }
      }
      else if (board[cur_board].is_pcie) {
          unsigned int baddr;

          // Word addressing, and each IMW is on a 128bit boundary
          baddr = board[cur_board].pb_base_address + num_instructions * 4;
          instruction[0] = DELAY;
          instruction[1] = OPCODE | (OCW << 24);
          instruction[2] = OCW >> 8;
					
          for (i = 0; i < 3; i++) {
              // write to same location 3 times, that is how the data is written
              return_value = pb_outw (baddr, instruction[i]);
              if (return_value) {
									debug (DEBUG_ERROR, "pb_inst_direct: Communications error (pcie): %d", return_value);
                  return return_value;
              }
					}
					
          goto done;
      }
      else {
					for (i = 0; i < 3; i++) {
             temp_byte = BIT_MASK & OCW;
             temp_byte >>= 16;
             return_value = pb_outp (port_base + 6, temp_byte);
						 
             if (return_value != 0 && (!(ISA_BOARD))) {
							debug (DEBUG_ERROR, "pb_inst_direct: Communications error (loop 1): %d", return_value);
              return return_value;
						 }
             
						 OCW <<= 8;
          }
      }
			
      BIT_MASK = 0xFF0000;
      for (i = 0; i < 3; i++) {
          temp_byte = BIT_MASK & OPCODE;
          temp_byte >>= 16;
          return_value = pb_outp (port_base + 6, temp_byte);
					
          if (return_value != 0 && (!(ISA_BOARD))) {
							debug (DEBUG_ERROR, "pb_inst_direct: Communications error (loop 2): %d", return_value);
              return return_value;
          }
					
          OPCODE <<= 8;
      }
				
      BIT_MASK = 0xFF000000;
      for (i = 0; i < 4; i++) {
          temp_byte = BIT_MASK & DELAY;
          temp_byte >>= 24;
          return_value = pb_outp (port_base + 6, temp_byte);
          if (return_value != 0 && (!(ISA_BOARD))) {
						debug (DEBUG_ERROR, "pb_inst_direct: Communications error (loop 3): %d", return_value);
            return return_value;
          }
          DELAY <<= 8;
      }
    }
		
done:
  num_instructions += 1;
  return num_instructions - 1;
}

SPINCORE_API int
pb_set_freq (double freq)
{
  unsigned int freq_byte = 0xFF000000;	//Bit Mask to send 1 byte at a time
  double dds_clock;
  unsigned int freq_word;
  unsigned int freq_word2;
  unsigned int temp_byte;
  int return_value;
  int i = 0;

  dds_clock = board[cur_board].clock;
  freq_word =  round_uint (((freq * pow232) / (dds_clock * 1000.0)));	// Desired data to trasnfer
  freq_word2 = round_uint (((freq * pow232) / (dds_clock * 1000.0 * board[cur_board].dds_clock_mult)));

  debug(DEBUG_INFO, "pb_set_freq: address:%d freq:%lf freq_word:%x freq_word2:%x clock:%lf", cur_device_addr, freq, freq_word, freq_word2, dds_clock);

  if (board[cur_board].usb_method == 2)
    {
      if (cur_device_addr >= (int)board[cur_board].dds_nfreq[cur_dds])
        {
          debug (DEBUG_ERROR, "pb_set_freq: Frequency registers full", );
          return -1;
        }

      usb_write_data (&freq_word2, 1);
    }
  else
    {
      // Check if use has already written to all registers
      if (cur_device_addr >= board[cur_board].num_freq0)
        {
          debug (DEBUG_ERROR, "pb_set_freq: Frequency registers full",);
          return -1;
        }

      switch(board[cur_board].dds_prog_method)
        {
          case DDS_PROG_OLDPB:
            debug (DEBUG_INFO, "pb_set_freq: using old programming method");
            for (i = 0; i < 4; i++)	// Loop to send 4 bytes
              {
                temp_byte = freq_byte & freq_word;	// Get current byte to transfer
                temp_byte >>= 24;	// Shift data into LSB
                return_value = pb_outp (port_base + 6, temp_byte);	// Send byte to PulseBlasterDDS
                if (return_value != 0 && (!(ISA_BOARD)))
                  {
                    return -1;
                  }

                freq_word <<= 8;	// Shift word up one byte so that next byte to transfer is in MSB
              }
            break;
          case DDS_PROG_RPG:
            debug (DEBUG_INFO, "pb_set_freq: using RPG method");
            dds_freq_rpg (cur_board, cur_device_addr, freq);
            break;
          default:
            debug (DEBUG_INFO, "pb_set_freq: using new programming method");
            dds_freq_extreg (cur_board, cur_device_addr, freq_word, freq_word2);
            break;
        }
    }

  cur_device_addr++;

  return 0;
}

SPINCORE_API int
pb_set_phase (double phase)
{
  unsigned int phase_byte = 0xFF000000;	//Bit Mask to send 1 byte at a time

  double temp = phase / 360.0;

  // fix phase to be 0 <phase <360.
  while (temp >= 1.0)
    {
      temp -= 1.0;
    }
  while (temp < 0.0)
    {
      temp += 1.0;
    }

  double temp2 = temp * pow232;
  unsigned int phase_word = round_uint (temp2);

  unsigned int temp_byte;
  int return_value;
  int i = 0;

  if (board[cur_board].usb_method == 2)
    {
      // Check if user has already written to all registers
      if (cur_device_addr >= (int)board[cur_board].dds_nphase[cur_dds])
        {
          debug (DEBUG_ERROR, "pb_set_phase: Phase registers full", );
          return -1;
        }
      phase_word >>= 20;

      debug (DEBUG_INFO, "pb_set_phase: phase word: 0x%x", phase_word);
      usb_write_data (&phase_word, 1);
    }
  else
    {
      int max_phase_regs = 0;

      if (cur_device == COS_PHASE_REGS)
        {
          max_phase_regs = board[cur_board].num_phase0;
        }
      if (cur_device == SIN_PHASE_REGS)
        {
          max_phase_regs = board[cur_board].num_phase1;
        }
      if (cur_device == TX_PHASE_REGS)
        {
          if (board[cur_board].is_radioprocessor)
            {
              max_phase_regs = board[cur_board].num_phase2;
            }
          else
            {
              max_phase_regs = board[cur_board].num_phase1;
            }
        }
      if (cur_device == RX_PHASE_REGS)
        {
          max_phase_regs = board[cur_board].num_phase0;
        }

      // Check if use has already written to all registers
      if (cur_device_addr >= max_phase_regs)
        {
          debug (DEBUG_ERROR, "pb_set_phase: Phase registers full", );
          return -1;
        }

      if (board[cur_board].dds_prog_method == DDS_PROG_OLDPB)
        {
          for (i = 0; i < 4; i++)	// Loop to send 4 bytes
            {
              temp_byte = phase_byte & phase_word;	// Get current byte to transfer
              temp_byte >>= 24;	// Shift data into LSB
              return_value = pb_outp (port_base + 6, temp_byte);	// Send byte to PulseBlasterDDS
              if (return_value != 0 && (!(ISA_BOARD)))	// conio's _outp returns value passed to it
                {
                  return -1;
                }

              phase_word <<= 8;	// Shift word up one byte so that next byte to transfer is in MSB
            }
        }
      else if (board[cur_board].is_radioprocessor == 2)
        {
          dds_phase_rpg (cur_board, cur_device, cur_device_addr, phase);
        }
      else
        {
          dds_phase_extreg (cur_board, cur_device, cur_device_addr, phase_word);
        }
    }

  cur_device_addr++;

  return 0;
}

SPINCORE_API int
pb_read_status (void)
{
  int status;
  status = 0;

  if (board[cur_board].usb_method == 2) 
    {
      debug (DEBUG_INFO, "pb_read_status: Using partial address decoding method.");
      return status = reg_read (board[cur_board].pb_base_address);
    }
  else if (board[cur_board].status_oldstyle) 
    {
      debug (DEBUG_INFO, "pb_read_status: using oldstyle");
      status =  pb_inp (0) & 0xF;
    }
  else if (board[cur_board].is_radioprocessor == 2)
    {
      status = reg_read (board[cur_board].status_reg);
    }
  else if (board[cur_board].is_pcie)
    {
      status = reg_read_simple (REG_EXPERIMENT_RUNNING << 2);
    }
  else
    {
      status = reg_read (REG_EXPERIMENT_RUNNING);
    }
	
	return status;
}
 
SPINCORE_API const char
*pb_status_message(void)
{
    int message_count=0;
    int status=pb_read_status();
    
    if(status < 0){
        strcpy (status_message, "Status error: ");
        if(status == -1)
        {
            strcat (status_message, "can't communicate with board.");
        }
        else if(status == -2)
        {
            strcat (status_message, "connection with the board timed out while sending address.");
        }
        else if(status == -3)
        {
            strcat (status_message, "connection with board timed out while receiving data.");
        }
        else
        {
            strcat (status_message, "can't communicate with board.");
        }
        strcat (status_message, "\nTry reinstalling SpinAPI.\n");
    }
    else
    {
        strcpy (status_message,"Board is ");
        
        if((status&0x01)!=0x00){
            //Stopped
            strcat(status_message,"stopped");
            message_count++;
        }
        if((status&0x02)!=0x00){
            //Reset
            if(message_count>0){
                strcat(status_message," and ");   
            }
            strcat(status_message,"reset");
            message_count++;
        }
        if((status&0x04)!=0x00){
            //Running
            if(message_count>0){
                strcat(status_message," and ");   
            }
            strcat(status_message,"running");
            message_count++;
        }
        if((status&0x08)!=0x00){
            //Waiting
            if(message_count>0){
                strcat(status_message," and ");   
            }
            strcat(status_message,"waiting");
            message_count++;
        }
        if((status&0x10)!=0x00){
            //Scanning
            if(message_count>0){
                strcat(status_message," and ");   
            }
            strcat(status_message,"scanning");
            message_count++;
        }
        strcat(status_message,".\n"); 
    }
    return status_message;
}

SPINCORE_API const char *
pb_get_version (void)
{
  return version;
}

SPINCORE_API int
pb_get_firmware_id (void)
{
  if (board[cur_board].has_firmware_id)
    {

      debug (DEBUG_INFO, "pb_get_firmware_id: has id");
      /*
        switch(board[cur_board].has_firmware_id) 
          {
            case 1:
              return reg_read(REG_FIRMWARE_ID);    
              break;
            case 2:
              return reg_read(0x15); // usb boards have the firmware ID stored in register 0x15
              break;
            case 3:
              return reg_read(REG_FIRMWARE_ID_RPG);
              break;
            default:
              return 0;
              break;
          }
      */
      return board[cur_board].firmware_id;
    }
  else
    {
      return 0;
    }
}

SPINCORE_API void
pb_set_ISA_address (int address)
{
  port_base = address;
}

///
/// Low level IO functions. Typically the end user will use the above functions
/// to access the hardware, and these functions are mainly included in the
/// API for backwards compatibility.
///

SPINCORE_API int
pb_outp (unsigned int address, unsigned char data)
{
  // If this is a USB device...
  if (board[cur_board].is_usb)
    {
      debug (DEBUG_INFO, "pb_outp: addr %x, data %x. Using the USB protocol.", address, data);
        return usb_do_outp (address, data);
    }
  else 
    {  // Otherwise, if it is a PCI device...
      if (board[cur_board].use_amcc == 1) {
        debug (DEBUG_INFO, "pb_outp: addr %x, data %x. Using the AMCC protocol.", address, data);
        return do_amcc_outp (cur_board, address, data);
      }
      else if (board[cur_board].use_amcc == 2) {
        debug (DEBUG_INFO, "pb_outp: addr %x, data %x. Using the AMCC protocol (old).", address, data);
        return do_amcc_outp_old (cur_board, address, data);
      }
      else {
        debug (DEBUG_INFO, "pb_outp: addr %x, data %x. Using the direct protocol.", address, data);
        return os_outp (cur_board, address, data);
      }
    }
}

SPINCORE_API char
pb_inp (unsigned int address)
{
  if (board[cur_board].is_usb)
    {
      debug (DEBUG_ERROR, "pb_inp: no support for usb devices");
      return -1;
    }

  if (board[cur_board].use_amcc)
    {
      if (board[cur_board].use_amcc == 2)
        {
          debug (DEBUG_ERROR, "pb_inp: Input from board not supported with this board revision", );
          return -1;
        }
      return do_amcc_inp (cur_board, address);
    }
  else
    {
      return os_inp (cur_board, address);
    }
}

SPINCORE_API int
pb_outw (unsigned int address, unsigned int data)
{
  if (board[cur_board].is_usb)
    {
      debug (DEBUG_ERROR, "pb_outw: no support for usb devices");
      return -1;
    }

  // amcc chip does not use 32 bit I/O, so this must be our custom PCI core
  return os_outw (cur_board, address, data);
}

SPINCORE_API unsigned int
pb_inw (unsigned int address)
{
  if (board[cur_board].is_usb)
    {
      debug (DEBUG_ERROR, "pb_inw: no support for usb devices");
      return -1;
    }

  // amcc chip does not use 32 bit I/O, so this must be our custom PCI core
  return os_inw (cur_board, address);
}

SPINCORE_API void
pb_sleep_ms (int milliseconds)
{
#if defined(WINDOWS) || defined(WIN32)
  Sleep (milliseconds);		// on windows, sleep() function takes values in ms.
#else
#include <unistd.h>
  usleep (milliseconds * 1000);	// this linux function takes time in us
#endif
}

int
do_os_init (int board)
{
  int dev_id;

  debug (DEBUG_INFO, "do_os_init: board # %d", board);
  debug (DEBUG_INFO, "do_os_init: num_pci_boards: %d", num_pci_boards);
  debug (DEBUG_INFO, "do_os_init: num_usb_devices: %d", num_usb_devices);


  if (board < num_pci_boards)
    {
      debug (DEBUG_INFO, "do_os_init: initializing pci");
      dev_id = os_init (board);
    }
  else
    {
      debug (DEBUG_INFO, "do_os_init: initializing usb");
      dev_id = os_usb_init (board - num_pci_boards);
      usb_reset_gpif (board - num_pci_boards);
    }

  return dev_id;
}

int
do_os_close (int board)
{
  int ret = -1;

  if (board < num_pci_boards)
    {
      debug (DEBUG_INFO, "do_os_close: closing pci");
      ret = os_close (board);
    }
  else
    {
      debug (DEBUG_INFO, "do_os_close: closing usb");
      ret = os_usb_close ();
    }

  return ret;
}

SPINCORE_API void
pb_bypass_FF_fix (int option)
{
  switch (option)
    {
    case 1:
      {
        debug
          (DEBUG_INFO, "pb_bypass_FF_fix: bypassing software fix.. no clock cycles will be subtracted from 0x..FF delays.");
        board[cur_board].has_FF_fix = 1;
        break;
      }
    case 0:
      {
        debug
          (DEBUG_INFO, "pb_bypass_FF_fix: software fix turned on: one clock cycle will be subtracted from 0x..FF delays.");
        board[cur_board].has_FF_fix = 0;
        break;
      }
    default:
      {
        debug (DEBUG_INFO, "pb_bypass_FF_fix: invalid argument. please enter 1 to bypass or 0 to enable.\n");
        break;
      }
    }

}

SPINCORE_API int
pb_inst_hs8(const char* Flags, double length)
{
     int i;
     int num_cycles;
     char hex_flags0;
     double clock_freq = board[cur_board].clock;
     
     //Check for 8-bits 
     if(strlen(Flags) != 8)
     {
        debug(DEBUG_ERROR, "pb_inst_hs8: Must define a value (1 or 0) for all 8 bits!",);
        return -2;
     }
     
     //Verify all bits are either 0 or 1 
     for(i=0;i<8;i++)
     {
        if((Flags[i] > 49) || (Flags[i] < 48))
        {
           debug(DEBUG_ERROR, "pb_inst_hs8: Flag bits must be either 0 or 1! flag[%d]: %d", i, (Flags[i]));
           return -3;
        }
     }
     
     //Convert the string of ones and zeros to an 8-bit decimal number
     hex_flags0 =(Flags[0] - 48)*128 + 
                 (Flags[1] - 48)*64 + 
                 (Flags[2] - 48)*32 + 
                 (Flags[3] - 48)*16 + 
                 (Flags[4] - 48)*8 + 
                 (Flags[5] - 48)*4 + 
                 (Flags[6] - 48)*2 + 
                 (Flags[7] - 48)*1;
                 
     
     //Convert the length from nanoseconds to a number of clock cycles        
     num_cycles = round_int(length*clock_freq); 
     if(num_cycles < 1)
     {
        debug(DEBUG_ERROR, "pb_inst_hs8: Length must be greater than or equal to one clock period",);
        return -4;
     }
     
     //Each pb_outp instruction controls the output for one clock cycle,
     //  so send this line to the board as many times as it takes to
     //  create the requested instruction length.
     for (i = 1; i <= num_cycles; i++)
         pb_outp(6,hex_flags0);     
        
     return num_cycles;
}

SPINCORE_API int
pb_inst_hs24(const char* Flags, double length)
{
     int i,num_cycles;
     char hex_flags0,hex_flags1,hex_flags2;
     double clock_freq = board[cur_board].clock;

     //Check for 24-bits 
     if(strlen(Flags) != 24)
     {
        debug(DEBUG_ERROR, "pb_inst_hs24: Must define states (1 or 0) for all 24 bits!");
        return -2;
     }
     
     //Verify all bits are either 0 or 1 
     for(i=0;i<24;i++)
     {
        if(Flags[i] > 49 || Flags[i] < 48)
        {
           debug(DEBUG_ERROR, "pb_inst_hs24: Flag bits must be either 0 or 1",);
           return -3;
        }
     }
     
     //Convert the string of ones and zeros to an 8-bit decimal number 
     hex_flags0 =(Flags[0] - 48)*128 + 
                 (Flags[1] - 48)*64 + 
                 (Flags[2] - 48)*32 + 
                 (Flags[3] - 48)*16 + 
                 (Flags[4] - 48)*8 + 
                 (Flags[5] - 48)*4 + 
                 (Flags[6] - 48)*2 + 
                 (Flags[7] - 48)*1;
     hex_flags1 =(Flags[8] - 48)*128 + 
                 (Flags[9] - 48)*64 + 
                 (Flags[10] - 48)*32 + 
                 (Flags[11] - 48)*16 + 
                 (Flags[12] - 48)*8 + 
                 (Flags[13] - 48)*4 + 
                 (Flags[14] - 48)*2 + 
                 (Flags[15] - 48)*1; 
     hex_flags2 =(Flags[16] - 48)*128 + 
                 (Flags[17] - 48)*64 + 
                 (Flags[18] - 48)*32 + 
                 (Flags[19] - 48)*16 + 
                 (Flags[20] - 48)*8 + 
                 (Flags[21] - 48)*4 + 
                 (Flags[22] - 48)*2 + 
                 (Flags[23] - 48)*1;
                 
     
     //Convert the length from nanoseconds to a number of clock cycles        
     num_cycles = round_int(length*clock_freq);
     if(num_cycles < 1)
     {
        debug(DEBUG_ERROR, "pb_inst_hs24: Length must be greater than or equal to one clock period");
        return -4;
     } 
     
     //Each pb_outp instruction controls the output for one clock cycle,
     //  so send this line to the board as many times as it takes to
     //  create the requested instruction length.
     for (i = 1; i <= num_cycles; i++)
     {
         pb_outp(6,hex_flags0);
         pb_outp(6,hex_flags1);
         pb_outp(6,hex_flags2);
     }        
        
     return num_cycles;
}


SPINCORE_API int
pb_select_dds (int dds_num)
{
  if (board[cur_board].firmware_id == 0xe01 || board[cur_board].firmware_id == 0xe02 || board[cur_board].firmware_id == 0x0E03)
    {
      if (dds_num >= 0 && dds_num <= board[cur_board].number_of_dds)
        {
          debug (DEBUG_INFO, "pb_select_dds: Setting current dds to dds #%d.", dds_num);
          cur_dds = dds_num;
        }
    }
  else if (board[cur_board].is_radioprocessor)
    {
      debug (DEBUG_INFO, "RadioProcessor only has one DDS, setting cur_dds to 0.");
      cur_dds = 0;
    }
  else
    {
      debug(DEBUG_ERROR,"pb_select_dds: Your current board does not support this function.");
	  return -1;
    }

  return 0;
}

SPINCORE_API int
pb_set_isr (int irq_num, unsigned int isr_addr)
{
  if (board[cur_board].firmware_id != 0xe01 && board[cur_board].firmware_id != 0xe02 && board[cur_board].firmware_id != 0x0E03)
    {
      debug(DEBUG_ERROR, "pb_set_isr: Your current board does not support this function.");
      return -1;
    }

  if (irq_num < 0 || irq_num > 3)
    {
      debug (DEBUG_ERROR, "pb_set_isr: The IRQ number specified is invalid.");
      return -1;
    }

  usb_write_address (board[cur_board].pb_base_address + 0x03 + irq_num);
  usb_write_data (&isr_addr, 1);
  debug (DEBUG_INFO, "pb_set_isr: IRQ #%d set to ISR Address 0x%x.", irq_num, isr_addr);

  return 0;

}
SPINCORE_API int
pb_set_irq_enable_mask (char mask)
{
  int imask = (int) mask;

  if (board[cur_board].firmware_id != 0xe01 && board[cur_board].firmware_id != 0xe02 && board[cur_board].firmware_id != 0x0E03)
    {
      debug(DEBUG_ERROR, "pb_set_irq_enable_mask: Your current board does not support this function.");
      return -1;
    }

  usb_write_address (board[cur_board].pb_base_address + 0x01);
  usb_write_data (&imask, 1);
  debug (DEBUG_INFO, "pb_set_irq_enable_mask: IRQ Enable Mask set to 0x%x.", mask & 0x0F);

  return 0;
}
SPINCORE_API int
pb_set_irq_immediate_mask (char mask)
{
  int imask = (int) mask;

  if (board[cur_board].firmware_id != 0xe01 && board[cur_board].firmware_id != 0xe02 && board[cur_board].firmware_id != 0x0E03)
    {
      debug(DEBUG_ERROR, "pb_set_irq_immediate_mask: Your current board does not support this function.");
      return -1;
    }

  usb_write_address (board[cur_board].pb_base_address + 0x02);
  usb_write_data (&imask, 1);
  debug (DEBUG_INFO, "pb_set_irq_immediate_mask: IRQ Immediate Mask set to 0x%x.", mask & 0x0F);

  return 0;
}

SPINCORE_API int
pb_generate_interrupt (char mask)
{
  int imask = (int) mask;

  if (board[cur_board].firmware_id != 0xe01 && board[cur_board].firmware_id != 0xe02 && board[cur_board].firmware_id != 0x0E03)
    {
      debug (DEBUG_ERROR, "pb_generate_interrupt: Your current board does not support this function.");
      return -1;
    }
  imask = (imask & 0xF) << 4;	//Shift into the IRQ control bits.
  usb_write_address (board[cur_board].pb_base_address + 0x00);
  usb_write_data (&imask, 1);

  debug (DEBUG_INFO, "pb_generate_interrupt: IRQ Mask set to 0x%x.", mask & 0x0F);

  return 0;
}

SPINCORE_API int
pb_write_register (unsigned int address, unsigned int value)
{
  if (board[cur_board].usb_method != 2) {
      reg_write(address, value);
  }
  else {
	usb_write_address (address);
	usb_write_data (&value, 1);
  }
  
  debug (DEBUG_INFO, "pb_write_register: Wrote 0x%x to 0x%x.", value, address);

  return 0;
}

SPINCORE_API 
int pb_select_core (unsigned int core_sel)
{
    reg_write (REG_CORE_SEL, core_sel);
    debug (DEBUG_INFO, "pb_select_core: Wrote 0x%x.", core_sel);
    return 0;
}

SPINCORE_API 
int pb_set_pulse_regs (unsigned int channel, double period, double clock_high, double offset)
{  
    int data[3];
    
	// period
    data[0] = (int)(period/20.0);
    // clock high
    data[1] = (int)(clock_high/20.0);
    // offset
	data[2] = (int)(offset/20.0);
    
    int one = 1;
	int zero = 0;
    
    if(channel < 4)
      {
        if( board[cur_board].prog_clock_base_address != 0x0 ) 
          {
            // program the registers
            usb_write_address( board[cur_board].prog_clock_base_address + (channel+1) * 0x10 );
            usb_write_data( data, 3 );
            usb_write_address( board[cur_board].prog_clock_base_address );
            usb_write_data( &one, 1 );
            
            // sync the clocks
            usb_write_address( board[cur_board].prog_clock_base_address );
            usb_write_data( &zero, 1 );
          } 
        else 
          {
            // There needs to be a way to check if the board has this functionality
            reg_write ((REG_PULSE_PERIOD + channel), data[0]);
            reg_write ((REG_PULSE_CLOCK_HIGH + channel), data[1]);
            reg_write ((REG_PULSE_OFFSET + channel), data[2]);
            reg_write(REG_PULSE_SYNC,1);
            reg_write(REG_PULSE_SYNC,0);
          }
        debug (DEBUG_INFO, "Programmable Fixed Pulse Output #:0x%x.", channel);
        debug (DEBUG_INFO, "pb_set_pulse_regs: Wrote period: 0x%x.", data[0]);
        debug (DEBUG_INFO, "pb_set_pulse_regs: Wrote pulse width: 0x%x.", data[1]);
        debug (DEBUG_INFO, "pb_set_pulse_regs: Wrote offset: 0x%x.", data[2]);
      }
    else
      {
        debug (DEBUG_ERROR, "Channel must be 0, 1, 2 or 3.");
		return -1;
      }

    return 0;  
}

SPINCORE_API int set_pts(double maxFreq, int is160, int is3200, int allowPhase, int noPTS, double frequency, int phase)
{
	return set_pts_ex(1, maxFreq, is160, is3200, allowPhase, noPTS, frequency, phase);
}

SPINCORE_API int set_pts_ex(int pts_index, double maxFreq, int is160, int is3200, int allowPhase, int noPTS, double frequency, int phase)// , PTSDevice* device)
{
	BCDFREQ fbcd;
	int ret_val;
	
	debug(DEBUG_INFO, "set_pts: Attempting to write %lf MHz and %d degrees to PTS",frequency,phase);

	if( !(phase==-1) && (phase<0 || phase>270 || (phase%90)!=0) )
	    ret_val = PHASE_INVALID;
		
	phase/=90; //Convert phase from degrees to identifying integer.

	if( is3200 )
		frequency /= 10.0;

	freq_double_to_bcd( frequency, &fbcd, is3200);
	
	if( noPTS == 0 )
		ret_val = __set_pts_(pts_index, fbcd, phase);
	else
	{
		/*
        if( frequency > device->mfreq || frequency < 0.0 )
			return FREQ_ORANGE;
		
		if( device->allowPhase == 0)
			phase = -1;
		
		if( device->fullRange10MHz)
			fbcd.bcd_MHz[1] += fbcd.bcd_MHz[2] * 10; // if PTS160, then multiply 100MHz value by ten and add to 10MHz value
		
		ret_val = __set_pts_(pts_index, fbcd, phase);
		*/
		if( frequency > maxFreq || frequency < 0.0 )
			return FREQ_ORANGE;
		
		if( allowPhase == 0)
			phase = -1;
		
		if( is160 )
			fbcd.bcd_MHz[1] += fbcd.bcd_MHz[2] * 10; // if PTS160, then multiply 100MHz value by ten and add to 10MHz value
		
		ret_val = __set_pts_(pts_index, fbcd, phase);
		
	}
	
	spinpts_err = ret_val; //Set last error.
	
	return ret_val;
}

 /**
 *\internal
 * This function sends the frequency and phase information to the PTS Device. The frequency must be contained within an BCDFREQ structure and the phase must be -1, 0, 1, 2 or 3. 
 * Its is not recommended that this function is used for setting the PTS directly. Please refer to int set_pts( double frequency, int phase , PTSDevice* device) to set the device frequency.
 * 
 * \param freq BCDFREQ structure
 * \param phase Must equal -1, 0, 1, 2, 3 (-1 means that this PTS does not support phase.)
 * \return Returns 0 or an error code defined in \link spinapi.h \endlink
 */
  
int __set_pts_(int pts_index, BCDFREQ freq, int phase)
{
	int cntDataSent;
	unsigned int i, found;
	
	FT_STATUS ftStatus;
    FT_HANDLE ftHandle;
	
    DWORD lpdwBytesWritten;
	DWORD ptsData[_PTS_SET_NUM_DATA];
	DWORD numDevs;

	char buffer1[64]; 				// buffer for description of first device
    char buffer2[64]; 				// buffer for description of second device
	
	char *ptr_buffers[] = { buffer1, buffer2, NULL };	
	 
	 
	if(!(phase==-1||phase==0||phase==1||phase==2||phase==3))
		return PHASE_INVALID;

	/*
     *	Set the data up to be sent to the USB-PTS 4 bytes at a time. 
	 *  Each byte sent is a  ID/BCD pair. The ^BCDBYTEMASK is used to 
	 *  invert the BCD bits because the PTS uses negative logic (low-true). 
	 *  For example, 0x4D would sent the command to set BCD 2 to  10 kHz.
	 */
	ptsData[0] = ( ((freq.bcd_MHz[2]<<0) + (freq.bcd_MHz[1]<<8) + (freq.bcd_MHz[0]<<16) + (freq.bcd_kHz[2]<<24)) ^BCDBYTEMASK) + ((ID_MHz100<<4)+(ID_MHz10 << 12)+(ID_MHz1<<20)+(ID_kHz100<<28));
	ptsData[1] = (((freq.bcd_kHz[1]<<0) + (freq.bcd_kHz[0]<<8) + (freq.bcd_Hz[2]<<16 ) + (freq.bcd_Hz[1]<<24 )) ^BCDBYTEMASK) + ((ID_kHz10<<4 )+(ID_kHz1<<12)+(ID_Hz100<<20)+(ID_Hz10 << 28));
	// Note: For devices with phase support, the  ID_pHz is used for phase.
	ptsData[2] = (((freq.bcd_Hz[0] <<0) + (((phase!=-1)?(3-phase):freq.bcd_pHz[2])<<8) )^BCDBYTEMASK ) + ((ID_Hz1<<4)+(ID_pHz<<12)+(ID_UNUSED<<20)+(ID_UNUSED<<28));
    		
    ftStatus = FT_ListDevices(ptr_buffers,&numDevs,FT_LIST_ALL|FT_OPEN_BY_DESCRIPTION);
	
	if(numDevs == 0 || pts_index < 1 || pts_index > (int)numDevs)
	           return NO_DEVICE_FOUND;
	

	/* This check was implemented for systems that have another FTDI board present that is not ours. 
	 * Note that it does not support multiple SpinCore devices, and will use the first one found.
	 */
	found = 0;
	if (ftStatus == FT_OK)
		{		
			for(i=0 ; i<numDevs ; i++) 
				{
					if(strcmp(ptr_buffers[i], "SpinCore USB-PTS Interface") == 0) 
						{
							pts_index = i+1; // just to preserve older code below...ideally we should just use i
							found = 1;
							break;
						}
				}
		}
		
	if (found) 
    {
			
                     /* Open the device */                
                     ftStatus = FT_OpenEx(ptr_buffers[pts_index - 1],FT_OPEN_BY_DESCRIPTION,&ftHandle);
					 
                     if (ftStatus == FT_OK) 
                     {
					   debug(DEBUG_INFO, "__set_pts_: Opened comm. with %s device",ptr_buffers[pts_index - 1]);
					 
						for(cntDataSent=0; cntDataSent <  _PTS_SET_NUM_DATA; cntDataSent++){
					   
							//Opening of the device succeeded. Begin writing frequency setting data
							ftStatus = FT_Write(ftHandle,&ptsData[cntDataSent],4,&lpdwBytesWritten);
						   
							if (ftStatus != FT_OK) { 
								debug(DEBUG_ERROR, "__set_pts_: Error writing to device");
								return DWRITE_FAIL;
							}
							debug(DEBUG_INFO, "__set_pts_: Wrote word #%d = 0X%X to device.",cntDataSent,ptsData[cntDataSent]);
					   }
	   
                       FT_Close(ftHandle); 
                    }
                    else 
                    {
						return DEVICE_OPEN_FAIL;
					} 
    }
    else 
    {
	 debug(DEBUG_ERROR, "__set_pts_: Error opening Device");
     return DEVICE_OPEN_FAIL;
    }             
   
   return 0;
}

 /**
 * \internal
 * This function converts a double value into a BCDFREQ structure. 
 * 
 * \param freq Double value for the frequency to be converted.
 * \param bcdfreq BCDFREQ structure pointer. This is the structure that will be filled out by the function.
 * \return Returns the pointer to the structure passed in param 2.
 */
 
BCDFREQ* freq_double_to_bcd(double freq, BCDFREQ* bcdfreq, int is3200)
{
	memset((void*)bcdfreq,0,sizeof(BCDFREQ));
    double tmp, result;			
	  
    freq=freq*10000000.0; //get frequency in 0.1Hz
      	
    result = modf( freq/1000000000.0 , &tmp);
    freq=freq-1000000000.0*tmp;             
    bcdfreq->bcd_MHz[2] = (int) tmp;

    result = modf( freq/100000000.0 , &tmp);
    freq=freq-100000000.0*tmp;      
    bcdfreq->bcd_MHz[1] = (int) tmp;
       
    result = modf( freq/10000000.0 , &tmp);
    freq=freq-10000000.0*tmp;
    bcdfreq->bcd_MHz[0] = (int) tmp;

    result = modf( freq/1000000.0 , &tmp);
    freq=freq-1000000.0*tmp;
    bcdfreq->bcd_kHz[2] = (int) tmp;

    result = modf( freq/100000.0 , &tmp);
    freq=freq-100000.0*tmp;
    bcdfreq->bcd_kHz[1] = (int) tmp;

    result = modf( freq/10000.0 , &tmp);
    freq=freq-10000.0*tmp;
    bcdfreq->bcd_kHz[0] = (int) tmp;

    result = modf( freq/1000.0 , &tmp);
    freq=freq-1000.0*tmp;
    bcdfreq->bcd_Hz[2] = (int) tmp;

    result = modf( freq/100.0 , &tmp);
    freq=freq-100.0*tmp;
    bcdfreq->bcd_Hz[1] = (int) tmp;

    result = modf( freq/10.0 , &tmp);
    freq=freq-10.0*tmp;
    bcdfreq->bcd_Hz[0] = (int) tmp;
	
	result = modf( freq/1.0 , &tmp);
    freq=freq-1.0*tmp;
    bcdfreq->bcd_pHz[2] = (int) tmp;

	if(is3200 != 1){
	debug(DEBUG_INFO, "freq_double_to_bcd:\n\t100MHz: 0X%x\n\t10MHz:  0X%x\n\t1MHz:   0X%x"
							 "\n\t100kHz: 0X%x\n\t10kHz:  0X%x\n\t1kHz:   0X%x"
							 "\n\t100Hz:  0X%x\n\t10Hz:   0X%x\n\t1Hz:    0X%x\n\t0.1Hz:  0X%x\n", 
							 bcdfreq->bcd_MHz[2],bcdfreq->bcd_MHz[1],bcdfreq->bcd_MHz[0],
							 bcdfreq->bcd_kHz[2],bcdfreq->bcd_kHz[1],bcdfreq->bcd_kHz[0],
							 bcdfreq->bcd_Hz[2],bcdfreq->bcd_Hz[1],bcdfreq->bcd_Hz[0],bcdfreq->bcd_pHz[2]);
	}
	else{
	debug(DEBUG_INFO, "freq_double_to_bcd:\n\t1GHz:   0X%x"
							 "\n\t100MHz: 0X%x\n\t10MHz:  0X%x\n\t1MHz:   0X%x"
							 "\n\t100kHz: 0X%x\n\t10kHz:  0X%x\n\t1kHz:   0X%x"
							 "\n\t100Hz:  0X%x\n\t10Hz:   0X%x\n\t1Hz:    0X%x\n", 
							 bcdfreq->bcd_MHz[2],bcdfreq->bcd_MHz[1],bcdfreq->bcd_MHz[0],
							 bcdfreq->bcd_kHz[2],bcdfreq->bcd_kHz[1],bcdfreq->bcd_kHz[0],
							 bcdfreq->bcd_Hz[2],bcdfreq->bcd_Hz[1],bcdfreq->bcd_Hz[0],bcdfreq->bcd_pHz[2]);
	}
 
    return  bcdfreq;
}
 
SPINCORE_API const char* spinpts_get_error(void)
{
	memset((void*)spinpts_err_buf,'\0',ERROR_STR_SIZE);
	
	switch(spinpts_err)
	{
		case PHASE_INVALID:
			strncpy(spinpts_err_buf,"Invalid Phase.",ERROR_STR_SIZE);
			break;
		case FREQ_ORANGE:
			strncpy(spinpts_err_buf,"Frequency out of range.",ERROR_STR_SIZE);
			break;
		case DWRITE_FAIL:
			strncpy(spinpts_err_buf,"Error writing to PTS.",ERROR_STR_SIZE);
			break;
		case DEVICE_OPEN_FAIL:
			strncpy(spinpts_err_buf,"Error opening PTS.",ERROR_STR_SIZE);
			break;
		case NO_DEVICE_FOUND:
			strncpy(spinpts_err_buf,"No PTS Found.",ERROR_STR_SIZE);
			break;
		case 0:
			strncpy(spinpts_err_buf,"PTS Operation Successful.",ERROR_STR_SIZE);
			break;
		default:
			strncpy(spinpts_err_buf,"Unknown error.",ERROR_STR_SIZE);
			break;
	};
	
	return spinpts_err_buf;
}

SPINCORE_API const char* spinpts_get_version(void)
{
            return spinpts_version;
}
/*
 *
 *  End ofSpinPTS Functions
 *
 */
