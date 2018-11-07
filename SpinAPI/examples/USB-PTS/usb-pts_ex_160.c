/*! \file usb-pts_160.c
 * \brief This program offers a simple example of how to use the  spinpts160 function.
 * The  spinpts160 function is designed to control PTS160 frequency synthesizers when 
 * used in conjunction with a SpinCore Technologies USB-PTS device.  To use this
 * function in your own program, simply remove the main function and add this 
 * file to your project. Note that you will also need to include the header 
 * file spinpts.h and link to the dll spinpts.dll which can both be found in 
 * the main directory.
 *
 * Please visit http://www.spincore.com/CD/USB-PTS/SpinPTS/Installation/
 * for more installation and use instructions.
 *
 * The frequency value passed to this function should be a double with a value
 * between 0.1 and 159.999 999 9, corresponding to 0.1MHz and 159.999 999 9MHz
 * respectively.  Digits beyond the 7th decimal place will be ignored. 
 *
 * *****NOTE******* Actual resolution of output signal for the PTS160 is 0.1 Hz 
 * to 100 KHz, optional. Please verify resolution of your particular device. If 
 * your device has a 100 kHz resolution, the USB-PTS device will output signals 
 * for lower resolution but they will be ignored by the PTS160.
 *
 *------------------------------------------------------------------------------
 * NOTE: This version only supports control of the PTS160 frequency synthesizer.
 *
 *       If you have a different PTS model, please visit http://www.spincore.com
 *       to check if a newer version of this code exists that will support your
 *       particular PTS model. If your model is not supported please contact  
 *       SpinCore for support developement.
 *------------------------------------------------------------------------------
 *
 * *****Warning*****  Do not use clock faster than 50MHz with this board.
 *
 * $Date: 2008/02/21 14:30:24 $
 *
 * To get the latest version of this code, or to contact us for support, please
 * visit http://www.spincore.com
 *
 */

/* Copyright (c) 2009 SpinCore Technologies, Inc.
 *
 * This software is provided 'as-is', without any express or implied warranty. 
 * In no event will the authors be held liable for any damages arising from the 
 * use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose, 
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 * 1. The origin of this software must not be misrepresented; you must not
 * claim that you wrote the original software. If you use this software in a
 * product, an acknowledgment in the product documentation would be appreciated
 * but is not required.
 * 2. Altered source versions must be plainly marked as such, and must not be
 * misrepresented as being the original software.
 * 3. This notice may not be removed or altered from any source distribution.
 */

#define PTS160
 
#include <stdio.h>
#include <stdlib.h>
#include "spinapi.h"

void printLicense(void);
int input_freq(double *retFreq);

int main(int argc, char* argv[])
{
	double maxFreq = 160;
	int is160 = 1;
	int is3200 = 0;
	int allowPhase = 0;
	int noPTS = 1;
	
    double frequency;
    
    printLicense();
    printf ("USB Interface to PTS Synthesizer developed by SpinCore Technologies\n\n");
    printf ("Using spinapi library version %s\n", pb_get_version ());
    
    while(1)
    {
    	//User input frequency
    	input_freq(&frequency);
 	

        if(frequency < 0.0 || frequency > maxFreq)
        {
            printf("Invalid Frequency! Must be between 0 and %lf MHz.\n", maxFreq);
            system("pause");
            return -1;  
        }

        else if(frequency == 0.0)
        {
            printf("Program exited!\n");
            system("pause");
            return 0;
        }
        else
        {
            set_pts(maxFreq, is160, is3200, allowPhase, noPTS, frequency, 0);
            printf("%s\n", spinpts_get_error() );	//format check OK, send to PTS
            system("pause");
        }
    }
    return 0;

}

void printLicense(void)
{
     printf("Copyright (c) 2009 SpinCore Technologies, Inc.\n");
     printf(" http://www.spincore.com\n\n");
     printf("This software is provided 'as-is', without any express or implied warranty.\n");
     printf("In no event will the authors be held liable for any damages arising from the\n"); 
     printf("use of this software.\n");
     printf("\n");
     printf("Permission is granted to anyone to use this software for any purpose,\n");
     printf("including commercial applications, and to alter it and redistribute it\n");
     printf("freely, subject to the following restrictions:\n");
     printf("\n");
     printf("1. The origin of this software must not be misrepresented; you must not\n");
     printf("claim that you wrote the original software. If you use this software in a\n");
     printf("product, an acknowledgment in the product documentation would be appreciated\n");
     printf("but is not required.\n");
     printf("2. Altered source versions must be plainly marked as such, and must not be\n");
     printf("misrepresented as being the original software.\n");
     printf("3. This notice may not be removed or altered from any source distribution.\n\n");
     system("pause");
     system("cls");
     return;
}

int input_freq(double *retFreq)
{	
	char freq[256];
	double user_input = -1.0;
	char* user_end;	
		
	do {
		fflush(stdin);
		printf("\nPlease enter the desired frequency (Enter 0 to quit): ");
		scanf("%256s", freq);
		user_input = strtod(freq,&user_end);
	}	while(user_end[0] != '\0');

    *retFreq = user_input;
}
