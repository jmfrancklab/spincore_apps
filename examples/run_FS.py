# {{{ note on phase cycling
"""
FOR PHASE CYCLING: Provide both a phase cycle label (e.g.,
'ph1', 'ph2') as str and an array containing the indices
(i.e., registers) of the phases you which to use that are
specified in the numpy array 'tx_phases'.  Note that
specifying the same phase cycle label will loop the
corresponding phase steps together, regardless of whether
the indices are the same or not.
    e.g.,
    The following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph1',r_[2,3]),
    will provide two transients with phases of the two pulses (p1,p2):
        (0,2)
        (1,3)
    whereas the following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph2',r_[2,3]),
    will provide four transients with phases of the two pulses (p1,p2):
        (0,2)
        (0,3)
        (1,2)
        (1,3)
FURTHER: The total number of transients that will be
collected are determined by both nScans (determined when
calling the appropriate marker) and the number of steps
calculated in the phase cycle as shown above.  Thus for
nScans = 1, the SpinCore will trigger 2 times in the first
case and 4 times in the second case.  for nScans = 2, the
SpinCore will trigger 4 times in the first case and 8 times
in the second case.
"""
# }}}
from pyspecdata import *
from numpy import *
from . import SpinCore_pp
import socket
import sys
import time

# {{{ for setting EPR magnet
def API_sender(value):
    IP = "jmfrancklab-bruker.syr.edu"
    if len(sys.argv) > 1:
        IP = sys.argv[1]
    PORT = 6001
    print("target IP:", IP)
    print("target port:", PORT)
    MESSAGE = str(value)
    print("SETTING FIELD TO...", MESSAGE)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Internet  # TCP
    sock.connect((IP, PORT))
    sock.send(MESSAGE)
    sock.close()
    print("FIELD SET TO...", MESSAGE)
    time.sleep(3)
    return


# }}}

field_axis = linspace(3490.0, 3510.0, 5, endpoint=False)
fl = figlist_var()
date = "190614"
output_name = "FS_1"
adcOffset = 34
carrierFreq_MHz = 14.894439
tx_phases = r_[0.0, 90.0, 180.0, 270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
p90 = 4.0
deadtime = 200.0
repetition = 4e6
SW_kHz = 500.0
nPoints = 2048
acq_time = nPoints / SW_kHz  # ms
tau_adjust = 0.0
tau = deadtime + acq_time * 1e3 * 0.5 + tau_adjust
print("ACQUISITION TIME:", acq_time, "ms")
print("TAU DELAY:", tau, "us")
data_length = 2 * nPoints * nEchoes * nPhaseSteps
for index, val in enumerate(field_axis):
    print("***")
    print("INDEX NO.", index)
    print("***")
    API_sender(val)
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    acq_time = SpinCore_pp.configureRX(
        SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps
    )  # ms
    print("ACQUISITION TIME IS", acq_time, "ms")
    SpinCore_pp.init_ppg()
    if phase_cycling:
        SpinCore_pp.load(
            [
                ("marker", "start", 1),
                ("phase_reset", 1),
                ("delay_TTL", 1.0),
                ("pulse_TTL", p90, "ph1", r_[0, 1, 2, 3]),
                ("delay", tau),
                ("delay_TTL", 1.0),
                ("pulse_TTL", 2.0 * p90, "ph2", r_[0, 2]),
                ("delay", deadtime),
                ("acquire", acq_time),
                ("delay", repetition),
                ("jumpto", "start"),
            ]
        )
    if not phase_cycling:
        SpinCore_pp.load(
            [
                ("marker", "start", nScans),
                ("phase_reset", 1),
                ("delay_TTL", 1.0),
                ("pulse_TTL", p90, 0.0),
                ("delay", tau),
                ("delay_TTL", 1.0),
                ("pulse_TTL", 2.0 * p90, 0.0),
                ("delay", deadtime),
                ("acquire", acq_time),
                ("delay", repetition),
                ("jumpto", "start"),
            ]
        )
    SpinCore_pp.stop_ppg()
    if phase_cycling:
        for x in range(nScans):
            print("SCAN NO. %d" % (x + 1))
            SpinCore_pp.runBoard()
    if not phase_cycling:
        SpinCore_pp.runBoard()
    raw_data = SpinCore_pp.getData(
        data_length, nPoints, nEchoes, nPhaseSteps, output_name
    )
    raw_data.astype(float)
    data = []
    # according to JF, this commented out line
    # should work same as line below and be more effic
    # data = raw_data.view(complex128)
    data[::] = complex128(raw_data[0::2] + 1j * raw_data[1::2])
    print("COMPLEX DATA ARRAY LENGTH:", shape(data)[0])
    print("RAW DATA ARRAY LENGTH:", shape(raw_data)[0])
    dataPoints = float(shape(data)[0])
    time_axis = linspace(0.0, nEchoes * nPhaseSteps * acq_time * 1e-3, dataPoints)
    data = nddata(array(data), "t")
    data.setaxis("t", time_axis).set_units("t", "s")
    data.name("signal")
    if index == 0:
        field_sweep = ndshape([len(field_axis), len(time_axis)], ["field", "t"]).alloc(
            dtype=complex128
        )
        field_sweep.setaxis("field", field_axis).set_units("field", "G")
        field_sweep.setaxis("t", time_axis).set_units("t", "s")
    field_sweep["field", index] = data
SpinCore_pp.stopBoard()
print("EXITING...")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        print("SAVING FILE...")
        field_sweep.name("field_sweep")
        field_sweep.hdf5_write(date + "_" + output_name + ".h5")
        print("Name of saved data", field_sweep.name())
        print("Units of saved data", field_sweep.get_units("t"))
        print("Shape of saved data", ndshape(field_sweep))
        save_file = False
    except Exception as e:
        print(e)
        print("FILE ALREADY EXISTS.")
        save_file = False
fl.next("raw data")
# manual_taxis_zero = acq_time*1e-3/2.0
# field_sweep.setaxis('t',lambda x: x-manual_taxis_zero)
fl.image(field_sweep)
field_sweep.ft("t", shift=True)
fl.next("FT raw field_sweep")
fl.image(field_sweep)
fl.show()
