#ifndef __DDS_H__
#define __DDS_H__

#ifndef SPINCORE_API
#define SPINCORE_API
#endif

#ifdef PBDDS
#define pb_inst pb_inst_tworf
#define PHASE_RESET 0x200
#endif

#ifdef __cplusplus
extern "C"
{
#endif

/**
 * Write the given frequency to a frequency register on a DDS enabled board. To do this, first call
 * pb_start_programming(), and pass it FREQ_REGS. The first call pb_set_freq() will then program
 * frequency register 0, the second call will program frequency register 1, etc.
 * When you have programmed all the registers you intend to, call pb_stop_programming()
 *
 * \param freq The frequency in MHz to be programmed to the register.
 * \return A negative number is returned on failure. 0 is returned on success.
 *
 */
SPINCORE_API int pb_set_freq (double freq);
/**
 * Write the given phase to a phase register on DDS enabled boards. To do this, first call
 * pb_start_programming(), and specify the appropriate bank of phase
 * registers (such as TX_PHASE, RX_PHASE, etc) as the argument. The first call pb_set_phase() will then program
 * phase register 0, the second call will program phase register 1, etc.
 * When you have programmed all the registers you intend to, call pb_stop_programming()
 * <br>
 * The given phase value may be rounded to fit the precision of the board.
 *
 * \param phase The phase in degrees to be programmed to the register.
 * \return A negative number is returned on failure. 0 is returned on success.
 *
 */
 
SPINCORE_API int pb_set_phase (double phase);
/**
 * Program an instruction of a pulse program to the board. This function
 * programs instructions for boards with 2 DDS outputs. (such as PulseBlasterDDS-III)
 * There are other forms
 * of this instruction (see below) design to program boards with differing
 * instruction formats.<br>
 * 
 * Instructions can also be programmed by calling pb_inst(), but you must
 * use an appropriate #define before including spinapi.h. See the example programs
 * for how to do this.
 *
 * \param freq The frequency register to use for this instruction
 * \param tx_phase The TX phase register to use for this instruction
 * \param tx_output_enable Set to ANALOG_ON to enable output, or ANALOG_OFF to output nothing
 * \param rx_phase The RX phase register to use for this instruction
 * \param rx_output_enable Set to ANALOG_ON to enable output, or ANALOG_OFF to output nothing
 * \param flags Set every bit to one for each flag you want to set high
 *
 * \param inst Specify the instruction you want. Valid instructions are:
 *<table border="0">
 *<tr><td>Opcode #</td><td>Instruction</td><td>Meaning of inst_data field</td></tr>
 *<tr><td>0</td><td>CONTINUE</td><td>Not Used</td></tr>
 *<tr><td>1</td><td>STOP</td><td>Not Used</td></tr>
 *<tr><td>2</td><td>LOOP</td><td>Number of desired loops</td></tr>
 *<tr><td>3</td><td>END_LOOP</td><td>Address of instruction originating loop</td></tr>
 *<tr><td>4</td><td>JSR</td><td>Address of first instruction in subroutine</td></tr>
 *<tr><td>5</td><td>RTS</td><td>Not Used</td></tr>
 *<tr><td>6</td><td>BRANCH</td><td>Address of instruction to branch to</td></tr>
 *<tr><td>7</td><td>LONG_DELAY</td><td>Number of desired repetitions</td></tr>
 *<tr><td>8</td><td>WAIT</td><td>Not Used</td></tr>
 *</table>
 * See your board manual for a detailed description of each instruction.
 *
 *
 * \param inst_data Instruction specific data. Internally this is a 20 bit unsigned number, so the largest value that can be passed is 2^20-1 (the largest value possible for a 20 bit number). See above table to find out what this means for each instruction.
 * \param length Length of this instruction in nanoseconds.
 * \return The address of the created instruction is returned. This can be used
 * as the branch address for any branch instructions.
 */
SPINCORE_API int pb_inst_tworf (int freq, int tx_phase,
				  int tx_output_enable, int rx_phase,
				  int rx_output_enable, int flags, int inst,
				  int inst_data, double length);

/**
 * This is the instruction programming function for boards with only one DDS
 * output channel. 
 * Syntax is identical to that of
 * pb_inst_tworf(), but the second RF channel is not used.
 */
SPINCORE_API int pb_inst_onerf (int freq, int phase, int rf_output_enable,
				                int flags, int inst, int inst_data,
				                double length);

//DDS related functions
/**
 * Write an instruction to the memory of a PBDDS-II.
 * \param freq0 Frequency register to control the first channel for the duration of this instruction.
 * \param phase0 Phase register for the first channel.
 * \param amp0 Amplitude register for the first channel.
 * \param dds_en0 Set this parameter to TX_ENABLE to enable analog output on the first channel. A value of
 * TX_DISABLE will turn off the output.
 * \param phase_reset0 Set this parameter to PHASE_RESET in order to synchronize the phase of the output on
 * the first channel. Setting this parameter to NO_PHASE_RESET will not enable this feature.
 * \param freq1 Frequency register to control the second channel for the duration of this instruction.
 * \param phase1 Phase register for the second channel.
 * \param amp1 Amplitude register for the second channel.
 * \param dds_en1 Set this parameter to TX_ENABLE to enable analog output on the second channel. A value of
 * TX_DISABLE will turn off the output.
 * \param phase_reset1 Set this parameter to PHASE_RESET in order to synchronize the phase of the output on
 * the second channel. Setting this parameter to NO_PHASE_RESET will not enable this feature.
 * \param flags The state of the TTL output signals.
 * \param inst A flow control command.
 * \param inst_data Extra data to be associated with the flow control command.
 * \param length The duration of the instruction. Remember to specify time units.
 */
  SPINCORE_API int pb_inst_dds2 (int freq0, int phase0, int amp0, int dds_en0,
				 int phase_reset0, int freq1, int phase1,
				 int amp1, int dds_en1, int phase_reset1,
				 int flags, int inst, int inst_data,
				 double length);
/**
 * Write an instruction that makes use of the pulse shape feature of the PBDDS-II-300 AWG boards. This adds two new parameters, use_shape0 and use_shape1, which control the shape features of the two DDS output channels. All other parameters are identical to the pb_inst_dds2() function. If you do not wish to use the shape feature, the pb_inst_dds2() function can be used instead.
 * \param use_shape0 Select whether or not to use shaped pulses for the first DDS-II channel. If this is 0, a regular non-shaped pulse (hard pulse) is output. If it is nonzero, the shaped pulse is used. The pulse shape waveform can be set using the pb_dds_load() function.
 * \param use_shape1 Select whether or not to use shaped pulses for the second DDS-II channel. If this is 0, a regular non-shaped pulse (hard pulse) is output. If it is nonzero, the shaped pulse is used. The pulse shape waveform can be set using the pb_dds_load() function.
 *\return A negative number is returned on failure. The address of the programmed instruction is returned upon success.
 */
SPINCORE_API int pb_inst_dds2_shape (int freq0, int phase0, int amp0, int use_shape0,
				 int dds_en0, int phase_reset0, int freq1, int phase1, int amp1, 
				 int use_shape1, int dds_en1, int phase_reset1, int flags, int inst, 
				 int inst_data, double length);
/**
 * This function initializes the shape parameters in order to use the AWG 
 * capabilities of the PBDDS-II-300 AWG design. This function is intended 
 * for use with PBDDS-II-300 AWG designs only. 
 *
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_set_shape_defaults(void);

SPINCORE_API int pb_select_dds (int dds_num);
/**
 * Load the DDS with the given waveform. There are two different waveforms that can be
 * loaded. Note that for PBDDS-II-300 AWG boards, this function should be used only after using 
 * pb_select_dds() to select which DDS channel (0 or 1) that you wish to program.
 * <ul>
 * <li>DEVICE_DDS - This is for the DDS module itself. By default, it is loaded with a sine wave,
 * and if you don't wish to change that or use shaped pulses, you do not need to use this function.
 * Otherwise this waveform can be loaded with any arbitrary waveform that will be used instead of a sine
 * wave.
 * <li>DEVICE_SHAPE - This waveform is for the shape function. This controls the shape used,
 * if you enable the use_shape parameters of pb_inst_radio_shape() or pb_inst_dds2_shape(). For example, 
 * if you wish to use soft pulses, this could be loaded with the values for the sinc function.
 * </ul>
 * \param data This should be an array of 1024 floats that represent a single period of the waveform
 * you want to have loaded. The range for each data point is from -1.0 to 1.0 
 * \param device Device you wish to program the waveform to. Can be DEVICE_SHAPE or DEVICE_DDS
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_dds_load (const float *data, int device);

/**
 * Load an envelope frequency register.
 * \param freq The frequency in MHz for the envelope register.
 * \param n Which frequency register to program
 */
SPINCORE_API void pb_dds_set_envelope_freq(float freq, int n);

/**
 * Set the value of one of the amplitude registers.
 * \param amp Amplitude value. 0.0-1.0
 * \param addr Address of register to write to
 * 
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_set_amp (float amp, int addr);

#define pb_inst_dds(FREQ, TX_PHASE, TX_ENABLE, PHASE_RESET, FLAGS, INST, INST_DATA, LENGTH) \
		pb_inst_radio(FREQ, 0, 0, TX_PHASE, TX_ENABLE, PHASE_RESET, 0, FLAGS, INST, INST_DATA, LENGTH);

#define pb_inst_dds_shape(FREQ, TX_PHASE, TX_ENABLE, PHASE_RESET, USESHAPE, AMP, FLAGS, INST, INST_DATA, LENGTH) \
		 pb_inst_radio_shape(FREQ, 0, 0, TX_PHASE, TX_ENABLE, PHASE_RESET, 0, USESHAPE, AMP, FLAGS, INST, INST_DATA, LENGTH);
		 

#ifdef __cplusplus
}
#endif

#endif /*__DDS_H__*/
