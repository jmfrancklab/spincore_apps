#ifndef _DRIVER_OS_H
#define _DRIVER_OS_H

#ifdef __cplusplus
extern "C"
{
#endif

int os_count_boards (int vend_id);

int os_init (int card_num);
int os_close (int card_num);

int os_outp (int card_num, unsigned int address, char data);
char os_inp (int card_num, unsigned int address);

int os_outw (int card_num, unsigned int addresss, unsigned int data);
unsigned int os_inw (int card_num, unsigned int address);

#ifdef __cplusplus
}
#endif

#endif /* #ifndef _DRIVER_OS_H */
