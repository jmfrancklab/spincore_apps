from numpy import empty
import pylab as plt
import h5py, time
from pyspecdata import *
from matplotlib.ticker import FuncFormatter
import matplotlib.transforms as transforms
from dateutil import parser
from datetime import timedelta
time_origin = parser.parse('0:00')
@FuncFormatter
def thetime(x, position):
    return (time_origin+timedelta(seconds=x)).strftime('%H:%M:%S')

myfile = "210622_100mM_TEMPO_hexane_capillary_probe.h5"
data = nddata_hdf5(myfile+"/enhancement_curve")
with h5py.File(myfile, 'r') as f:
    log_grp = f['log']
    dset = log_grp['log']
    print("length of dset",dset.shape)
    # {{{ convert to a proper structured array
    read_array = empty(len(dset), dtype=dset.dtype)
    read_array[:] = dset
    # }}}
    read_dict = {}
    for j in range(dset.attrs['dict_len']):
        val = dset.attrs['val%d'%j]
        if isinstance(val, bytes):
            val = val.decode('ASCII')
        read_dict[dset.attrs['key%d'%j]] = val
with figlist_var() as fl:
    data.reorder(['power','t2'],first=False)
    fl.next('raw data')
    data.ft(['ph1'])
    fl.image(data.C.setaxis('power','#'))
    fl.next('FT and slice')
    data.ft('t2', shift=True)
    data = data['t2':(-2e3,2e3)]
    fl.image(data.C.setaxis('power','#'))
    # {{{ show the log
    fig, (ax_Rx,ax_power) = plt.subplots(2,1, figsize=(10,8))
    fl.next("log", fig=fig)
    print("the log starts at",time.strftime('%m/%d/%y %I:%M %p',time.localtime(read_array['time'][0])))
    read_array['time'] -= read_array['time'][0] # for the purposes of this log, start at zero
    ax_Rx.xaxis.set_major_formatter(thetime)
    ax_power.xaxis.set_major_formatter(thetime)
    ax_Rx.set_ylabel('Rx / mV')
    ax_Rx.plot(read_array['time'], read_array['Rx'], '.')
    ax_power.set_ylabel('power / dBm')
    ax_power.plot(read_array['time'], read_array['power'], '.')
    mask = read_array['cmd'] != 0
    n_events = len(read_array['time'][mask])
    trans_power = transforms.blended_transform_factory(
        ax_power.transData, ax_power.transAxes)
    trans_Rx = transforms.blended_transform_factory(
        ax_Rx.transData, ax_Rx.transAxes)
    for j,thisevent in enumerate(read_array[mask]):
        ax_Rx.axvline(x=thisevent['time'])
        ax_power.axvline(x=thisevent['time'])
        y_pos = j/n_events
        #ax_Rx.text(thisevent['time'], y_pos, read_dict[thisevent['cmd']], transform=trans_Rx)
        #ax_power.text(thisevent['time'], y_pos, read_dict[thisevent['cmd']], transform=trans_power)
    #ax.legend(**dict(bbox_to_anchor=(1.05,1), loc=2, borderaxespad=0.))
    plt.tight_layout()
    # }}}
