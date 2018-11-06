#ifndef DRIVER_USB_H_
#define DRIVER_USB_H_

#ifdef __cplusplus
extern "C"
{
#endif

int os_usb_count_devices (int vendor_id);
int os_usb_init (int dev_num);
int os_usb_close ();
int os_usb_write (int dev_num, int pipe, const void *data, int size);
int os_usb_read (int dev_num, int pipe, void *data, int size);
int os_usb_reset_pipes (int dev_num);

#ifdef __cplusplus
}
#endif

#endif /*DRIVER_USB_H_ */
