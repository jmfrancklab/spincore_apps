#pragma once
#ifndef __IO_H__
#define __IO_H__

#define IO_FUTURE_WAIT_TIMEOUT 0
#define IO_FUTURE_WAIT_COMPLETE 1
#define IO_FUTURE_WAIT_ERROR -1

/**
 * Represents an IO request that is guaranteed to be filled at
 * some point in the future.
 */

struct io_future_t 
{
	HANDLE handle; /*< Device subsystem handle*/

	void *buffer; /*< Pointer to user-allocated buffer for the IO*/
	unsigned int sz_buffer; /*< Size of the buffer*/
	unsigned int wait_ms; /*< Maximum time to wait, in ms, before abandoning the IO request*/

	void *reserved;
};

/** 
 * Initialize io_future_t structure.
 * @param future io_future_t structure to initialize.
 * @return Returns 0 on success.
 */
int io_future_init(struct io_future_t *future);

/**
 * Reset an io_future structure status inbetween uses
 * @param future io_future_t structure to reset the status of.
 * @return Returns 0 on success.
 */
int io_future_reset(struct io_future_t *future);

/** 
 * Wait for an io_future structure to complete, or error. This function WILL block
 * until the request completes or timer expires.
 * @param future io_future structure to wait for completion
 * @return Returns 0 on success.
 */
int io_future_wait(struct io_future_t *future);

/**
 * Check the status of the IO request.
 * @param future io_future_t structure to check the status of.
 * @return 1 - IO completed
           0 - IO pending
		  -1 - Error
 */
int io_future_status(struct io_future_t *future);

/**
 * Free an allocated io_future_t structure.
 * @param future Structure to free resources from
 * @return Returns 0 on success.
 */
int io_future_free(struct io_future_t *future);

int io_future_cancel(struct io_future_t *future) ;

#endif /*__IO_H__*/