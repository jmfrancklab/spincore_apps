#ifndef USB_H_
#define USB_H_

#ifdef __cplusplus
extern "C"
{
#endif

int usb_write_reg (unsigned int addr, unsigned int data);
int usb_read_reg (unsigned int addr, unsigned int *data);
int usb_read_ram (unsigned int bank, unsigned int start_addr,
		  unsigned int len, char *data);
int usb_write_ram (unsigned int bank, unsigned int start_addr,
		   unsigned int len, const char *data);
int usb_write_address (int addr);
int usb_write_data (const void *data, int nData);

void usb_set_device (int board_num);

int usb_do_outp (unsigned int address, char data);

int usb_reset_gpif (int dev_num);

#ifdef __cplusplus
}
#endif

// RAM banks for usb_{read,write}_ram
#define BANK_DATARAM 0x1000
#define BANK_DDSRAM 0x2000

// Definitions for low-level transfer stuff
#define ADDR_REG_EN 0x80
#define RST_L 0x40
#define DO_RENUM 0x20
#define DO_GPIF_RESET 0x10

#define DO_LITE 0x02
#define DO_HEAVY 0x01

#define EP1OUT 0x01
#define EP2OUT 0x02
#define EP6IN  0x86

#endif /*USB_H_ */
