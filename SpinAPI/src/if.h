#ifndef _IF_H
#define _IF_H

#include <stdint.h>

#define MEM_ADDRESS 8
#define MEM_DATA    12

#define EXT_ADDRESS 16
#define EXT_DATA    20

// Extended registers
#define REG_DDS_CONTROL          0x0001
#define REG_DDS_DATA             0x0002
#define REG_CONTROL              0x0003
#define REG_SAMPLE_NUM           0x0004
#define REG_DAC_CONTROL          0x0005
#define REG_ADC_CONTROL          0x0006
#define REG_CIC_CONTROL          0x0007
#define REG_FIR_COEF_DATA        0x0008
#define REG_FIR_COEF_ADDR        0x0009
#define REG_FIR_NUM_TAPS         0x000A
#define REG_FIR_CONTROL          0x000B
#define REG_EXPERIMENT_RUNNING   0x000C
#define REG_OVERFLOW_COUNT       0x000D
#define REG_OVERFLOW2_COUNT      0x000E
#define REG_SCAN_SEGMENTS        0x000F
#define REG_SCAN_COUNT           0x0010
#define REG_DDS_DATA2            0x0011
#define REG_PBRAM_ADDR           0x0012
#define REG_DATARAM_ADDR         0x0013
#define REG_PBCORE               0x0014
#define REG_SHAPE_CONTROL        0x0016
#define REG_CORE_SEL             0x0017
#define REG_CIC_CONTROL2         0x0018
#define REG_PULSE_PERIOD         0x0020
#define REG_PULSE_CLOCK_HIGH     0x0024
#define REG_PULSE_OFFSET         0x0028
#define REG_PULSE_SYNC		     0x002C

#define REG_FIRMWARE_ID          0x00FF

#define REG_FIRMWARE_ID_RPG      0x007C
#define REG_FIRMWARE_ID_PCIE     0x000F

#define FIR_RESET 0x00010000

// this is valid on the COEF_ADDR register
#define FIR_COEF_LOAD_EN 0x0400

// bits of the control register

#define REG 0
#define AUX 1

// Bit defs for DDS_CONTROL register
#define DDS_RUN          0x00000020
#define DDS_FREQ_WE      0x00000004
#define DDS_TX_PHASE_WE  0x00000002
#define DDS_RX_PHASE_WE  0x00000001
#define DDS_REF_PHASE_WE 0x00040000
#define DDS_WRITE_SEL    0x80000000

// Bit defs for DDS_SHAPE register
#define SHAPE_FREQ_WE (1 << 4)
#define SHAPE_DDSRAM_WRITE_SEL (1 << 5)
#define SHAPE_SHAPERAM_WRITE_SEL (1 << 6)
#define SHAPE_WRITE_ADDR_SEL (1 << 7)
#define SHAPE_AMP_WE (1 << 8)


#ifdef __cplusplus
extern "C"
{
#endif

int dds_freq_extreg (int cur_board, int addr, int freq_word, int freq_word2);
int dds_phase_extreg (int cur_board, int phase_bank, int addr,
		      int phase_word);
void dds_freq_rpg (int bdnum, int reg, double freq);
void dds_phase_rpg (int bdnum, int dev, int addr, double phase);
void cos_sin_phase_default_rpg(void);
void phase_set_rpg(unsigned int addr_addr, unsigned int data_addr, 
                   unsigned int offset, unsigned int width, double phase);
                   
int pb_inst_rpg (unsigned int freq, unsigned int cos_phase, unsigned int sin_phase, 
                 unsigned int tx_phase, char tx_en, char phase_reset,
                 char trigger_scan, char envelope_freq, int amp, unsigned int real_add_sub,
                 unsigned int imag_add_sub, unsigned int swap,
                 uint64_t flags, unsigned int data, char op, double delay_ns);


void reg_write (unsigned int address, unsigned int data);
unsigned int reg_read (unsigned int address);
int ram_write (unsigned int bank, unsigned int start_addr, unsigned int len, const char *data);

void reg_write_simple (unsigned int address, unsigned int data);
unsigned int reg_read_simple (unsigned int address);
//int ram_write_rpg


int num_bits (int num);

#ifdef __cplusplus
}
#endif


#endif /* #ifdef _IF_H */
