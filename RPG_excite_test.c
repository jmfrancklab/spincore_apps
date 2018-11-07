#include <stdio.h>
#include <math.h>

#include "mrispinapi.h"

#define ERROR_CATCH(arg) error_catch(arg, __LINE__)

void pause(void)
{
    printf("Press enter to exit...");
    //flushing input stream
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

    // ** Configure Board ** 
    // Initialize MRI SpinAPI
    ERROR_CATCH( spmri_init() );

    printf("SpinAPI initialized.");
    // Set all values on board to default values
    ERROR_CATCH( spmri_set_defaults() );

    // Carrier Shape
    double carrier[1024];
    int i;
    for( i = 0 ; i < 1024 ; i++ ) {
        carrier[i] = sin( (double) i / 1024.0 * 2 * 3.14159 );
    }
    ERROR_CATCH(spmri_set_carrier_shape( carrier, 1024));

    // Carrier Frequency Registers
    double freq[1] = {1.0};
    ERROR_CATCH( spmri_set_frequency_registers( freq, 1 ) );

    // Phase Registers
    double phase[1] = {0.0};
    ERROR_CATCH( spmri_set_phase_registers( phase, 1 ) );

    // Amplitude Registers
    double amp[1] = {1.0};
    ERROR_CATCH( spmri_set_amplitude_registers( amp, 1 ) );
    
    // ** Program Board **
    int loop_addr;
    printf("RPG excite test program \n\n");
    // Signal board that ready to start sending it instructions
    ERROR_CATCH( spmri_start_programming() );
    // Read current memory address for ability to return back to this point later on in the program
    ERROR_CATCH( spmri_read_addr( &loop_addr ) );

    // This instruction enables a 1 MHz analog output
    int start;
    start = ERROR_CATCH(spmri_mri_inst(
                // DAC Information
                0.0, // Amplitude
                ALL_DACS, // DAC Select
                DONT_WRITE, // Write
                DONT_UPDATE, // Update
                DONT_CLEAR, // Clear
                // RF Information
                0, // freq register
                0, // phase register
                1, // tx enable
                0, // phase select
                0, // rx enable
                7, // envelope frequency register (7=no shape)
                0, // amp register
                0, // cyclops phase (must be 0)
                // PulseBlaster Information
                0x01, // flags
                0, // data
                CONTINUE, // opcode
                10.0 * us // pulse time
                ));

    // This instruct disables the analog output and resets phase
    // for next instruction
    ERROR_CATCH(spmri_mri_inst(
                // DAC Information
                0.0, // Amplitude
                ALL_DACS, // DAC Select
                DO_WRITE, // Write
                DO_UPDATE, // Update
                DONT_CLEAR, // Clear
                // RF Information
                0, // freq register
                0, // phase register
                0, // tx enable
                0, // phase reset
                0, // rx enable
                7, // envelope frequency register
                0, // amp register
                0, // cyclops phase
                // PulseBlaster Information
                0x00, // flags
                0, // data
                BRANCH, // opcode
                1000000.0 * us // delay
                ));
   // Stop Instruction
   ERROR_CATCH(spmri_mri_inst(
               // DAC Information
               0.0, // Amplitude
               ALL_DACS, // DAC Select
               DO_WRITE, // Write
               DO_UPDATE, // Update
               DONT_CLEAR, // Clear
               // RF Information
               0, // freq register
               0, // phase register
               0, // tx enable
               0, // phase reset
               0, // rx enable
               7, // envelope freq reg
               0, // amp register
               0, // cyclops phase
               // PulseBlaster Information
               0x00, // flags
               start, // data
               STOP, // opcode
               1.0 * us // delay
               ));

   printf("Board programmed.\n");

   // Starts the pulse program stored on board
   ERROR_CATCH(spmri_start());

   printf("Board is running...\n");

   pause();

   // Stops the board by resetting it
   ERROR_CATCH(spmri_stop());

    return 0;
}

