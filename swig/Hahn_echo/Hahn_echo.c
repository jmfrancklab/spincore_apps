#include <stdio.h>
#include <math.h>
#include <time.h>

#include "mrispinapi.h"

#define ERROR_CATCH(arg) error_catch(arg,__LINE__)

char *get_time()
{
    time_t ltime;
    time(&ltime);
    return ctime(&ltime);
}

void pause(void)
{
    printf("Press enter to exit...");
    // flushing input stream
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

int configureBoard(int adcOffset, double carrierFreq_MHz, double tx_phase, double amplitude){
    double freqs[1] = {carrierFreq_MHz};
    double phase[1] = {tx_phase};
    double amp[1] = {amplitude};
    ERROR_CATCH( spmri_init() );
    printf("SpinAPI initialized...");
    ERROR_CATCH( spmri_set_defaults() );
    printf("Set to defaults...");
    ERROR_CATCH( spmri_set_adc_offset(adcOffset));
    ERROR_CATCH( spmri_set_frequency_registers( freqs, 1));
    ERROR_CATCH( spmri_set_phase_registers( phase, 1 ));
    ERROR_CATCH( spmri_set_amplitude_registers( amp, 1));
    
    return 0;
}

int programBoard(int nScans, double p90, double tau){
    DWORD loop_addr;
    ERROR_CATCH(spmri_start_programming());
    ERROR_CATCH( spmri_read_addr( &loop_addr ) );
    // LOOP
    ERROR_CATCH(spmri_mri_inst(
                0.0, // DAC
                ALL_DACS, // DAC SELECT
                DO_WRITE, // WRITE
                DO_UPDATE, // UPDATE
                DONT_CLEAR, // CLEAR
                //RF
                0, // freq reg
                0, // phase reg
                0, // tx enable
                1, // phase reset 
                0, // rx enable
                7, // envelope freq
                0, // amp reg
                0, // cyclops (default)
                // Pulse Blaster
                0x00, // flags = TTL low (off)
                nScans, // data
                LOOP, // opcode
                1.0 * us // delay
                ));
    // PHASE RESET DELAY
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF
                0,0,0,0,0,7,0,0,
                // PB
                0x00,0,CONTINUE,1.0*us
                ));
    // PULSE
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DONT_WRITE,DONT_UPDATE,DONT_CLEAR,
                // RF
                0,0,1,0,0,7,0,0,
                // PB
                0x00,0,CONTINUE,p90*us
                ));
    // DELAY
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF
                0,0,0,0,0,7,0,0,
                // PB
                0x00,0,CONTINUE,tau*us
                ));
    // DELAY
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF
                0,0,0,0,0,7,0,0,
                // PB
                0x00,loop_addr,END_LOOP,1.0*us
                ));
    // STOP
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF
                0,0,0,0,0,7,0,0,
                // PB
                0x00,0,STOP,1.0*us
                ));
    return 0;
}

int runBoard(void)
{
    ERROR_CATCH(spmri_start());
    printf("Board is running...");
    pause();
    ERROR_CATCH(spmri_stop());
    return 0;
}

int spincore_stop(void)
{
    ERROR_CATCH( spmri_stop() );
    return 0;
}


