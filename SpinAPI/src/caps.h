#ifndef _CAPS_H
#define _CAPS_H

#define AMCC_DEVID      0x8852  //dev id for boards using amcc bridge chip
#define PBESR_PRO_DEVID 0x8875  //dev id for pci core
#define VENDID          0x10e8  //our vendor id  (AMCC)

#define DDS_PROG_OLDPB   0
#define DDS_PROG_EXTREG  1
#define DDS_PROG_RPG     2

typedef struct
{
  int did_init;	   /** nonzero if this board has been initialized */
	int is_pcie;
	int is_usb;      /** nonzero if this is a usb devices */
  int usb_method;  /** method 1 is the original method, method 2 is what the DDSII usb boards use along with future PB24 USB boards*/
  
  int use_amcc;  /** nonzero if this board uses an amcc bridge chip. 1 for "modern" amcc protocol. 2 for "old" protocol, used by PB02PC boards*/
  double clock;  /** the clock speed of this board (in GHz)*/

  double dds_clock_mult;  /** this times clock is the dds clock speed */
  double pb_clock_mult;   /** this times clock is the pulseblaster clock speed */

  int has_firmware_id;     /** nonzero if the firmware id register exists. if 1, it is at location 0xFF, if 2, it is at location 0x15, if 3, it is at location 0x7F */
  unsigned int firmware_id; /** */
  //bugfixes
  int has_FF_fix;/** PB Core "1FF" issue status (equal to 1 if the board has the fix) */

  // pulse program limits
  int num_instructions;      /** number of pulse instructions the design can hold **/
  int num_IMW_bytes;          /** number of bytes making up the internal memory word **/

  int status_oldstyle; /** ... **/

  // dds limits
  int dds_prog_method; /** either DDS_PROG_OLDPB -or- DDS_PROG_EXTREG */
  int num_phase0;   /** number of phase registers in bank 0 (tx)*/
  int num_phase1;   /** number of phase registers in bank 1 (rx)*/
  int num_phase2;   /** number of phase registers in bank 2 (ref)*/
  int num_freq0;    /** number of frequency registers */

  // RadioProcessor
  int is_radioprocessor; /** 1 if normal, 2 if RPG */
  int cic_max_stages;
  int cic_max_decim;
  int cic_max_shift;

  int fir_max_taps;
  int fir_max_decim;
  int fir_max_shift;
  int fir_coef_width;    /** width in bits of the fir coefficients */

  int num_points; /** number of complex points the board can hold */
  int supports_scan_segments;
  int supports_scan_count;

  int has_wraparound_problem;

  int supports_cyclops;
  int supports_dds_shape;
  int num_shape;   /** number of period registers for the dds shape */
  int num_amp;     /** number of amplitude registers that are available */

  int acquisition_disabled;   /** set to 1 if board does not allow data acquisition */
  int custom_design;   /** 0 => not a custom design
                           1 => Topsin(Israel) custom design (firmware 10-10)
                           2 => Progression Systems custom design (firmware 12-6)
                           3 =>  custom design (firmware 10-15) */

  int number_of_dds;
  unsigned int dds_list[4];

  unsigned int dds_nfreq[4];
  unsigned int dds_nphase[4];
  unsigned int dds_namp[4];
  
  // special RP (RPG)
  unsigned int status_reg;
  unsigned int fir_1;
  unsigned int fir_2;
  unsigned int cic_1;
  unsigned int cic_2;
  unsigned int acq_1;
  unsigned int acq_2;
  unsigned int misc_1;
  unsigned int phase_addr;
  unsigned int phase_data;
  unsigned int shape_addr;
  unsigned int shape_data;
  unsigned int memory_addr;
  unsigned int memory_data;
  unsigned int memory_offset;
  unsigned int sin_phase_width;
  unsigned int cos_phase_width;
  unsigned int phase_addr_cos_offset;
  unsigned int phase_addr_sin_offset;
  unsigned int freq_addr;
  unsigned int freq_data;
  unsigned int freq_rx_offset;
  unsigned int freq_tx_offset;
  unsigned int envelope_freq_offset;
  unsigned int tx_phase_width;
  unsigned int phase_addr_tx_offset;
  unsigned int amp_shape_width; // uses shape registers
  unsigned int amp_shape_offset;
  unsigned int envelope_shape_offset;
  unsigned int envelope_shape_width;
  unsigned int carrier_shape_offset;
  unsigned int carrier_shape_width;
  unsigned int imw_base_addr;
  unsigned int imw_base_data_addr;
  double adc_clock_MHz;
  double dac_clock_int_MHz;
  float default_shape_period;
  
  unsigned int reg_scan_count;
  unsigned int pb_base_address;

  unsigned int prog_clock_base_address; /** base address for a programmable clock, used with SP9 boards */
  unsigned int dds_address[4];

  unsigned int pb_core_version;
} BOARD_INFO;


#ifdef __cplusplus
extern "C"
{
#endif

int get_caps (BOARD_INFO * board, int dev_id);

#ifdef __cplusplus
}
#endif

#endif /* #define _CAPS_H */
