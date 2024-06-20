#include <Python.h>
#include <stdio.h>
#include <math.h>
#include <time.h>

#include "mrispinapi.h"

#define ADC_OFFSET_MIN -256
#define ADC_OFFSET_MAX 256

#define ADC_OFFSET_NUM_POINTS (16*1024)
#define ADC_OFFSET_SW_MHZ (75.0/1.0)
#define ADC_OFFSET_SF_MHZ (0.0)

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

int configureTX(int adcOffset, double carrierFreq_MHz, double* tx_phases, int nPhases, double amplitude, unsigned int nPoints){
    int j;
    double freqs[1] = {carrierFreq_MHz};
    double amp[1] = {amplitude};
    ERROR_CATCH( spmri_init() );
    ERROR_CATCH( spmri_set_defaults() );
    ERROR_CATCH( spmri_set_adc_offset(adcOffset));
    ERROR_CATCH( spmri_set_frequency_registers( freqs, 1));
    // ERROR_CATCH( spmri_set_phase_registers( phases, 1 ));
    ERROR_CATCH( spmri_set_phase_registers( tx_phases, nPhases ));
    ERROR_CATCH( spmri_set_amplitude_registers( amp, 1));
    ERROR_CATCH( spmri_set_num_samples(nPoints));
    if(nPoints > 16384){
        printf("WARNING: TRYING TO ACQUIRE TOO MANY POINTS THAN BOARD CAN STORE.\n");
    }
    return 0;
}

double configureRX(double SW_kHz, unsigned int nPoints, unsigned int nScans, unsigned int nEchoes, unsigned int nPhaseSteps){
    double SW_MHz = SW_kHz / 1000.0;
    double adcFrequency_MHz = 75.0;
    int dec_amount;
    ERROR_CATCH( spmri_setup_filters(
                SW_MHz,
                nScans,
                0,
                &dec_amount
                ));
    double actual_SW = (adcFrequency_MHz * 1e6) / (double) dec_amount;
    double acq_time = ((double) nPoints) / ((double) actual_SW) * ((double) 1e3);
    int nSegments = nEchoes*nPhaseSteps;
    // following line is for debug only -- don't commit
    printf("DEBUG: You tried to set the SW to %0.3f kHz, and the closest allowed value is %0.3f kHz which differ by %g kHz, based on dec_amount %d\n",SW_kHz,actual_SW/1e3,SW_kHz-actual_SW/1e3,dec_amount);
    printf("DEBUG: I calculated this from an SW of %0.3f and nPoints %d \n",SW_kHz,nPoints);
    if(abs(actual_SW - 1e3*SW_kHz) > 1.0){
        printf("Error: You tried to set the SW to %0.3f kHz, but the closest allowed value is %0.3f kHz\n",SW_kHz,actual_SW/1e3);
        ERROR_CATCH(999);
    }
    if(nPoints*nEchoes*nPhaseSteps > 16384){
        printf("WARNING: TRYING TO ACQUIRE TOO MANY POINTS THAN BOARD CAN STORE.\n");
    }
    ERROR_CATCH( spmri_set_num_segments(nSegments));
    return acq_time;
}

int init_ppg(){
	BOARD_INFO* cur_board = spmri_get_current_board();
    // printf("information for this board:\n");
	// printf("imw_dac_amp_bits: %d\n",cur_board->imw_dac_amp_bits);
	// printf("imw_dac_addr_bits: %d\n",cur_board->imw_dac_addr_bits);
	// printf("imw_carrier_freq_bits: %d\n",cur_board->imw_carrier_freq_bits);
	// printf("imw_envelope_freq_bits: %d\n",cur_board->imw_envelope_freq_bits);
	// printf("imw_tx_phase_bits: %d\n",cur_board->imw_tx_phase_bits);
	// printf("imw_amp_bits: %d\n",cur_board->imw_amp_bits);
	// printf("imw_sin_phase_bits: %d\n",cur_board->imw_sin_phase_bits);
	// printf("imw_cos_phase_bits: %d\n",cur_board->imw_cos_phase_bits);
    ERROR_CATCH(spmri_start_programming());
    return 0;
}

int stop_ppg(){
    ERROR_CATCH(spmri_mri_inst(
                // DAC: Amplitude, DAC Select, Write, Update, Clear
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                0,0,0,0,0,7,0,0,
                // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                0x00,0,STOP,1.0*us
                ));
    return 0;
}

char *error_message = "";

/* provide function that interprets series of tuples
 * and uses them to generate pulse program via SpinCore*/
/* PULSE: 'pulse', time_len, phase */
/* DELAY: 'delay', time_len */
/* MARKER: 'marker', string */
/* JUMPTO: 'jumpto', string, no. times */
DWORD jump_addresses[10];

int ppg_element(char *str_label, double firstarg, int secondarg){ /*takes 3 vars*/
    int error_status;
    if (strcmp(str_label,"pulse")==0){
        error_status = 0;
        /* COMMAND FOR PROGRAMMING RF PULSE */
        ERROR_CATCH(spmri_mri_inst(
                    // DAC: Amplitude, DAC Select, Write, Update, Clear
                    0.0,ALL_DACS,DONT_WRITE,DONT_UPDATE,DONT_CLEAR,
                    // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                    0,(int) secondarg,1,0,0,7,0,0,
                    // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                    0x00,0,CONTINUE,firstarg*us
                    ));
    }else if (strcmp(str_label,"pulse_TTL")==0){
        error_status = 0;
        /* COMMAND FOR PROGRAMMING RF PULSE */
        ERROR_CATCH(spmri_mri_inst(
                    // DAC: Amplitude, DAC Select, Write, Update, Clear
                    0.0,ALL_DACS,DONT_WRITE,DONT_UPDATE,DONT_CLEAR,
                    // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                    0,(int) secondarg,1,0,0,7,0,0,
                    // PB: flags = TTL high BNC1, data, opcode -- listed in radioprocessor g manual, delay
                    0x01,0,CONTINUE,firstarg*us
                    ));
    }else if (strcmp(str_label,"phase_reset")==0){
        error_status = 0;
        if(secondarg != 0){
            error_status = 1;
            error_message = "PHASE RESET tuples should only be 'phase_reset' followed by the delay";
        }
        /* COMMAND FOR RESETTING PHASE */
        ERROR_CATCH(spmri_mri_inst(
                    // DAC: Amplitude, DAC Select, Write, Update, Clear
                    0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                    // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                    0,0,0,1,0,7,0,0,
                    // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                    0x00,0,CONTINUE,firstarg*us
                    ));
        /* PHASE RESET TRANSIENT DELAY */
        ERROR_CATCH(spmri_mri_inst(
                    // DAC: Amplitude, DAC Select, Write, Update, Clear
                    0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                    // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                    0,0,0,0,0,7,0,0,
                    // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                    0x00,0,CONTINUE,1.0*us
                    ));
    }else if (strcmp(str_label,"acquire")==0){
        error_status = 0;
        if(secondarg != 0){
            error_status = 1;

            error_message = "ACQUIRE tuples should only be 'acquire' followed by length of acquisition time";
        }
        /* COMMAND FOR PROGRAMMING DELAY */
        ERROR_CATCH(spmri_mri_inst(
                    // DAC: Amplitude, DAC Select, Write, Update, Clear
                    0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                    // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                    0,0,0,0,1,7,0,0,
                    // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                    0x00,0,CONTINUE,firstarg*ms
                    ));
    }else if (strcmp(str_label,"delay")==0){
        error_status = 0;
        if(secondarg != 0){
            error_status = 1;
            error_message = "DELAY tuples should only be 'delay' followed by the delay";
        }
        /* COMMAND FOR PROGRAMMING DELAY */
        ERROR_CATCH(spmri_mri_inst(
                    // DAC: Amplitude, DAC Select, Write, Update, Clear
                    0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                    // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                    0,0,0,0,0,7,0,0,
                    // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                    0x00,0,CONTINUE,firstarg*us
                    ));
    }else if (strcmp(str_label,"delay_TTL")==0){
        error_status = 0;
        if(secondarg != 0){
            error_status = 1;
            error_message = "DELAY tuples should only be 'delay' followed by the delay";
        }
        /* COMMAND FOR PROGRAMMING DELAY */
        ERROR_CATCH(spmri_mri_inst(
                    // DAC: Amplitude, DAC Select, Write, Update, Clear
                    0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                    // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                    0,0,0,0,0,7,0,0,
                    // PB: flags = TTL high BNC1, data, opcode -- listed in radioprocessor g manual, delay
                    0x01,0,CONTINUE,firstarg*us
                    ));
    }else if (strcmp(str_label,"marker")==0){
        error_status = 0;
        int label = (int) firstarg;
        unsigned int nTimes = (int) secondarg;
        ERROR_CATCH(spmri_read_addr( &jump_addresses[label] ));
        ERROR_CATCH(spmri_mri_inst(
                    // DAC: Amplitude, DAC Select, Write, Update, Clear
                    0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                    //RF
                    0,0,0,0,0,7,0,0,
                    // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                    0x00,nTimes,LOOP,1.0*us
                    ));
    }else if (strcmp(str_label,"jumpto")==0){
        error_status = 0;
        if(secondarg != 0){
            error_status = 1;
            error_message = "JUMPTO tuples should only provide label to which you wish to jump";
        }
        int label = (int) firstarg;
        ERROR_CATCH(spmri_mri_inst(
                    // DAC: Amplitude, DAC Select, Write, Update, Clear
                    0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                    // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                    0,0,0,0,0,7,0,0,
                    // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                    0x00,jump_addresses[label],END_LOOP,1.0*us
                    ));
    }else{
        error_status = 1;
        error_message = "unknown ppg element";
    }
    return(error_status);
}

char *exception_info() {
    return error_message;
}

int runBoard()
{
    ERROR_CATCH(spmri_start());
    int done = 0;
    int last_scan = 0;
    int status;
    unsigned int current_scan;
    while( done == 0)
    {
        ERROR_CATCH(spmri_get_status(&status));
        ERROR_CATCH(spmri_get_scan_count(&current_scan));
        if( status == 0x01 ) {
            done = 1; }
        else if(current_scan != last_scan) {
        last_scan = current_scan;
        printf("(SPINCORE): transient %d done\n",last_scan);
        }
        }
    return 0;
}

void getData(int* output_array, int length, unsigned int nPoints, unsigned int nEchoes, unsigned int nPhaseSteps){
    int* real = malloc(nPoints * nEchoes * nPhaseSteps * sizeof(int));
    int* imag = malloc(nPoints * nEchoes * nPhaseSteps * sizeof(int));
    int j;
    int index=0;
    ERROR_CATCH(spmri_read_memory(real, imag, nPoints*nEchoes*nPhaseSteps));
    for( j = 0 ; j < nPoints*nEchoes*nPhaseSteps ; j++){
        output_array[index] = real[j];
        output_array[index+1] = imag[j];
        index = index+2;
    }
    free(real);
    free(imag);
    return;
}

void stopBoard(){
    ERROR_CATCH(spmri_stop());
    return;
}

void tune(double carrier_freq)
{
    // ** Configure Board ** 
    // Initialize MRI SpinAPI
    ERROR_CATCH( spmri_init() );

    // Set all values on board to default values
    ERROR_CATCH( spmri_set_defaults() );

    // Carrier Frequency Registers
    // previously hard-coded carrier 14.902344
    double freq[1] = {carrier_freq};
    ERROR_CATCH( spmri_set_frequency_registers( freq, 1 ) );

    // Phase Registers
    double phase[1] = {0.0};
    ERROR_CATCH( spmri_set_phase_registers( phase, 1 ) );

    // Amplitude Registers
    double amp[1] = {1.0};
    ERROR_CATCH( spmri_set_amplitude_registers( amp, 1 ) );
    
    // ** Program Board **
    // Signal board that ready to start sending it instructions
    ERROR_CATCH( spmri_start_programming() );
    // Read current memory address for ability to return back to this point later on in the program

    // This instruction enables analog output
    DWORD branch_addr;
    ERROR_CATCH( spmri_read_addr( &branch_addr ) );
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
        1, // tx enable
        0, // phase select
        0, // rx enable
        7, // envelope frequency register (7=no shape)
        0, // amp register
        0, // cyclops phase (must be 0)
        // PulseBlaster Information
        0x00, // flags
        0, // data
        CONTINUE, // opcode
        4.0 * us // pulse time
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
                branch_addr, // data
                BRANCH, // opcode
                5000.0 * us // delay
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
               0, // data
               STOP, // opcode
               1.0 * us // delay
               ));

   // Starts the pulse program stored on board
   ERROR_CATCH(spmri_start());


   pause();

   // Stops the board by resetting it
   ERROR_CATCH(spmri_stop());
}

double adc_offset_get_dc_value(int adc_offset)
{
	double peak;
	ERROR_CATCH( adc_offset_configureBoard( adc_offset ) );
	ERROR_CATCH( adc_offset_programBoard( ) );
	ERROR_CATCH( runBoard( ) );
	ERROR_CATCH( adc_offset_readData( adc_offset, &peak ) );
	return peak;
}

int adc_offset_readData(int adc_offset, double* peak)
{
	int i;
	int real[ADC_OFFSET_NUM_POINTS];
	int imag[ADC_OFFSET_NUM_POINTS];
	double mag_out[ADC_OFFSET_NUM_POINTS];
	double mag_out_max;
	int mag_out_max_index;
	double dc_value;
	
	ERROR_CATCH(spmri_read_memory(real, imag, ADC_OFFSET_NUM_POINTS));
	
	dc_value = 0;
	for( i = 0 ; i < ADC_OFFSET_NUM_POINTS ; i++ ) {
        ////printf("for adc offset %d, point %d, I get %d\n",adc_offset,i,real[i]);
		dc_value += real[i];
	}
	
	// Felix output file
	char filename[128];
	snprintf(filename, 128, "adc_offest_%d.fid", adc_offset);
	ERROR_CATCH(spmri_write_felix(filename, "titleblock", ADC_OFFSET_NUM_POINTS,
		ADC_OFFSET_SW_MHZ * 1e6, ADC_OFFSET_SF_MHZ * 1e6 + 1e-6, real, imag));
	
	// DC frequency
	*peak = dc_value;
	
	return 0;
}

int adc_offset(int argc, char *argv[])
{
	double max_offset_result = adc_offset_get_dc_value(ADC_OFFSET_MAX);
	double min_offset_result = adc_offset_get_dc_value(ADC_OFFSET_MIN);


    if(max_offset_result==0 && min_offset_result==0){
        //printf("both max and min offset results are 0 -- try using an adc offset of 0\n");
        return 0;
    }
	
	double theoretical_adc_offset = (0 - min_offset_result) / (max_offset_result - min_offset_result) * (ADC_OFFSET_MAX - ADC_OFFSET_MIN) + ADC_OFFSET_MIN;
	int test_offset = round( theoretical_adc_offset );
	
	//printf("Correct ADC offset = %d\n", test_offset);
	
	return test_offset;
}

int adc_offset_configureBoard(int adc_offset)
{
	int dec_amount;
	
	ERROR_CATCH( spmri_init() );
	ERROR_CATCH( spmri_set_defaults() );
	ERROR_CATCH( spmri_stop() );
	
	// ADC offset
	ERROR_CATCH( spmri_set_adc_offset( adc_offset ) );
	
	ERROR_CATCH( spmri_set_num_samples( ADC_OFFSET_NUM_POINTS ) );
	
	ERROR_CATCH(spmri_setup_filters(
		ADC_OFFSET_SW_MHZ, // Spectral Width in MHz
		1, // Number of Scans
		0, // Not Used
		&dec_amount
	));
	
	// Carrier Frequency Registers
	double freqs[1] = {ADC_OFFSET_SF_MHZ}; // MHz
	ERROR_CATCH(spmri_set_frequency_registers( freqs, 1 ));
	
	return 0;
}
int adc_offset_programBoard( )
{
    ERROR_CATCH(spmri_start_programming());
    ppg_element("delay", 1.0, 0);
    double acq_time_us = ADC_OFFSET_NUM_POINTS / (ADC_OFFSET_SW_MHZ);
    ppg_element("acquire", acq_time_us*us/ms, 0);
    /*here*/
    stop_ppg();
    return 0;
}
