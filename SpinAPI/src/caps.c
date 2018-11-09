#include <stdlib.h>
#include <string.h>

#include "caps.h"
#include "debug.h"
#include "if.h"
#include "spinapi.h"
#include "usb.h"
#include "util.h"

/**
 * Get capabilities of board. This is called by pb_init() to fill out
 * the board structure so error checking can be done throughout the program.
 *
 * \return -1 on failure, 0 on success
 */

int
get_caps (BOARD_INFO * board, int dev_id)
{
  unsigned int firmware_id, firmware_id_save, caps_assigned;
  debug (DEBUG_INFO, "dev_id=0x%x", dev_id);
  memset (board, 0, sizeof (BOARD_INFO));
  board->custom_design = 0;	//default value, indicates design is NOT custom

  // for boards using AMCC_DEVID and PBESR_PRO_DEVID, the firmware
  // id register was not implemented. Thus, we cannot be sure exactly
  // what design we are dealing with, so   of these parameters we have
  // to guess on. Overestimates are used so that the software will not
  // give errors, and the users are expected to use appropriate values.
  // unknown values are marked as "est"

  // These device ID's are for boards using the AMCC bridge chip
  switch (dev_id) {

    case AMCC_DEVID:
    case 0x8879:
    case 0x5920:
      debug (DEBUG_INFO, "detected generic PulseBlaster board (devid=0x%x)", dev_id);

      board->is_usb = 0;

      if (dev_id == AMCC_DEVID || dev_id == 0x8879) {
				board->use_amcc = 1;	// regular amcc protocol
			}

			if (dev_id == 0x5920) {
				board->use_amcc = 2;	// older amcc protocol
			}

      board->has_FF_fix = 0;	//no way to tell if these boards have the FF fix

      board->dds_clock_mult = 1.0;
      board->pb_clock_mult = 1.0;
      board->num_instructions = 1024 * 1024;	// est
      board->dds_prog_method = DDS_PROG_OLDPB;
      board->has_firmware_id = 0;
      board->firmware_id = 0;
      board->status_oldstyle = 1;

      board->num_phase0 = 64;	// est
      board->num_phase1 = 64;	// est
      board->num_phase2 = 64;	// est
      board->num_freq0 = 64;	// est

      board->is_radioprocessor = 0;
      board->supports_scan_segments = 0;
      board->supports_scan_count = 0;
			board->supports_cyclops = 0;

      break;

      // PulseBlasterESR with FPGA connected directly to PCI
    case PBESR_PRO_DEVID:
      debug (DEBUG_INFO, "detected PulseBlasterESR-PRO board");

      board->has_FF_fix = 0;	//no way to tell if these boards have the FF fix

      board->is_usb = 0;
      board->use_amcc = 0;
      board->dds_clock_mult = 1.0;
      board->pb_clock_mult = 1.0;
      board->num_instructions = 1024 * 1024;	// est
      board->dds_prog_method = DDS_PROG_OLDPB;
      board->has_firmware_id = 0;
      board->firmware_id = 0;
      board->status_oldstyle = 1;

      board->num_phase0 = 64;	// est
      board->num_phase1 = 64;	// est
      board->num_phase2 = 64;	// est
      board->num_freq0 = 64;	// est

      board->is_radioprocessor = 0;
      board->supports_scan_segments = 0;
      board->supports_scan_count = 0;
      board->supports_cyclops = 0;

      break;

      // All othere boards implement the firmware id register. So we know exactly
      // what capabilties the board has.

      // PBESR with direct FPGA, supports firmware id register
    case 0x8878:
      firmware_id = reg_read (REG_FIRMWARE_ID);
      debug (DEBUG_INFO, "Detected PulseBlasterESR board (r 0x%x)", firmware_id);

      board->has_FF_fix = 0;

      // the PB Core "1ff" issue has been fixed in 8-5 and up
      if ((0x0900 > firmware_id) && (firmware_id >= 0x0805))
        {
          board->has_FF_fix = 1;
        }

      // the PB Core "1ff" issue has been fixed in 9-4 and up
      if ((0x0A00 > firmware_id) && (firmware_id >= 0x0904))
        {
          board->has_FF_fix = 1;
        }
        
      // the PB Core "1ff" issue has been fixed in 18-xx designs
      if ((0x1300 > firmware_id) && (firmware_id >= 0x1206))
        {
          board->has_FF_fix = 1;
        }
    
      // the PB Core "1ff" issue has been fixed in 19-xx designs
      if ((0x1400 > firmware_id) && (firmware_id >= 0x1301))
        {
          board->has_FF_fix = 1;
        }

      board->is_usb = 0;
      board->use_amcc = 0;
      board->dds_clock_mult = 1.0;
      board->pb_clock_mult = 1.0;
      board->num_instructions = 4 * 1024;

      if(firmware_id == 0x0908)
        {
          board->num_IMW_bytes = 8;
        }
      else if(firmware_id == 0x1105)
        {
          board->num_IMW_bytes = 4;
        }
      else 
        {
          board->num_IMW_bytes = 10;
        }

      board->dds_prog_method = DDS_PROG_OLDPB;
      board->has_firmware_id = 1;
      board->firmware_id = firmware_id;
      board->status_oldstyle = 0; //WAS 1

      board->num_phase0 = 0;
      board->num_phase1 = 0;
      board->num_phase2 = 0;
      board->num_freq0 = 0;

      board->is_radioprocessor = 0;
      board->supports_scan_segments = 0;
      board->supports_scan_count = 0;
      board->supports_cyclops = 0;

      break;
			
		// PCI Express PulseBlaster
		case 0x887A:
			firmware_id = reg_read_simple (REG_FIRMWARE_ID_PCIE << 2);
			debug (DEBUG_INFO, "Detected PulseBlaster PCIe board (r 0x%x)", firmware_id);

			// the only existing designs for this board have the FF fix
			board->has_FF_fix = 1;
			board->is_pcie = 1;
			board->is_usb = 0;
			board->use_amcc = 0;
			board->dds_clock_mult = 1.0;
			board->pb_clock_mult = 1.0;
			board->num_instructions = 4 * 1024;
			board->num_IMW_bytes = 10;
			board->pb_base_address = 0x40000;

			board->dds_prog_method = DDS_PROG_OLDPB;
			board->has_firmware_id = 1;
			board->firmware_id = firmware_id;
			board->status_oldstyle = 0;
			break;
			
    // RadioProcessor PCI Board
    case 0x8876:
      firmware_id = reg_read (REG_FIRMWARE_ID);
      debug (DEBUG_INFO, "FWID@%u: firmware_id=0x%.4x", REG_FIRMWARE_ID, firmware_id);

      switch (firmware_id)
			{
				case 0x0a01:
				case 0x0a02:
				case 0x0a03:
				case 0x0a04:
				case 0x0a05:
				case 0x0a06:
				case 0x0a07:
				case 0x0a08:
				case 0x0a09:
				case 0x0a0a:
				case 0x0a0b:
				case 0x0a0c:
				case 0x0a0d:
				case 0x0a0e:
				case 0x0a0f:
				case 0x0a10:
				case 0x0a11:
				case 0x0a12:
				case 0x0a13:
				case 0x0a14:
				case 0x0a15:
				case 0x0a16:
				case 0x0a17:
				case 0x0F02:
				case 0x0F03:
				case 0x0F04:
				case 0x0F05:
			debug (DEBUG_INFO, "detected RadioProcessor board (r%d)", 0x00FF & firmware_id);
			caps_assigned = 0;
			board->has_FF_fix = 0;
			board->is_usb = 0;
			board->use_amcc = 0;
			board->pb_clock_mult = 1.0;
			board->num_instructions = 1024;
				board->num_IMW_bytes = 10;
			board->dds_prog_method = DDS_PROG_EXTREG;
			board->supports_dds_shape = 0;
			board->has_firmware_id = 1;
			board->firmware_id = firmware_id;
			board->status_oldstyle = 0;
			//these are default values.  These values may be overwritten  multiple times in the 'if' statements below
			board->num_phase0 = 4;	// cos
			board->num_phase1 = 4;	// sin
			board->num_phase2 = 128;	// tx
			board->num_freq0 = 16;	//      
			// miscellaneous capture stuff   
			board->is_radioprocessor = 1;
			board->cic_max_stages = 3;
			board->cic_max_decim = 64 * 1024 - 1;
			board->cic_max_shift = 63;
			board->fir_max_taps = 1020;
			board->fir_max_shift = 63;
			board->fir_max_decim = 256;
			board->fir_coef_width = 18;
			board->num_points = 16 * 1024;
			board->acquisition_disabled = 0;
			
			// these next parameters change depending on the firmware
			// revision. specify defualts here, and change if necessary
			// below
			board->supports_scan_segments = 0;
			board->supports_scan_count = 0;
			board->dds_clock_mult = 1.0;

			// 10-3 and above have scan segment ability
			if (firmware_id >= 0x0a03)
				{
					board->supports_scan_segments = 1;
					caps_assigned = 1;
				}

			// 10-4 and above have scan count register
			if (firmware_id >= 0x0a04)
				{
					board->supports_scan_count = 1;
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a04)
				{
					board->dds_clock_mult = 4.0;	// 10-4 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->has_wraparound_problem = 1;	// boards 10-4, 10-5, 10-6 and up have the wraparound problem
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a05)
				{
					board->dds_clock_mult = 4.0;	// 10-5 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->has_wraparound_problem = 1;	// boards 10-4, 10-5, 10-6 and up have the wraparound problem
					caps_assigned = 1;
				}

			// 10-5 and up have shape register
			if (firmware_id >= 0x0a05)
				{
					board->supports_dds_shape = 1;
					board->num_shape = 7;
					board->num_amp = 4;
					board->num_phase2 = 16;	//the addition of AWG required a sacrifice from 128 to 16  tx phase regs.
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a06)
				{
					board->has_wraparound_problem = 1;	// boards 10-4, 10-5, 10-6 and up have the wraparound problem
					board->dds_clock_mult = 2.0;	// 10-6 has no pll, so the DAC only operates at 2x the frequency (75-75-150)
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a07)
				{
					board->acquisition_disabled = 1;	//version 10-7 has data acquisition disabled
					board->dds_clock_mult = 4.0;	// 10-7 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a08)
				{
					board->dds_clock_mult = 2.0;	//10-8 has no pll, so the DAC only operates at 2x the frequency (75-75-150)
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a09)
				{
					board->dds_clock_mult = 4.0;	// 10-9 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					caps_assigned = 1;
				}

			//version 10-10 is a custom design for Sasi Solomon in Israel (based on 10-8, but with more TTL outputs)
			if (firmware_id == 0x0a0a)
				{
					board->dds_clock_mult = 2.0;	//10-10 firmware has no pll, so the DAC only operates at 2x the frequency (75-75-150)
					board->num_freq0 = 4;	// frequency registers, downgraded from 16
					board->num_phase2 = 2;	//tx phase regs, downgraded from 16
					//could strip down sin_phase and cos_phase as well for 2 extra bits in the future (possible, depending on customer application?)
					board->custom_design = 1;	//used to identify board as custom design for Topspin 
					caps_assigned = 1;
				}

			//versions 10-10 and later have the PB Core counter 'FF' fix
			if (firmware_id >= 0x0a0a) {
					board->has_FF_fix = 1;
					caps_assigned = 1;
			}

			if (firmware_id == 0x0a0b)
				{
					board->dds_clock_mult = 2.0;	//10-11 has no pll, so the DAC only operates at 2x the frequency (75-75-150)
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a0c)
				{
					board->dds_clock_mult = 4.0;	// 10-12 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a0d)
				{
					board->dds_clock_mult = 4.0;	// 10-13 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a0e) {
					board->dds_clock_mult = 4.0;	// 10-14 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					caps_assigned = 1;
			}

			if (firmware_id == 0x0a0f)
				{
					board->dds_clock_mult = 4.0;	// 10-15 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->custom_design = 3;	// custom design 3 has aquisition disabled and 9 TTL outputs
					board->acquisition_disabled = 1;
					board->num_phase0 = 0;	// cos
					board->num_phase1 = 0;	// sin
					board->num_phase2 = 16;	// tx
					board->num_freq0 = 16;	//      
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a10)	//10-16
				{
					board->dds_clock_mult = 4.0;	// 10-16 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->custom_design = 4;	// custom design 4 has aquisition disabled, 4 TTL outputs, 1024 freq, 8 tx phase registers
					board->acquisition_disabled = 1;
					board->num_phase0 = 0;	// cos
					board->num_phase1 = 0;	// sin
					board->num_phase2 = 8;	// tx
					board->num_freq0 = 1024;	// freq
					board->num_instructions = 4096;
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a11)	//10-17
				{
					board->dds_clock_mult = 2.0;	// 10-17 has a 2x multiplier on the DDS that drives the DAC (75-75-150)
					board->custom_design = 4;	// custom design 4 has aquisition disabled, 4 TTL outputs, 1024 freq, 8 tx phase registers
					board->acquisition_disabled = 1;
					board->num_phase0 = 0;	// cos
					board->num_phase1 = 0;	// sin
					board->num_phase2 = 8;	// tx
					board->num_freq0 = 1024;	// freq
					board->num_instructions = 4096;
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a12)	//10-18
				{
					board->dds_clock_mult = 4.0;	// 10-18 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->num_instructions = 4096;	//instructions
					caps_assigned = 1;
				}

			if (firmware_id == 0x0a13)	//10-19
				{
					board->dds_clock_mult = 4.0;	// 10-19 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->custom_design = 5;	// custom design 5 has aquisition disabled, 4 TTL outputs, 1024 freq, 1024 amplitude registers, 8 phase registers
					board->acquisition_disabled = 1;
					board->num_phase0 = 0;	// cos
					board->num_phase1 = 0;	// sin
					board->num_phase2 = 8;	// tx
					board->num_freq0 = 1024;	// freq
					board->num_amp = 1024;	//amp
					board->num_instructions = 10 * 1024;	//instructions
					board->num_IMW_bytes = 11;
					caps_assigned = 1;
				}
				if (firmware_id == 0x0a14)	//10-20
				{
					board->dds_clock_mult = 4.0;	// 10-20 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->num_instructions = 4096;	//instructions
					caps_assigned = 1;
				}
			if (firmware_id == 0x0a15)	//10-21
				{
					board->dds_clock_mult = 4.0;	// 10-21 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->num_instructions = 4096;	//instructions
				board->custom_design = 6;	// custom design 6 has CYCLOPS control in hardware.
				board->supports_cyclops = 1;
					board->num_phase2 = 4;	// tx
					board->num_freq0 = 8;	// freq
					board->num_amp = 4;	//amp
					caps_assigned = 1;
				}
			if (firmware_id == 0x0a16)	//10-22
				{
					board->dds_clock_mult = 4.0;	// 10-22 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->num_instructions = 4096;	//instructions
				board->custom_design = 6;	// custom design 6 has CYCLOPS control in hardware.
				board->supports_cyclops = 1;
					board->num_phase2 = 4;	// tx
					board->num_freq0 = 8;	// freq
					board->num_amp = 4;	//amp
					board->cic_max_decim = 1024*1024 - 1;
						caps_assigned = 1;
					}
			if (firmware_id == 0x0a17)	//10-23
				{
					board->dds_clock_mult = 4.0;	// 10-23 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->num_instructions = 4096;	//instructions
					board->custom_design = 6;	// custom design 6 has CYCLOPS control in hardware.
					board->supports_cyclops = 1;
					board->num_phase2 = 4;	// tx
					board->num_freq0 = 8;	// freq
					board->num_amp = 4;	//amp
					board->cic_max_decim = 1024*1024 - 1;
						caps_assigned = 1;
					}
					
				if (firmware_id == 0x0F02)	//15-2
				{
					board->dds_clock_mult = 4.0;	// 15-2 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->num_instructions = 4096;	//instructions
					board->cic_max_decim = 1024*1024 - 1;
					caps_assigned = 1;
				}
			if (firmware_id == 0x0F03)	//15-3
				{
					board->dds_clock_mult = 4.0;	// 15-3 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->num_instructions = 4096;	//instructions
					board->custom_design = 6;	// custom design 6 has CYCLOPS control in hardware.
					board->supports_cyclops = 1;
					board->num_phase2 = 4;	// tx
					board->num_freq0 = 8;	// freq
					board->num_amp = 4;	//amp
					board->cic_max_decim = 1024*1024 - 1;
					caps_assigned = 1;
				}
			if (firmware_id == 0x0F04)	//15-4
				{
					board->dds_clock_mult = 4.0;	// 15-4 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
					board->num_instructions = 4096;	//instructions
			board->custom_design = 6;	// custom design 6 has CYCLOPS control in hardware.
					board->supports_cyclops = 1;
					board->num_phase2 = 4;	// tx
					board->num_freq0 = 8;	// freq
					board->num_amp = 4;	//amp
					board->cic_max_decim = 1024*1024 - 1;
					caps_assigned = 1;
				}

			// ^ Add new firmware revision clauses above  ^
			if ((firmware_id > 0x0a17) && (caps_assigned == 0))
				{
			debug(DEBUG_ERROR, "Capabilities not assigned (firmware id 0x%x). Please notify SpinCore of this problem.", firmware_id);
					return -1;
				}

	  break;

	default:
    debug (DEBUG_INFO, "Attempting to read at RPG firmware address...",);
    firmware_id_save = firmware_id;
	  firmware_id = reg_read_simple (REG_FIRMWARE_ID_RPG);
    debug (DEBUG_INFO, "FWID@%u: firmware_id=0x%.8x", REG_FIRMWARE_ID_RPG, firmware_id);
	  if(0x000F0000 == (0xFFFF0000 & firmware_id)) 
	    {
        debug(DEBUG_INFO, "Found RadioProcessor with firmware_id = %u-%u\n", (0xFFFF0000 & firmware_id) >> 16, 0xFFFF & firmware_id);
      
        caps_assigned = 1;
        board->has_FF_fix = 0;
        board->is_usb = 0;
        board->use_amcc = 0;
        board->pb_clock_mult = 1.0;
        board->num_instructions = 2048; // RPG 15-4 and 15-5 have 2048
        board->num_IMW_bytes = 16;
        board->dds_prog_method = DDS_PROG_RPG;
        board->supports_dds_shape = 1; // only amplitude control at this time
        board->has_firmware_id = 3;
        board->firmware_id = ( (0xFFFF0000 & firmware_id) >> 8 ) | 0xFFFF & firmware_id; // convert to standard 16bit format
        board->status_oldstyle = 0;
        //these are default values.  These values may be overwritten  multiple times in the 'if' statements below
        board->num_phase0 = 4;	// cos
        board->num_phase1 = 4;	// sin
        board->num_phase2 = 128;	// tx
        board->num_freq0 = 16;	//      
        // miscellaneous capture stuff   
        board->is_radioprocessor = 2;
        board->cic_max_stages = 3;
        board->cic_max_decim = 64 * 1024 - 1;
        board->cic_max_shift = 63;
        board->fir_max_taps = 1020;
        board->fir_max_shift = 63;
        board->fir_max_decim = 256;
        board->fir_coef_width = 18;
        board->num_points = 16 * 1024;
        board->acquisition_disabled = 0;
        board->supports_scan_segments = 1;
        board->supports_scan_count = 1; // RPG doesn't support reading (to my knowledge), but will reset it
        board->dds_clock_mult = 4.0;	// RPG 15-4 and 15-5
        board->num_shape = 1;
        board->num_amp = 4;
        board->adc_clock_MHz = 75.0;
        board->dac_clock_int_MHz = 300.0;
        board->num_points = 16 * 1024;
        board->supports_cyclops = 1;
        // Control Registers
	board->status_reg = 0x0014;
        board->fir_1 = 0x4C;
        board->fir_2 = 0x50;
        board->cic_1 = 0x54;
        board->cic_2 = 0x58;
        board->acq_1 = 0x60;
        board->acq_2 = 0x64;
        board->misc_1 = 0x70;
        board->freq_addr = 0x20;
        board->freq_data = 0x24;
        board->phase_addr = 0x28;
        board->phase_data = 0x2C;
        board->shape_addr = 0x30;
        board->shape_data = 0x34;
        board->memory_addr = 0x38;
        board->memory_data = 0x3C;
        board->memory_offset = 0;
        board->cos_phase_width = 12;
        board->sin_phase_width = 12;
        board->phase_addr_cos_offset = 0;
        board->phase_addr_sin_offset = 0x1000000;
        board->freq_rx_offset = 0;
        board->freq_tx_offset = 0x1000000;
        board->envelope_freq_offset = 0x2000000;
        board->tx_phase_width = 12;
        board->phase_addr_tx_offset = 0x2000000;
        board->amp_shape_width = 15;
        board->amp_shape_offset = 0;
        board->envelope_shape_offset = 0x2000000;
        board->envelope_shape_width = 15;
        board->carrier_shape_offset = 0x1000000;
        board->carrier_shape_width = 14;
        board->imw_base_addr = 0;
        board->imw_base_data_addr = 0x0004;
        board->default_shape_period = 10; // in microseconds
        board->reg_scan_count = 0x68;
        
      }
	  else
      {
		debug(DEBUG_ERROR, "Unknown RadioProcessor board found (firmware id 0x%x). Make sure you have the latest version of spinapi.",
	          firmware_id_save);
	      return -1;
		}
	  break;
	}			// end of switch (firmware_id)
      break;			//end of RadioProcessor PCI Board case
      case 0x8890:
          firmware_id = reg_read (REG_FIRMWARE_ID);
          debug (DEBUG_INFO, "Detected PulseBlaster 4-Core (r 0x%x)",
    	     firmware_id);
    
          board->has_FF_fix = 1;
          board->is_usb = 0;
          board->use_amcc = 0;
          board->dds_clock_mult = 1.0;
          board->pb_clock_mult = 1.0;
          board->num_instructions = 4 * 1024;
    
          board->num_IMW_bytes = 4;
          board->dds_prog_method = DDS_PROG_OLDPB;
          board->has_firmware_id = 1;
          board->firmware_id = firmware_id;
          board->status_oldstyle = 0;	//WAS 1
    
          board->num_phase0 = 0;
          board->num_phase1 = 0;
          board->num_phase2 = 0;
          board->num_freq0 = 0;
    
          board->is_radioprocessor = 0;
          board->supports_scan_segments = 0;
          board->supports_scan_count = 0;

      break;
      // USB RadioProcessor board
    case 0xC1A9:
      if (usb_read_reg (0x15, &firmware_id) < 0)
        return 0;

      debug (DEBUG_INFO, "found usb radioprocessor board (firmware_id=0x%x)",
	     firmware_id);

      board->is_usb = 1;
      board->use_amcc = 0;
      board->dds_clock_mult = 4.0;
      board->pb_clock_mult = 1.0;
      board->num_instructions = 1024 * 1024;	// est
      board->dds_prog_method = DDS_PROG_EXTREG;
      board->has_firmware_id = 2;
      board->firmware_id = firmware_id;
      board->status_oldstyle = 0;

      board->num_phase0 = 4;	// cos
      board->num_phase1 = 4;	// sin
      board->num_phase2 = 32;	// tx
      board->num_freq0 = 32;

      board->is_radioprocessor = 1;
      board->supports_scan_segments = 1;
      board->supports_scan_count = 1;

      board->cic_max_stages = 3;
      board->cic_max_decim = 64 * 1024 - 1;
      board->cic_max_shift = 63;

      board->fir_max_taps = 1020;
      board->fir_max_shift = 63;
      board->fir_max_decim = 256;
      board->fir_coef_width = 18;

      board->num_points = 256 * 1024;	// number of complex points

      board->supports_dds_shape = 1;
      board->num_shape = 7;
      board->num_amp = 4;
      board->custom_design = 0;
      board->acquisition_disabled = 0;
      board->has_FF_fix = 0;

      if (firmware_id >= 0x0c03)	//firmware versions 12-3 and up have the PB Core 'FF' counter fix
	{
	  board->has_FF_fix = 1;
	}

      if (firmware_id == 0x0c06 || firmware_id == 0x0c09 || firmware_id == 0x0C0E)	//firmware version 12-6 is a custom design with 8 TTL output bits
	{
	  board->custom_design = 2;	//used to identify board has a custom design
	  board->num_phase2 = 4;	// tx
	  board->num_freq0 = 4;
	}
      if (firmware_id == 0x0c07)	//firmware version 12-7 has data acquisition disabled in hardware
	{
	  board->acquisition_disabled = 1;
	}
	// 12-18 has TX disabled. No change made in the API to reflect this
	if(firmware_id == 0x0c0f || firmware_id == 0x0c12)
	{
      board->dds_clock_mult = 4.0;	// 12-15 has a 4x multiplier on the DDS that drives the DAC (50-75-300)
	  board->num_instructions = 4096;	//instructions
	  board->custom_design = 6;	// custom design 6 has CYCLOPS control in hardware.
	  board->supports_cyclops = 1;
	  board->num_phase2 = 4;	// tx
	  board->num_freq0 = 8;	// freq
	  board->num_amp = 4;	//amp         
      board->cic_max_decim = 1024*1024-1; //20-bit counter used for CIC decimation
      caps_assigned = 1;    
    }
	if(firmware_id == 0x0C10) // RadioProcessor USB 12-16 Custom Design for PROGRESSION with CYCLOPS
	{
      board->num_IMW_bytes = 11;
	  board->num_instructions = 4096;	//instructions
	  board->custom_design = 7;	// custom design 7 has CYCLOPS control in hardware and PROGRESSION output flags
	  board->supports_cyclops = 1;
	  board->num_phase2 = 16;	// tx
	  board->num_freq0 = 16;	// freq
	  board->num_amp = 4;	//amp         
      board->cic_max_decim = 1024*1024-1; //20-bit counter used for CIC decimation
      caps_assigned = 1;    
    }
	if(firmware_id == 0x0C13) // PulseBlasterDDS-I-300 USB 12-19
	{
	  board->acquisition_disabled = 1;
	  board->is_radioprocessor = 1;
	  board->usb_method = 2;
      board->num_IMW_bytes = 12;
	  board->num_instructions = 4096;	//instructions
	  board->supports_cyclops = 0;
	  //board->num_phase2 = 128;	// tx
	  //board->num_freq0 = 1024;	// freq
	  //board->num_amp = 1024;	//amp
	  board->dds_nfreq[0] = 1024;
      board->dds_nphase[0] = 128;
      board->dds_namp[0] = 1024;
	  board->dds_nfreq[1] = 1;
      board->dds_nphase[1] = 1;
      board->dds_namp[1] = 1;
	  board->supports_dds_shape = 1;
	  board->num_shape = 7;
	  board->number_of_dds = 1;
	  board->dds_prog_method = 2;
	  board->pb_base_address = 0x040000;
      board->dds_address[0] = 0x0C0000;
      caps_assigned = 1;
    }

      break;

      // USB PulseBlaster Plus! (v2)
    case 0xC1AA:
      if (usb_read_reg (0x15, &firmware_id) < 0)
        return -1;

      debug
	(DEBUG_INFO, "found USB PulseBlaster Plus! board (firmware_id=0x%x)",
	 firmware_id);

      board->has_FF_fix = 1;

      board->is_usb = 1;
      board->use_amcc = 0;
      board->dds_clock_mult = 1.0;
      board->pb_clock_mult = 1.0;
      board->num_instructions = 1 * 1024;	// est
      board->dds_prog_method = DDS_PROG_EXTREG;
      board->has_firmware_id = 2;
      board->firmware_id = firmware_id;
      board->status_oldstyle = 0;

      board->num_phase0 = 0;	// cos
      board->num_phase1 = 0;	// sin
      board->num_phase2 = 0;	// tx
      board->num_freq0 = 0;

      board->is_radioprocessor = 0;
      board->supports_scan_segments = 0;
      board->supports_scan_count = 0;

      break;
      
      // USB PulseBlaster Board (with improved USB communications)
    case 0xC1AB:
	  if (usb_read_reg (0x0, &firmware_id) < 0)
        return -1;
      
      debug (DEBUG_INFO, "found USB PulseBlaster (firmware_id=0x%x)", firmware_id);
      
      if(firmware_id == 0x0D08 || firmware_id == 0x130E || firmware_id > 0x0D09)
	  {
		  board->has_FF_fix = 1;
		  board->use_amcc = 0;
		  board->is_usb = 1;
		  board->usb_method = 2;
		  board->num_instructions = 4 * 1024;
		  board->pb_clock_mult = 1.0;
		  board->has_firmware_id = 2;
		  board->firmware_id = firmware_id;
		  board->pb_base_address = 0x040000;
		  board->dds_prog_method = 2;
		  usb_read_reg (board->pb_base_address + 0xFF, &(board->pb_core_version));
		  debug (DEBUG_INFO, "pb_core_version=%d", board->pb_core_version);
	  }
	  else if(firmware_id == 0x0D09)
	  {
		  // similar to 0x0D08 except for a custom clock output
		  board->has_FF_fix = 1;
		  board->use_amcc = 0;
		  board->is_usb = 1;
		  board->usb_method = 2;
		  board->num_instructions = 4 * 1024;
		  board->pb_clock_mult = 1.0;
		  board->has_firmware_id = 2;
		  board->firmware_id = firmware_id;
		  board->pb_base_address = 0x040000;
		  // Programmable clock base address
		  // since this value is not 0, the api knows this design has a
		  // programmable clock output
		  board->prog_clock_base_address = 0x0C0000;
		  board->dds_prog_method = 2;
		  usb_read_reg (board->pb_base_address + 0xFF, &(board->pb_core_version));
		  debug (DEBUG_INFO, "pb_core_version=%d", board->pb_core_version);
	  }
	  
	  break;
	  
      // USB DDS-II Board
    case 0xC2A9:
      if (usb_read_reg (0x0, &firmware_id) < 0)
        return -1;
        
      debug (DEBUG_INFO, "found DDS board (firmware_id=0x%x)", firmware_id);
	  if(firmware_id == 0x0E01 || firmware_id == 0x0E02)
	  {
		  board->has_FF_fix = 1;
		  board->use_amcc = 0;
		  board->is_usb = 1;
		  board->usb_method = 2;
		  board->dds_clock_mult = 4.0;
		  board->num_instructions = 16 * 1024;	// est                   
		  board->pb_clock_mult = 1.0;
		  board->has_firmware_id = 2;
		  board->firmware_id = firmware_id;
		  board->number_of_dds = 2;
		  board->dds_nfreq[0] = 16;
		  board->dds_nfreq[1] = 16;
		  board->dds_nphase[0] = 8;
		  board->dds_nphase[1] = 8;
		  board->dds_namp[0] = 4;
		  board->dds_namp[1] = 4;
		  board->supports_dds_shape = 1;
		  board->num_shape = 7;
		  board->pb_base_address = 0x040000;
		  board->dds_address[0] = 0x0C0000;
		  board->dds_address[1] = 0x100000;
		  board->dds_prog_method = 2;
		  usb_read_reg (board->pb_base_address + 0xFF, &(board->pb_core_version));
		  debug (DEBUG_INFO, "pb_core_version=%d", board->pb_core_version);
	  }
	  else if(firmware_id == 0x0E03)
	  {
		  board->has_FF_fix = 1;
		  board->use_amcc = 0;
		  board->is_usb = 1;
		  board->usb_method = 2;
		  board->dds_clock_mult = 4.0;
		  board->num_instructions = 4 * 1024;	// est                   
		  board->pb_clock_mult = 1.0;
		  board->has_firmware_id = 2;
		  board->firmware_id = firmware_id;
		  board->number_of_dds = 2;
		  board->dds_nfreq[0] = 1024;
		  board->dds_nfreq[1] = 1024;
		  board->dds_nphase[0] = 128;
		  board->dds_nphase[1] = 128;
		  board->dds_namp[0] = 1024;
		  board->dds_namp[1] = 1024;
		  board->supports_dds_shape = 1;
		  board->num_shape = 7;
		  board->pb_base_address = 0x040000;
		  board->dds_address[0] = 0x0C0000;
		  board->dds_address[1] = 0x100000;
		  board->dds_prog_method = 2;
		  usb_read_reg (board->pb_base_address + 0xFF, &(board->pb_core_version));
		  debug (DEBUG_INFO, "pb_core_version=%d", board->pb_core_version);
	  }

      break;
    default:
	debug(DEBUG_ERROR, "Unknown board found (dev id 0x%x). Make sure you have the latest version of spinapi, and the .dll is placed in either the current directory, or a system directory.",
	 dev_id);      
	return -1;

    }				// end of switch (dev_id)

  return 0;
}
