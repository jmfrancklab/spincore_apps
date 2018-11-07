/* Copyright (c) 2009 SpinCore Technologies, Inc.
 *   http://www.spincore.com
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

 /**
 * \file pb_start.c
 * \brief This program sends a software trigger to the selected board.
 * \ingroup genex
 */

#include <stdio.h>
#include <stdlib.h>

#include "spinapi.h"

int detect_boards();
int select_board(int numBoards);

void pause(void)
{
	printf("Press enter to continue...");
	char buffer = getchar();
	while(buffer != '\n' && buffer != EOF);
	getchar();
}

int main(int argc, char **argv)
{
	int numBoards;

	//Uncommenting the line below will generate a debug log in your current
	//directory that can help debug any problems that you may be experiencing   
	//pb_set_debug(1);  

	printf("Copyright (c) 2010 SpinCore Technologies, Inc.\n\n");

	printf("Using SpinAPI library version %s\n", pb_get_version());

	/*If there is more than one board in the system, have the user specify. */
	if ((numBoards = detect_boards()) > 1) {
		select_board(numBoards);
	}

	if (pb_init() != 0) {
		printf("Error initializing board: %s\n", pb_get_error());
		pause();
		return -1;
	}

	if (pb_start()) {
		printf("Error occurred trying to trigger board: %s\n\n", pb_get_error());
	}
	else {
		printf("Board triggered successfully\n\n");
	}

	pb_close();

	pause();
	return 0;
}

int detect_boards()
{
	int numBoards;

	numBoards = pb_count_boards();	/*Count the number of boards */

	if (numBoards <= 0) {
		printf
		    ("No Boards were detected in your system. Verify that the board "
		     "is firmly secured in the PCI slot.\n\n");
		pause();
		exit(-1);
	}

	return numBoards;
}

int select_board(int numBoards)
{
	int choice;

	do {
		printf
		    ("Found %d boards in your system. Which board should be used? "
		     "(0-%d): ", numBoards, numBoards - 1);
		fflush(stdin);
		scanf("%d", &choice);

		if (choice < 0 || choice >= numBoards) {
			printf("Invalid Board Number (%d).\n", choice);
		}
	} while (choice < 0 || choice >= numBoards);

	pb_select_board(choice);
	printf("Board %d selected.\n", choice);

	return choice;
}
