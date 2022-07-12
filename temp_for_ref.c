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
	double max_offset_result = get_dc_value(ADC_OFFSET_MAX);
	double min_offset_result = get_dc_value(ADC_OFFSET_MIN);


    if(max_offset_result==0 && min_offset_result==0){
        printf("both max and min offset results are 0 -- try using an adc offset of 0\n");
        return 0;
    }
	
	double theoretical_adc_offset = (0 - min_offset_result) / (max_offset_result - min_offset_result) * (ADC_OFFSET_MAX - ADC_OFFSET_MIN) + ADC_OFFSET_MIN;
	int test_offset = round( theoretical_adc_offset );
	
	printf("Correct ADC offset = %d\n", test_offset);
	
	return 0;
}

double get_dc_value(int adc_offset)
{
	double peak;
	ERROR_CATCH( configureBoard( adc_offset ) );
	ERROR_CATCH( programBoard( ) );
	ERROR_CATCH( runScan( ) );
	ERROR_CATCH( readData( adc_offset, &peak ) );
	return peak;
}

int configureBoard(int adc_offset)
{
	int dec_amount;
	
	ERROR_CATCH( spmri_init() );
	ERROR_CATCH( spmri_set_defaults() );
	ERROR_CATCH( spmri_stop() );
	
	// ADC offset
	ERROR_CATCH( spmri_set_adc_offset( adc_offset ) );
	
	ERROR_CATCH( spmri_set_num_samples( NUM_POINTS ) );
	
	ERROR_CATCH(spmri_setup_filters(
		SW_MHZ, // Spectral Width in MHz
		1, // Number of Scans
		0, // Not Used
		&dec_amount
	));
	
	// Carrier Frequency Registers
	double freqs[1] = {SF_MHZ}; // MHz
	ERROR_CATCH(spmri_set_frequency_registers( freqs, 1 ));
	
	return 0;
}

int programBoard( )
{
	ERROR_CATCH(spmri_start_programming());
	
	// Start
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
		7, // envelope frequency register (7 = no shape)
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		CONTINUE, // opcode
		1.0 * us // delay
	));
	
	double acq_time_us = NUM_POINTS / (SW_MHZ);
	
	// Acquire Data
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
		1, // rx enable
		7, // envelope frequency register (7 = no shape)
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		CONTINUE, // opcode
		acq_time_us * us // delay
	));
	
	// Stop
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
		7, // envelope frequency register (7 = no shape)
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		STOP, // opcode
		1.0 * us // delay
	));
	
	return 0;
}

int configureTX(int adcOffset, double carrierFreq_MHz, double* tx_phases, int nPhases, double amplitude, unsigned int nPoints){
    int j;
    printf("***");
    printf("RECEIVED %d TX PHASES...\n",nPhases);
    for(j=0;j<nPhases;j++){
        printf("%f\n",tx_phases[j]);
    }
    double freqs[1] = {carrierFreq_MHz};
    double amp[1] = {amplitude};
    ERROR_CATCH( spmri_init() );
    printf("SpinAPI initialized...");
    ERROR_CATCH( spmri_set_defaults() );
    printf("Set to defaults...");
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
    printf("Decimation: %d\n", dec_amount);
    printf("Actual SW: %f Hz\n", actual_SW);
    double acq_time = nPoints / actual_SW * 1000.0;
    printf("Acq time: %f ms\n", acq_time);
    int nSegments = nEchoes*nPhaseSteps;
    printf("Number of segements (i.e., buffers): %d\n",nSegments);
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
    printf("Initializing pulse programming...\n");
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
        printf("PULSE: length %0.1f us phase %0.1f\n",firstarg,secondarg);
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
        printf("TRIGGERED PULSE: length %0.1f us phase %0.1f\n",firstarg,secondarg);
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
        printf("PHASE RESET: length %0.1f us\n",firstarg);
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
        printf("ACQUIRE: length %0.1f ms\n",firstarg);
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
        printf("DELAY: length %g s\n",firstarg/1e6);
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
        printf("TRIGGERED DELAY: length %0.1f us \n",firstarg);
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
        printf("MARKER: label %d, %d times\n",(int) firstarg,(double) secondarg);
        printf("READING TO MEMORY...\n");
        int label = (int) firstarg;
        unsigned int nTimes = (int) secondarg;
        ERROR_CATCH(spmri_read_addr( &jump_addresses[label] ));
        printf("BEGINNING LOOP INSTRUCTION, jump address %04x...\n",jump_addresses[label]);
        ERROR_CATCH(spmri_mri_inst(
                    // DAC: Amplitude, DAC Select, Write, Update, Clear
                    0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                    //RF
                    0,0,0,0,0,7,0,0,
                    // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                    0x00,nTimes,LOOP,1.0*us
                    ));
        printf("ENDING LOOP INSTRUCTION...\n");
    }else if (strcmp(str_label,"jumpto")==0){
        error_status = 0;
        if(secondarg != 0){
            error_status = 1;
            error_message = "JUMPTO tuples should only provide label to which you wish to jump";
        }
        printf("JUMPTO: label %d\n",(int) firstarg);
        int label = (int) firstarg;
        printf("BEGINNING END_LOOP INSTRUCTION, marker address %04x...\n",jump_addresses[label]);
        ERROR_CATCH(spmri_mri_inst(
                    // DAC: Amplitude, DAC Select, Write, Update, Clear
                    0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                    // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                    0,0,0,0,0,7,0,0,
                    // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                    0x00,jump_addresses[label],END_LOOP,1.0*us
                    ));
        printf("ENDING END_LOOP INSTRUCTION...\n");
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
    printf("Board is running...\n");
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
            printf("Current scan: %d\n", current_scan);
        last_scan = current_scan;
        }
        }
    printf("Scan completed.\n");
    return 0;
}

void getData(int* output_array, int length, unsigned int nPoints, unsigned int nEchoes, unsigned int nPhaseSteps, char* output_name){
    int* real = malloc(nPoints * nEchoes * nPhaseSteps * sizeof(int));
    int* imag = malloc(nPoints * nEchoes * nPhaseSteps * sizeof(int));
    int j;
    int index=0;
    printf("Reading data...\n");
    ERROR_CATCH(spmri_read_memory(real, imag, nPoints*nEchoes*nPhaseSteps));
    printf("Read data. Creating array...\n");
    for( j = 0 ; j < nPoints*nEchoes*nPhaseSteps ; j++){
        output_array[index] = real[j];
        output_array[index+1] = imag[j];
        index = index+2;
    }
    printf("Finished getting data.\n");
    free(real);
    free(imag);
    return;
}

void stopBoard(){
    printf("Calling STOP BOARD...\n");
    //pause();
    ERROR_CATCH(spmri_stop());
    printf("Stopped pulse program. Reset board.\n");
    return;
}

void tune(double carrier_freq)
{
    // ** Configure Board ** 
    // Initialize MRI SpinAPI
    ERROR_CATCH( spmri_init() );

    printf("SpinAPI initialized.\n");
    // Set all values on board to default values
    ERROR_CATCH( spmri_set_defaults() );

    // Carrier Frequency Registers
    // previously hard-coded carrier 14.902344
    printf("I'm using a carrier frequency of %0.6f", carrier_freq);
    double freq[1] = {carrier_freq};
    ERROR_CATCH( spmri_set_frequency_registers( freq, 1 ) );

    // Phase Registers
    double phase[1] = {0.0};
    ERROR_CATCH( spmri_set_phase_registers( phase, 1 ) );

    // Amplitude Registers
    double amp[1] = {1.0};
    ERROR_CATCH( spmri_set_amplitude_registers( amp, 1 ) );
    
    // ** Program Board **
    printf("RPG match/tune in time domain \n\n");
    printf("FREQUENCY: %lf \n",freq[0]);
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

   printf("Board programmed.\n");

   // Starts the pulse program stored on board
   ERROR_CATCH(spmri_start());

   printf("Board is running...\n");

   pause();

   // Stops the board by resetting it
   ERROR_CATCH(spmri_stop());
}
