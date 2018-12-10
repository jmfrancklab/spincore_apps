#include <Python.h>
#include <stdio.h>

char *error_message = "";

/* provide a function that interprets tuples an uses them to generate a pulse program*/
int ppg_element(char *str_label, double firstarg, double secondarg){
    printf("received a pulse sequence element of type %s with first argument %f and second argument %f\n",str_label,firstarg,secondarg);
    int error_status;
    if (strcmp(str_label,"pulse")==0){
        error_status = 0;
        printf("found a pulse with phase %0.1f and length %0.1f\n",firstarg,secondarg);
    }else if (strcmp(str_label,"delay")==0){
        error_status = 0;
        if(secondarg != 0){
            error_status = 1;
            error_message = "third element of delay tuple must be zero";
        }
        printf("found a delay of length %0.1f\n",firstarg);
    }else{
        error_status = 1;
        error_message = "unknown ppg element";
    }
    return(error_status);
}

char *exception_info() {
	return error_message;
}
