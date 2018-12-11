#include <Python.h>
#include <stdio.h>
#include "mrispinapi.h"
char *error_message = "";

/* provide a function that interprets tuples an uses them to generate a pulse program*/
int ppg_element(char *str_label, double firstarg, double secondarg){
    DWORD DWORDS[50]; /* large amount -- probably unnecessary */
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
        if ((int) firstarg==0){
            DWORDS[(int) firstarg] = 14;} /* numbers 14 and 24 mean nothing */
        else if ((int) firstarg==1){
            DWORDS[(int) firstarg] = 24;}
        printf("%d\n", DWORDS[(int) firstarg]);
    }else if (strcmp(str_label,"jumpto")==0){
        error_status = 0;
        if(secondarg != 0){
            error_status = 1;
            error_message = "JUMPTO tuples should only provide label to which you wish to jump";
        }
        printf("JUMPTO: label %d\n",(int) round(firstarg));
    }else{
        error_status = 1;
        error_message = "unknown ppg element";
    }
    return(error_status);
}

char *exception_info() {
	return error_message;
}
