#ifndef __RADIOPROCESSOR_H__
#define __RADIOPROCESSOR_H__

#ifndef SPINCORE_API
#define SPINCORE_API
#endif

//Defines for start_programming

#define FREQ_REGS      1

#define PHASE_REGS     2
#define TX_PHASE_REGS  2
#define PHASE_REGS_1   2

#define RX_PHASE_REGS  3
#define PHASE_REGS_0   3

// These are names used by RadioProcessor
#define COS_PHASE_REGS 51
#define SIN_PHASE_REGS 50

// For specifying which device in pb_dds_load
#define DEVICE_SHAPE 0x099000
#define DEVICE_DDS   0x099001

//Defines for enabling analog output
#define ANALOG_ON 1
#define ANALOG_OFF 0
#define TX_ANALOG_ON 1
#define TX_ANALOG_OFF 0
#define RX_ANALOG_ON 1
#define RX_ANALOG_OFF 0

//Defines for using different units of frequency
#define MHz 1.0
#define kHz .001
#define Hz .000001

//Defines for status bits

#define STATUS_SCANNING 16

/// \brief Overflow counter structure
///
/// This structure holds the values of the various onboard overflow counters. These counters
/// stop counting once they reach 65535.
typedef struct
{
  /// Number of overflows that occur when sampling data at the ADC
  int adc;
  /// Number of overflows that occur after the CIC filter
  int cic;
  /// Number of overflows that occur after the FIR filter
  int fir;
  /// Number of overflows that occur during the averaging process
  int average;
} PB_OVERFLOW_STRUCT;


#ifdef __cplusplus
extern "C"
{
#endif


// RadioProcessor related functions
/**
 * This function sets the RadioProcessor to its default state. It has no effect
 * on any other SpinCore product. This function should generally be called after pb_init()
 * to make sure the RadioProcessor is in a usable state. It is REQUIRED that this
 * be called at least once after the board is powered on. However, there are a few
 * circumstances when you would not call this function. In the case where you had
 * one program that configured the RadioProcessor, and another separate program
 * which simply called pb_start() to start the experiment, you would NOT call
 * pb_set_defaults() in the second program because this would overwrite the
 * configuration set by the first program.
 *
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_set_defaults (void);
/**
 * Program an instruction of the pulse program. 
 *
 *\param freq Selects which frequency register to use
 *\param cos_phase Selects which phase register to use for the cos (real) channel
 *\param sin_phase Selects which phase register to use for the sin (imaginary) channel
 *\param tx_phase Selects which phase register to use for the TX channel
 *\param tx_enable When this is 1, the TX channel will be output on the Analog
 * Out connector. When this is 0, Analog Out channel will be turned off.
 *\param phase_reset When this is 1, the phase of all DDS channels will be reset
 * to their time=0 phase. They will stay in this state until the value of this
 * bit returns to 0.
 *\param trigger_scan When this is 1, a scan will be triggered. To start a second
 * scan, this bit must be set to 0 and then back to 1.
 *\param flags Controls the state of the user available digital out pins. Since
 * there are 6 user outputs, only the lower 6 bits of this parameter are used.
 * Bits 1 and 0 control BNC1 and BNC0 respectively.
 *\param inst Which instruction to use. See manual for details.
 *\param inst_data Some instructions require additional data. This allows that data
 * to be specified. See manual for details.
 *\param length Time until the next instruction is executed in nanoseconds
 */
SPINCORE_API int pb_inst_radio (int freq, int cos_phase, int sin_phase,
				  int tx_phase, int tx_enable,
				  int phase_reset, int trigger_scan,
				  int flags, int inst, int inst_data,
				  double length);
/**
 * Write an instruction that makes use of the pulse shape feature of some RadioProcessor boards. This adds two new paramters, use_shape and amp, which control the shape feature. All other parameters are identical to the pb_inst_radio() function. If you do not wish to use the shape feature, the pb_inst_radio() function can be used instead.
 * \param use_shape Select whether or not to use shaped pulses. If this is 0, a regular non-shaped pulse (hard pulse) is output. If it is nonzero, the shaped pulse is used. The pulse shape waveform can be set using the pb_dds_load() function.
 * \param amp Select which amplitude register to use. The values of the amplitude registers can be set with pb_set_amp()
 */
SPINCORE_API int pb_inst_radio_shape (int freq, int cos_phase,
					int sin_phase, int tx_phase,
					int tx_enable, int phase_reset,
					int trigger_scan, int use_shape,
					int amp, int flags, int inst,
					int inst_data, double length);
/**
 * Write an instruction that makes use of the pulse shape feature of some RadioProcessor boards. This adds two new paramters, use_shape and amp, which control the shape feature. All other parameters are identical to the pb_inst_radio() function. If you do not wish to use the shape feature, the pb_inst_radio() function can be used instead.
 * \param use_shape Select whether or not to use shaped pulses. If this is 0, a regular non-shaped pulse (hard pulse) is output. If it is nonzero, the shaped pulse is used. The pulse shape waveform can be set using the pb_dds_load() function.
 * \param amp Select which amplitude register to use. The values of the amplitude registers can be set with pb_set_amp()
 */
SPINCORE_API int pb_inst_radio_shape_cyclops (int freq, int cos_phase,
					int sin_phase, int tx_phase, int tx_enable, 
					int phase_reset, int trigger_scan, int use_shape,
					int amp, int real_add_sub, int imag_add_sub,
					int channel_swap, int flags, int inst,
					int inst_data, double length);
/**
 * Set the number of complex points to capture. This is typically set to
 * the size of the onboard RAM, but a smaller value can be used if all
 * points are not needed.
 *
 *\param num_points The number of complex points to capture
 *
 *\return A negative number is returned on failure. 0 is returned on success.
 *
 */
SPINCORE_API int pb_set_num_points (int num_points);
/**
 * Set the number of data "segments" to be acquired. The default value is 1,
 * meaning when data is acquired, it will be stored to the RAM starting
 * at address zero, and continue until the desired number of points are
 * acquired. Any subsequent data acquisition scans will behave in the same
 * way and thus overwrite (or average with) the previous data. If num_segments
 * is set to a value higher than 1, the given number of segments will be acquired
 * before resetting the ram address to 0. For example if num_points is set to
 * 1000, and num_segments is set to 3, the first time the acquisition is triggered
 * (using scan_trigger), data will be written to RAM locations 0-999. The
 * second time it is triggered, data will be written to locations 1000-1999
 * (instead of writing again to locations 0-999 as would be the case for
 * num_segments = 1). On the third trigger data will go to locations 2000-2999.
 * Finally a fourth trigger would again write to locations 0-999, and the cycle
 * will continue as desired.
 *
 * <p>
 * When this function is called, the internal segment counter is reset to
 * segment 0.
 * </p>
 *
 *\param num_segments Number of segments to acquire. Must be between 1 and 65535.
 *
 *\return A negative number is returned on failure. 0 is returned on success.
 *
 */
SPINCORE_API int pb_set_scan_segments (int num_segments);
/**
 * Get the current value of the scan count register, or reset the register to 0. This
 * function can be used to monitor the progress of an experiment if multiple
 * scans are being performed.
 *
 * \param reset If this parameter is set to 1, this function will reset the 
 * scan counter to 0. If reset is 0, this function will return the current value of the scan counter.
 * \return The number of scans performed since the last reset is returned when reset=0. -1 is returned on error
 */
SPINCORE_API int pb_scan_count (int reset);
/**
 * Retrieve the contents of the overflow registers. This can be used to find out if
 * the ADC is being driven with to large of a signal. In addition, the RadioProcessor must
 * round data values at certain points during the processing of the signal. By
 * default, this rounding is done in such a way that overflows cannot occur. However,
 * if you change the rounding procedure, this function will allow you to determine
 * if overflows have occurred. Each overflow register counts the number of overflows
 * up to 65535. If more overflows than this occur, the register will remain at 65535.
 * The overflow registers can reset by setting the reset argument of this function to 1.
 * <br><br>
 * See your manual for a detailed explanation of how the on-board rounding works.
 *
 *\param reset Set this to one to reset the overflow counters
 *\param of Pointer to a PB_OVERFLOW_STRUCT which will hold the values
 * of the overflow counter. This can be a NULL pointer if you are using
 * this function to reset the counters
 *
 *\return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_overflow (int reset, PB_OVERFLOW_STRUCT * of);
/**
 * Retrieve the captured data from the board's memory. Data is returned as a
 * signed 32 bit integer. Data can be accessed at any time, even while the data
 * from a scan is being captured. However, this is not recommended since there
 * is no way to tell what data is part of the current scan and what is part
 * of the previous scan.<br>
 * No post processing of the data is done; it is read directly from memory into
 * the output arrays.<br>
 * pb_read_status() can be used to determine whether or not a scan is currently
 * in progress.<br>
 * It takes approximately 160ms to transfer all 16k complex points.
 *
 *\param num_points Number of complex points to read from RAM
 *\param real_data Real data from RAM is stored into this array
 *\param imag_data Imag data from RAM is stored into this array
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_get_data (int num_points, int *real_data,
				int *imag_data);
SPINCORE_API int pb_get_data_direct(int num_points, short *data);

  SPINCORE_API int pb_write_ascii (const char *fname, int num_points, float SW,
				   const int *real_data, const int *imag_data);
/**
 * Write the data captured from RAM to an ascii file. The file format produced is:
 * The first three lines are comments containing information about the RadioProcessor and SpinAPI.
 * The fourth line contains the number of complex points, the fifth line
 * contains the spectrometer frequency (in MHz), the sixth line contains the spectral width 
 * of the data (in Hz), and the remaining lines
 * contain the complex points themselves. Real and Imaginary components of the
 * complex points are given on alternate lines. Thus, the real and imaginary
 * components of the first point are given on lines 7 and 8 respectively. The
 * second point is given on lines9 and 10, etc.
 *
 *\param fname Filename to write the data to
 *\param num_points Number of complex data points to write
 *\param SW Spectral width in Hz. This should be set to the spectral width of the stored baseband data.
  *\param SF Spectrometer frequency in MHz
 *\param real_data Array holding the real portion of the complex data points
 *\param imag_data Array holding the imaginary portion of the complex data points
 *\return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_write_ascii_verbose (const char *fname, int num_points,
					   float SW, float SF, const int *real_data,
					   const int *imag_data);
/**
 * Write the RAM contents to a JCAMP-DX file. 
 *\param fname The filename for the file you want to create
 *\param num_points Number of points to write to the file
 *\param SW Spectral width of the baseband data in Hz
 *\param SF Spectrometer frequency in MHz
 *\param real_data Integer array containing the real portion of the data points
 *\param imag_data Integer array containing the imaginary portion of the data points
 *\return A negative number is returned on failure. 0 is returned on success.
 */
/**
 * Write the RAM contents to a JCAMP-DX file. 
 *\param fname The filename for the file you want to create
 *\param num_points Number of points to write to the file
 *\param SW Spectral width of the baseband data in Hz
 *\param SF Spectrometer frequency in MHz
 *\param real_data Integer array containing the real portion of the data points
 *\param imag_data Integer array containing the imaginary portion of the data points
 *\return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_write_jcamp (const char *fname, int num_points, float SW,
				   float SF, const int *real_data, const int *imag_data);
/**
 * Write the RAM contents to a Felix file. 
 *\param fnameout The filename for the Felix file you want to create
 *\param title_string Large string with all parameter information to include in Felix Title Block
 *\param num_points Number of points to write to the file
 *\param SW Spectral width of the baseband data in Hz
 *\param SF Spectrometer frequency in MHz
 *\param real_data Integer array containing the real portion of the data points
 *\param imag_data Integer array containing the imaginary portion of the data points
 *\return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_write_felix (const char *fnameout, const char *title_string, int num_points, float SW, float SF, 
                const int *real_data, const int *imag_data);
/**
 * Program the onboard filters to capture data and reduce it to a baseband
 * signal with the given spectral width.
 * This function will automatically set the filter parameters and decimation
 * factors. For greater control over the filtering process, the filters can
 * be specified manually by using the pb_setup_cic() and pb_setup_fir() functions.
 *
 *\param spectral_width Desired spectral width (in MHz) of the stored baseband data. The decimation factor used is the return
 * value of this function, so that can be checked to determine the exact
 * spectral width used. If the FIR filter is used, this value must be the ADC clock divided by a multiple of 8. The value will be rounded appropriately if this condition is not met.
 *
 *\param scan_repetitions Number of scans intended to be performed. This number
 * is used only for internal rounding purposes. The actual number of scans performed
 * is determined entirely by how many times the scan_trigger control line is enabled
 * in the pulse program. However, if more scans are performed than specified here,
 * there is a chance that the values stored in RAM will overflow.
 *
 *\param cmd This parameter provides additional options for this function. 
 * Multiple options can be sent by ORing them together. If you do not wish to invoke any of the available options, use the number zero for this field. Valid options are:<ul>
 * <li>BYPASS_FIR - Incoming data will not pass through the FIR filter. This
 * eliminates the need to decimate by a multiple of 8. This is useful to obtain
 * large spectral widths, or in circumstances where the FIR is deemed unnecessary.
 * Please see the RadioProcessor manual for more information about this option.
 * <li>NARROW_BW - Configure the CIC filter so that it will have a narrower bandwidth (the CIC filter will be configured to have three stages rather than the default of one).  Please see your board's product manual for more specific information on this feature.
 * </ul>
 *
 *
 *\return A negative number is returned on failure. The overall decimation factor used is returned
 *on success.
 */
SPINCORE_API int pb_setup_filters (double spectral_width,
				     int scan_repetitions, int cmd);
/**
 * Set the parameters on the onboard CIC filter. If
 * the pb_setup_filters() function is used, filter specification is done
 * automatically and this function is not necessary.
 *
 *\param dec_amount The amount of decimation the filter should perform. This can
 * be between 8 and 65535
 *\param shift_amount Amount to shift the output of the CIC filter to the right
 *\param m M parameter (differential delay) for the CIC filter. This can be 1 or 2.
 *\param stages Number of stages of the filter (1, 2, or 3)
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_setup_cic (int dec_amount, int shift_amount, int m,
				 int stages);
/**
 * Load the coefficients for the FIR filter. This function will read floating point
 * values, one on each line, into the coef array. The coefficients will be scaled
 * appropriately to make use of the entire word coefficient word size. The coefficients
 * MUST be even symmetric.<br><br>
 * This function also calculates the worst case gain of
 * the filter. Thus the absolute largest value needed to represent the output of
 * the filter is the input word with + the worst case gain.
 * <br><br>
 * This function only fills the coef array with the coefficients given in
 * the file. To actually set these values to the board, use the pb_setup_fir()
 * function.
 * 
 *
 *\param coef Integer array that will hold the coefficients. This should have
 * enough space allocated to fit num_taps coefficients
 *\param fname The filename to open
 *\param num_coefs Number of coefficients in filter.
 *\return A negative number is returned on failure. The worst case bit growth 
 for the filter is returned
 * on success.
 */
SPINCORE_API int pb_load_coef_file (int *coef, const char *fname, int num_coefs);
/**
 * Set the parameters on the onboard FIR filter. If
 * the pb_setup_filters() function is used, filter specification is done
 * automatically and this function is not necessary.
 *
 *\param num_coefs Number of coefficients in the filter.
 *\param coef Array containing the coefficients of the filter. This array can be generated
 * from data stored in a file with the pb_load_coef_file() function. The coefficients must be even symmetric.
 *\param shift_amount Amount to shift the output of the CIC filter to the right.
 *\param dec_amount Specify by what amount the output of the FIR filter should be
 * decimated. This can be between 1 (no decimation) and 255. Take care not
 * to decimate the signal so that the resulting bandwidth is smaller than the 
 * FIR cutoff frequency, or unwanted aliasing may occur.
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_setup_fir (int num_taps, const int *coef, int shift_amount,
				 int dec_amount);
/**
 * The RadioProcessor contains internal registers which can be used to modify
 * the way the board works. These settings are mainly for debugging purposes
 * and not generally used during normal operation.
 * Valid bits that can be set are:
 *
 * BYPASS_MULT<br>
 * BYPASS_CIC<br>
 * BYPASS_FIR<br>
 * SELECT_AUX_DDS<br>
 * SELECT_INTERNAL_DDS<br>
 * DAC_FEEDTHROUGH<br>
 * BNC0_CLK (for boards that have selectable clock output on BNC0)<br>
 * FORCE_AVG (for boards that support averaging across separate scan calls) <br>
 *
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_set_radio_control (unsigned int control);
/**
 * This function unsets bits from the control register.  Valid bits are the same ones
*  listed under pb_set_radio_control(unsigned int control).
 *
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_unset_radio_control (unsigned int control);
/*
 * The onboard ADC and DAC units have several control bits which can be used
 * to control their performance characteristics. For now, users should ignore
 * this function and use the default settings. Full documentation for this
 * function will be provided soon.
 * \param adc_control
 * \param dac_control
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_set_radio_hw (int adc_control, int dac_control);

SPINCORE_API int pb_set_isr (int irq_num, unsigned int isr_addr);
SPINCORE_API int pb_set_irq_enable_mask (char mask);
SPINCORE_API int pb_set_irq_immediate_mask (char mask);
SPINCORE_API int pb_generate_interrupt (char mask);
SPINCORE_API int pb_write_register (unsigned int address, unsigned int value);
/**
 * Deprecated function. Included only to avoid breaking old code.
 *
 * \return Always returns 0
 */
SPINCORE_API int pb_zero_ram(void);


SPINCORE_API int pb_adc_zero(int set);

/**
 * Applies an offset to the input from the ADC for DC correction. 
 *
 *\param set If set is 1, then the DC offset is applied. If zero, offset correction  is cleared.
 *           For certain boards, is the amount of DC offset.
 *
 *\return The offset set by the DC offset correction unit.
 *
 */
SPINCORE_API int pb_adc_zero(int set);

//Signal processing functions
/**
 * Calculates the Fourier transform of a given set of real and imaginary points
 *
 *\param n Number of points for FFT.
 *\param real_in Array of real points for FFT calculation
 *\param imag_in Array of imaginary points for FFT calculation
 *\param real_out Real part of FFT output
 *\param imag_out Imaginary part of FFT output
 *\param mag_fft Magnitude of the FFT output
 *
 *\return Returns zero.
 *
 */
SPINCORE_API int pb_fft (int n, const int *real_in, const int *imag_in, double *real_out,
			   double *imag_out, double *mag_fft);
				 
/**
 * Calculates the resonance frequency of a given set of real and imaginary points
 * based on the maximum value of the magnitude of the Fourier transform. 
 *
 *\param num_points Number of complex data points.
 *\param SF Spectrometer Frequency used for the experiment (in Hz).
 *\param SW Spectral Width used for data acquisition (in Hz).
 *\param real Array of the real part of the complex data points.
 *\param imag Array of the imaginary part of the complex data points.
 *
 *\return Returns the resonance frequency (in Hz).
 *
 */
SPINCORE_API double pb_fft_find_resonance (int num_points, double SF, 
               double SW, const int *real, const int *imag);

//RadioProcessor control word defines
#define TRIGGER             0x0001
#define PCI_READ            0x0002
#define BYPASS_AVERAGE      0x0004
#define NARROW_BW           0x0008
#define FORCE_AVG			      0x0010
#define BNC0_CLK            0x0020
#define DO_ZERO             0x0040
#define BYPASS_CIC          0x0080
#define BYPASS_FIR          0x0100
#define BYPASS_MULT         0x0200
#define SELECT_AUX_DDS      0x0400
#define DDS_DIRECT          0x0800
#define SELECT_INTERNAL_DDS 0x1000
#define DAC_FEEDTHROUGH     0x2000
#define OVERFLOW_RESET      0x4000
#define RAM_DIRECT          0x8000|BYPASS_CIC|BYPASS_FIR|BYPASS_MULT

#define pb_get_wait_time(ADCFREQ, NPOINTS, DEC) 1000.0*((double)DEC)*((double)NPOINTS)/(((double)ADCFREQ)*1e6)

#ifdef __cplusplus
}
#endif


#endif /*__PULSEBLASTER_H__*/
