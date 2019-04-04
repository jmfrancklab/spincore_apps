/* 
  * Copyright (c)  2011, SpinCore Technologies, Inc.
  * All rights reserved.
  *
  * This program is free software: you can redistribute it and/or modify
  * it under the terms of the GNU General Public License as published by
  * the Free Software Foundation, either version 3 of the License, or
  * (at your option) any later version.
  * 
  * This program is distributed in the hope that it will be useful,
  * but WITHOUT ANY WARRANTY; without even the implied warranty of
  * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  * GNU General Public License for more details.
  * 
  * You should have received a copy of the GNU General Public License
  *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
  */

/*
 * Example Program 1
 * SpinCore Technologies Inc.
 * 2011
 *
 * This program outputs a square wave with frequency 1 Hz and duty
 * cycle 50% on the digital BNC outputs.
 */
 

#include <stdio.h>

#include "mrispinapi.h"

#define ERROR_CATCH(arg) error_catch(arg, __LINE__)

void pause(void)
{
	printf("Press enter to exit...");
	// flushing input stream doesn't work on all platforms
	fflush(stdin);
	fgetc(stdin);
}

DWORD error_catch(int error, int line_number)
{
	if( error != 0 ) {
		printf("ERROR CODE 0x%X AT LINE NUMBER %d\n", error, line_number);
		pause();
		exit(1);
	}
	return error;
}

int main(int argc, char *argv[])
{
	int loop_addr;
	
	printf("Example 1 - SpinCore Technologies 2011\n\n");
	printf("This program outputs a pulse on the digital output BNCs.\n");
	printf("The pulse has an on time and an off time of 500 ms.\n\n");
	
	// Initializes MRI SpinAPI
	ERROR_CATCH( spmri_init() );
	
	printf("SpinAPI initialized.\n");
	
	// Sets all of the values related to the board to their default values
	ERROR_CATCH( spmri_set_defaults() );
	
	// Signals to the board that you are going to start programming instructions
	// to it. The board resets the address in preperation.
	ERROR_CATCH( spmri_start_programming() );
	
	// Reads the current address in instruction memory for the branch
	// instruction later on that will return to this point in the program.
	ERROR_CATCH( spmri_read_addr( &loop_addr ) );
	
	// Outputs a high voltage level on the two digital out BNCs for 500 ms.
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		0.0, // Amplitude
		ALL_DACS, // DAC Select
		DONT_WRITE, // Write
		DONT_UPDATE, // Update
		DONT_CLEAR, // Clear
	  // RF Information
		0, // freq register
		0, // phase register
		0, // tx enable
		0, // phase reset
		0, // rx enable
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x02, // flags
		0, // data
		CONTINUE, // opcode
		500.0 * ms // delay
	));
	
	// Outputs a low voltage level on the two digital out BNCs for 500 ms and
	// jumps to the first instruction.
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		0.0, // Amplitude
		ALL_DACS, // DAC Select
		DONT_WRITE, // Write
		DONT_UPDATE, // Update
		DONT_CLEAR, // Clear
	  // RF Information
		0, // freq register
		0, // phase register
		0, // tx enable
		0, // phase reset
		0, // rx enable
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		loop_addr, // data
		BRANCH, // opcode
		500.0 * ms // delay
	));
	
	printf("Board programmed.\n");
	
	// Starts the pulse program stored on the board
	ERROR_CATCH(spmri_start());
	
	printf("Board is running...\n");
	
	pause();
	
	// Stops the board by resetting it.
	ERROR_CATCH(spmri_stop());
	
	return 0;
}
