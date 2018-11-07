/*
 * Copyright (c) 2009 SpinCore Technologies, Inc.  http://www.spincore.com
 * This software is provided 'as-is', without any express or implied
 * warranty. In no event will the authors be held liable for any damages
 * arising from the use of this software. Permission is granted to anyone
 * to use this software for any purpose, including commercial applications, 
 * and to alter it and redistribute it freely, subject to the following
 * restrictions: 1. The origin of this software must not be misrepresented; 
 * you must not claim that you wrote the original software. If you use this
 * software in a product, an acknowledgment in the product documentation
 * would be appreciated but is not required. 2. Altered source versions must 
 * be plainly marked as such, and must not be misrepresented as being the
 * original software. 3. This notice may not be removed or altered from any
 * source distribution. 
 */

/**
 * \file read_firmware.c
 * \brief This example program will print the firmware(s) of detected device(s).
 * \ingroup genex
 */

#include <stdio.h>
#include <stdlib.h>

#include "spinapi.h"

#define FW_DEV_MSK 0xFF00
#define FW_REV_MSK 0x00FF

void pause(void)
{
	printf("Press enter to continue...");
	char buffer = getchar();
	while(buffer != '\n' && buffer != EOF);
	getchar();
}

int main(int argc, char **argv)
{
	int i, fw, device, revision, numBoards;

	// Uncommenting the line below will generate a debug log in your
	// current
	// directory that can help debug any problems that you may be
	// experiencing 
	// pb_set_debug(1);

	printf("Copyright (c) 2010 SpinCore Technologies, Inc.\n\n");

	printf("Using SpinAPI library version %s\n", pb_get_version());

	numBoards = pb_count_boards();
	printf("Detected %d Boards.\n", numBoards);

	for (i = 0; i < numBoards; i++) {
		pb_select_board(i);	/* Select the ith board */

		if (pb_init()) {
			printf("Error initializing board: %s\n", pb_get_error());
			pause();
			return -1;
		}

		fw = pb_get_firmware_id();
		device = (fw & FW_DEV_MSK) >> 8;	/* Get device number from ID */
		revision = (fw & FW_REV_MSK);	/* Get revision number from ID */

		printf("Board %d Firmware ID: %d-%d\n", i, device, revision);

		pb_close();
	}

	printf("\n\n");
	pause();

	return 0;
}
