/**
 * 
 * 
 */
int
os_usb_count_devices (int vendor_id)
{
  return 0;
}

/**
 * 
 * 
 * \returns A negative number is returned on error. 0 is returned on success
 */
int
os_usb_init (int dev_num)
{
  return 0;
}

int
os_usb_close ()
{
  return 0;
}

int
os_usb_reset_pipes (int dev_num)
{
  return 0;
}

/**
 * Write data to the USB device
 * \param pipe endpoint to write data too
 * \param data buffer holding data to be written
 * \param size Size in bytes of the buffer
 * \returns 0 on success, or a negative number on failure
 */
int
os_usb_write (int dev_num, int pipe, const void *data, int size)
{
  return 0;
}

/**
 * Read data from the USB device.
 * \param pipe Endpoint to read data from
 * \param data Buffer to hold the data that will be read
 * \param size Size in bytes of data to read
 * \returns 0 on success, or a negative number on failure
 */
int
os_usb_read (int dev_num, int pipe, void *data, int size)
{
  return 0;
}
