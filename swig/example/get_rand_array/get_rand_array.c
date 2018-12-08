/* File get_rand_array.cpp */
#include "get_rand_array.h"

void get_rand_array(double* output_array, int length){

  for (int i=0; i < length; i++)
    output_array[i] = ((double) rand()) / RAND_MAX;
  return;
}
