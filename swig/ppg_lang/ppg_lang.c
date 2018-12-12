#include <Python.h>
#include <stdio.h>
#include <math.h>
#include <time.h>

#include "mrispinapi.h"

char *error_message = "";

/* provide function that interprets series of tuples
 * and uses them to generate pulse program via SpinCore*/
/* PULSE: 'pulse', time_len, phase */
/* DELAY: 'delay', time_len */
/* MARKER: 'marker', string */
/* JUMPTO: 'jumpto', string, no. times */
DWORD jump_addresses[10];
int ppg_element(char *str_label, double firstarg, double secondarg){ /*takes 3 vars*/
    int error_status;
    if (strcmp(str_label,"pulse")==0){
        error_status = 0;
        printf("PULSE: length %0.1f phase %0.1f\n",firstarg,secondarg);
    }else if (strcmp(str_label,"delay")==0){
        error_status = 0;
        if(secondarg != 0){
            error_status = 1;
            error_message = "DELAY tuples should only be 'delay' followed by the delay";
        }
        printf("DELAY: length %0.1f\n",firstarg);
    }else if (strcmp(str_label,"marker")==0){
        error_status = 0;
        printf("MARKER: label %d, %d times\n",(int) firstarg,(int) secondarg);
        printf("READING TO MEMORY...\n");
        int label = (int) firstarg;
        unsigned int nTimes = (int) secondarg;
        printf("BEGINNING LOOP INSTRUCTION, jump address %04x...\n",jump_addresses[label]);
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
