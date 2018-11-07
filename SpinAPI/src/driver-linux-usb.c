#include <stdio.h>
#include <stdlib.h>
#include <usb.h>

#include "debug.h"
#include "usb.h"
#include "util.h"

#define VENDOR_ID 0x0403
#define MAX_IO_WAIT_TIME 500

static usb_dev_handle** handles = 0;
static struct usb_device** devices = 0;
int pid_list[128] = { 0 };

/**
 * Count SpinCore devices on the USB bus.
 * 
 */
int os_usb_count_devices(int vendor_id)
{
    int d = 0;

    struct usb_bus* bus;
    struct usb_bus* busses;
    struct usb_device* device;

    debug("os_usb_count_devices called\n");
    
    usb_init();
    usb_find_busses();
    usb_find_devices();

    busses = usb_get_busses();

    // Check all the USB busses.
    for (bus = busses; bus; bus = bus->next)
    {
        // And on each bus, check each device.
        for (device = bus->devices; device; device = device->next)
        {
            if (device->descriptor.idVendor == VENDOR_ID)
                d++;
        }
    }

	return d;
}

/**
 * Unique USB device identifier is idVendor << 16 | idProduct
 * 
 * \returns A negative number is returned on error.
 * description of the error. 0 is returned on success
 */
int os_usb_init(int dev_num)
{
    struct usb_bus* bus;
    struct usb_bus* busses;
    struct usb_device* device;
    int number_of_devices = os_usb_count_devices(VENDOR_ID);
    int d = dev_num;
    int interface;

    debug("os_usb_init called\n");

    // initialize array of handles, if necessary.
    if (!handles)
        handles = calloc(number_of_devices, sizeof(usb_dev_handle*));
    if (!devices)
        devices = calloc(number_of_devices, sizeof(struct usb_device*));
    
    usb_init();
    usb_find_busses();
    usb_find_devices();

    busses = usb_get_busses();

    // find the device by counting through the devices.
    // this is inefficient, but most likely, only a small number of devices are involved.
    // Check all the USB busses.
    for (bus = busses; bus; bus = bus->next)
    {
        // And on each bus, check each device.
        for (device = bus->devices; device; device = device->next)
        {
            if (device->descriptor.idVendor == VENDOR_ID)
                d--;
            if (d == -1)
                break;
        }
        if (d == -1)
            break;
    }
    
    if (d != -1)
    {
    	debug(DEBUG_ERROR, "os_usb_init: device not found. Device not found.");
      return -1;
    }

    devices[dev_num] = device;
    handles[dev_num] = usb_open(device);
    pid_list[dev_num] = device->descriptor.idProduct;
    
    if (!handles[dev_num])
    {
        debug(DEBUG_ERROR, "os_usb_init: handle not set. Handle failed.");
        return -1;
    }

    /* Only interface the boards provide. */
    interface = usb_claim_interface(handles[dev_num], 0);

    if (interface < 0)
    {
    	debug(DEBUG_INFO, "os_usb_init: could not claim interface. Could not claim interface.");
      return -1;
    }

    return device->descriptor.idProduct;
}

int os_usb_close()
{
    debug(DEBUG_INFO, "os_usb_close called.");
    int number_of_devices = os_usb_count_devices(VENDOR_ID);
    int i;

    for (i = 0; i < number_of_devices; i++)
        if (handles[i]) {
            debug(DEBUG_INFO, "os_usb_close: closing device %d", i);
            if (usb_release_interface(handles[i], 0))
            	return -2;
            if (usb_close(handles[i]) < 0)
                return -1;
        }

    return 0;   
}

int os_usb_reset_pipes(int dev_num)
{
    debug(DEBUG_INFO, "os_usb_reset_pipes called");
		
    if (usb_clear_halt(handles[dev_num], EP1OUT) < 0)
        return -1;
    
    if (usb_clear_halt(handles[dev_num], EP2OUT) < 0)
        return -1;

    if (usb_clear_halt(handles[dev_num], EP6IN) < 0)
        return -1;

    return 0;
}

/**
 * Write data to the USB device
 * \param pipe endpoint to write data too
 * \param data buffer holding data to be written
 * \param size Size in bytes of the buffer
 * \returns 0 on success, or a negative number on failure
 */
int os_usb_write(int dev_num, int pipe, const void *data, int size)
{
    debug(DEBUG_INFO, "os_usb_write(dev_num = %d, pipe = 0x%X, data, size = %d)", dev_num, pipe, size);

    int bytes_written = usb_bulk_write(handles[dev_num], pipe, (char *)data, size, MAX_IO_WAIT_TIME);
    if (bytes_written < 0)
    {
        return -1;
    }
    debug(DEBUG_INFO, "number of bytes written: %d\n", bytes_written);
    
    return  0;
}

/**
 * Read data from the USB device.
 * \param pipe Endpoint to read data from
 * \param data Buffer to hold the data that will be read
 * \param size Size in bytes of data to read
 * \returns 0 on success, or a negative number on failure
 */
int os_usb_read(int dev_num, int pipe, void *data, int size)
{
    debug(DEBUG_INFO, "os_usb_read(dev_num = %d, pipe = 0x%X, data, size = %d)\n", dev_num, pipe, size);

    int bytes_read = usb_bulk_read(handles[dev_num], pipe, data, size, MAX_IO_WAIT_TIME);
    if (bytes_read < 0)
    {
        return -1;
    }
    debug(DEBUG_INFO, "number of bytes read: %d\n", bytes_read);

    return  0;
}
