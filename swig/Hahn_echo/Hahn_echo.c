#include <stdio.h>
#include <math.h>
#include <time.h>

#include "mrispinapi.h"

char *get_time()
{
    time_t ltime;
    time(&ltime);
    return ctime(&ltime);
}

