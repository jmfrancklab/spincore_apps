#include "driver-os.h"

/**
 * This function returns the number of boards with a given vendor id.
 *
 *\param vend_id The vendor ID user for SpinCore boards will be passed
 * as a paramter.
 *\return number of boards present, or -1 on error.
 */

int
os_count_boards (int vend_id)
{
  return 0;
}

/**
 * Initialize the OS so that it can access a given board. Nothing needs to be
 * written to the registers of the board itself. Rather this function should
 * perform some functions such as gaining access to the IO space used by the
 * board, etc. Basically this needs to do whatever must be done to ensure
 * that the os_outx, and os_inx functions will work properly.
 *
 * Any initialization that may be needed on the board itself is done at a higher
 * level after this function exits (by using os_outp, etc.) and the implementor
 * of this file need not be concerned with this procedure.
 *
 *\return -1 on error
 */
int
os_init (int card_num)
{
  return 0;
}

/**
 * End access with the board. This should do the opposite of whatever was
 * done is os_init()
 *\return -1 on error
 */
int
os_close (int card_num)
{
  return 0;
}

// The following functions read and write to the IO address space of the card.
//
// For all of these functions, address is given as an offset of the base address.
// For example if the card has the IO addresses 0x0400-0x040F, 
// os_outp(0, 4, 42)
// should write the value 42 to the absolute IO address 0x0404 of the first
// card present in the system.
//


/**
 * Write a byte of data to the given card, at given the address.
 * \return -1 on error
 */

int
os_outp (int card_num, unsigned int address, char data)
{
  return 0;
}

/**
 * Read a byte of data from the given card, at the given address
 * \return value from IO address
 */
char
os_inp (int card_num, unsigned int address)
{
  return 0;
}

/**
 * Write a 32 bit word to the given card, at the given address
 *\return -1 on error
 */

int
os_outw (int card_num, unsigned int addresss, unsigned int data)
{
  return 0;
}

/**
 * Read a 32 bit word from the given card, at the given address
 *\return value form IO address
 */

unsigned int
os_inw (int card_num, unsigned int address)
{
  return 0;
}
