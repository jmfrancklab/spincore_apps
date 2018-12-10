#include <Python.h>
#include <stdio.h>

char *error_message = "";

/* provide a function that interprets tuples an uses them to generate a pulse program*/
int ppg_element(char *str_label, double firstarg, double secondarg){
    int error_status;
    if (strcmp(str_label,"pulse")==0){
        error_status = 0;
        printf("PULSE: length %0.1f phase %0.1f\n",firstarg,secondarg);
    }else if (strcmp(str_label,"delay")==0){
        error_status = 0;
        if(secondarg != 0){
            error_status = 1;
            error_message = "Delay tuples should only be 'delay' followed by the delay";
        }
        printf("DELAY: length %0.1f\n",firstarg);
    }else if (strcmp(str_label,"marker")==0){
        error_status = 0;
        if(secondarg != 0){
            error_status = 1;
            error_message = "Marker tuples should only be 'marker' followed by the name";
        }
        printf("MARKER: %d\n",(int) firstarg);
    }else if (strcmp(str_label,"jumpto")==0){
        error_status = 0;
        printf("JUMPTO: label %d, %d times\n",(int) round(firstarg),
                (int) round(secondarg));
    }else{
        error_status = 1;
        error_message = "unknown ppg element";
    }
    return(error_status);
}

char *exception_info() {
	return error_message;
}
