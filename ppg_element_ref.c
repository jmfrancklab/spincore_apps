int ppg_element(char *str_label, double firstarg, int secondarg){ /*takes 3 vars*/
    int error_status;
    if (strcmp(str_label,"pulse")==0){
        error_status = 0;
        printf("PULSE: length %0.1f us phase %0.1f\n",firstarg,secondarg);
        /* COMMAND FOR PROGRAMMING RF PULSE */
        ERROR_CATCH(spmri_mri_inst(
                    0.0,
                    ALL_DACS,
                    DONT_WRITE,
                    DONT_UPDATE,
                    DONT_CLEAR,
                    0,
                    (int) secondarg,
                    1,
                    0,
                    0,
                    7,
                    0,
                    0,
                    0x00,
                    0,
                    CONTINUE,
                    firstarg * us
                    ));
    }else if (strcmp(str_label,"pulse_TTL")==0){
        error_status = 0;
        printf("TRIGGERED PULSE: length %0.1f us phase %0.1f\n",firstarg,secondarg);
        /* COMMAND FOR PROGRAMMING RF PULSE */
        ERROR_CATCH(spmri_mri_inst(
                    0.0,
                    ALL_DACS,
                    DONT_WRITE,
                    DONT_UPDATE,
                    DONT_CLEAR,
                    0,
                    (int) secondarg,
                    1,
                    0,
                    0,
                    7,
                    0,
                    0,
                    0x01,
                    0,
                    CONTINUE,
                    firstarg * us
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
                    0.0,
                    ALL_DACS,
                    DO_WRITE,
                    DO_UPDATE,
                    DONT_CLEAR,
                    0,
                    0,
                    0,
                    1,
                    0,
                    7,
                    0,
                    0,
                    0x00,
                    0,
                    CONTINUE,
                    firstarg * us
                    ));
        /* PHASE RESET TRANSIENT DELAY */
        ERROR_CATCH(spmri_mri_inst(
                    0.0,
                    ALL_DACS,
                    DO_WRITE,
                    DO_UPDATE,
                    DONT_CLEAR,
                    0,
                    0,
                    0,
                    0,
                    0,
                    7,
                    0,
                    0,
                    0x00,
                    0,
                    CONTINUE,
                    1.0 * us
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
                    0.0,
                    ALL_DACS,
                    DO_WRITE,
                    DO_UPDATE,
                    DONT_CLEAR,
                    0,
                    0,
                    0,
                    0,
                    1,
                    7,
                    0,
                    0,
                    0x00,
                    0,
                    CONTINUE,
                    firstarg*ms
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
                    0.0,
                    ALL_DACS,
                    DO_WRITE,
                    DO_UPDATE,
                    DONT_CLEAR,
                    0,
                    0,
                    0,
                    0,
                    0,
                    7,
                    0,
                    0,
                    0x00,
                    0,
                    CONTINUE,
                    firstarg * us
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
                    0.0,
                    ALL_DACS,
                    DO_WRITE,
                    DO_UPDATE,
                    DONT_CLEAR,
                    0,
                    0,
                    0,
                    0,
                    0,
                    7,
                    0,
                    0,
                    0x01,
                    0,
                    CONTINUE,
                    firstarg * us
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
                    0.0,
                    ALL_DACS,
                    DO_WRITE,
                    DO_UPDATE,
                    DONT_CLEAR,
                    0,
                    0,
                    0,
                    0,
                    0,
                    7,
                    0,
                    0,
                    0x00,
                    nTimes,
                    LOOP,
                    1.0 * us
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
                    0.0,
                    ALL_DACS,
                    DO_WRITE,
                    DO_UPDATE,
                    DONT_CLEAR,
                    0,
                    0,
                    0,
                    0,
                    0,
                    7,
                    0,
                    0,
                    0x00,
                    jump_addresses[label],
                    END_LOOP,
                    1.0 * us
                    ));
        printf("ENDING END_LOOP INSTRUCTION...\n");
    }else{
        error_status = 1;
        error_message = "unknown ppg element";
    }
    return(error_status);
}
