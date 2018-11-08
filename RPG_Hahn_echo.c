#include <stdio.h>
#include <math.h>

#include "mrispinapi.h"

#define ERROR_CATCH(arg) error_catch(arg,__LINE__)

void pause(void)
{
    printf("Press enter to exit...");
    //flushing input stream
    fflush(stdin);
    fgetc(stdin);
}

DWORD error_catch(int error, int line_number)
{
    if( error != 0) {
        printf("ERROR CODE 0x%X AT LINE NUMBER %d\n", error, line_number);
        pause();
        exit(1);
    }
    return error;
}

int main(int argc, char *argv[])
{
    // ** Configure board **
    // Initialize MRI SpinAPI
    ERROR_CATCH( spmri_init() );

    printf("SpinAPI initialized...");
    // Set all values on board to default values
    ERROR_CATCH( spmri_set_defaults() );

    // Carrier frequency registers
    double freq[1] = {1.0};
    ERROR_CATCH( spmri_set_frequency_registers( freq, 1 ) );

    // Phase registers
    double phase[1] = {0.0};
    ERROR_CATCH( spmri_set_phase_registers( phase, 1 ) );

    // Amplitude registers
    double amp[1] = {1.0};
    ERROR_CATCH( spmri_set_amplitude_registers( amp, 1 ) );

    // ** Program board **
    int loop_addr;
    printf("RPG Hahn echo test program \n\n");
    // Signal board that ready to start sending it instructions
    ERROR_CATCH( spmri_start_programming() );
    // Read current memory address for ability to return back to this point later on in prog
    ERROR_CATCH( spmri_read_addr( &loop_addr ) );

    // This instruction enables a 15 MHz analog output 90 pulse
    int start;
    float pulse_90;
    float pulse_180;
    pulse_90 = 10.0;
    pulse_180 = 20.0;
    start = ERROR_CATCH( spmri_mri_inst(
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
                7, // envelope freq reg (7=no shape)
                0, // amp register
                0, // cyclops phase (must be 0)
                // PulseBlaster Information
                0x01, // flags
                0, // data
                CONTINUE, // opcode
                pulse_90 * us // pulse time
                ));

    // This instruction enables delay tau
    ERROR_CATCH(spmri_mri_inst(
                // DAC Information
                0.0, // Amplitude
                ALL_DACS, // DAC Select
                DO_WRITE, // Write
                DO_UPDATE, // Update
                DONT_CLEAR, // Clear
                // RF Information
                0, // freq reg
                0, // ph reg
                0, // tx enable
                0, // phase reset
                0, // rx enable
                7, // envelope freq reg
                0, // amp register
                0, // cyclops phase
                // PulseBlaster
                0x00, // flags
                0, // data
                CONTINUE, // opcode
                40.0 * us // delay
                ));

    // This instruction outputs 180 pulse
   ERROR_CATCH(spmri_mri_inst(
               // DAC
               0.0, // Amplitude
               ALL_DACS, // DAC Select
               DO_WRITE, // Write
               DO_UPDATE, // Update
               DONT_CLEAR, // Clear
               // RF
               0, // freq reg
               0, // ph reg
               1, // tx enable
               0, // phase reset
               0, // rx enable
               7, // envelope freq reg
               0, // amp reg
               0, // cyclops ph
               // PulseBlaster
               0x01, // flags
               0, // data
               CONTINUE, // opcode
               pulse_180 * us // pulse length
               ));
   //
    // This instruction enables repetition delay
    ERROR_CATCH(spmri_mri_inst(
                // DAC Information
                0.0, // Amplitude
                ALL_DACS, // DAC Select
                DO_WRITE, // Write
                DO_UPDATE, // Update
                DONT_CLEAR, // Clear
                // RF Information
                0, // freq reg
                0, // ph reg
                0, // tx enable
                0, // phase reset
                0, // rx enable
                7, // envelope freq reg
                0, // amp register
                0, // cyclops phase
                // PulseBlaster
                0x00, // flags
                0, // data
                BRANCH, // opcode
                3000000.0 * us // delay
                ));

   // Stop instruction
   ERROR_CATCH(spmri_mri_inst(
               // DAC
               0.0, // Amplitude
               ALL_DACS, // DAC Select
               DO_WRITE, // Write
               DO_UPDATE, // Update
               DONT_CLEAR, // Clear
               // RF
               0, // freq reg
               0, // ph reg
               0, // tx enable
               0, // ph reset
               0, // rx enable
               7, // envelope freq reg
               0, // amp reg
               0, // cyclops phase
               // PulseBlaster
               0x00, // flags
               start, // data
               STOP, // opcode
               1.0 * us // delay
               ));


   printf("Board programmed.\n");

   // Starts pulse prog stored on board
   ERROR_CATCH(spmri_start());

   printf("Board is running...\n");

   pause();

   // Stops the board by resetting it
   ERROR_CATCH(spmri_stop());

   return 0;
}

