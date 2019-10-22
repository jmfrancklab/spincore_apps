from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping
class flv(figlist_var):
    def show_complex(fl,d):
        fl.plot(abs(s),'k',alpha=0.5)
        fl.plot(s.real,'b',alpha=0.5)
        fl.plot(s.imag,'g',alpha=0.5)
        return
fl = flv()
for date,id_string in [
        ('191007','echo_2'),
        ]:
    title_string = 'unenhanced'
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    print ndshape(s)
    nPoints = s.get_prop('acq_params')['nPoints']
    nEchoes = s.get_prop('acq_params')['nEchoes']
    nPhaseSteps = s.get_prop('acq_params')['nPhaseSteps']
    SW_kHz = s.get_prop('acq_params')['SW_kHz']
    s.reorder('t',first=True)
    s.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    s.setaxis('ph2',r_[0.,2.]/4)
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    s.reorder('t2',first=False)
    s.ft(['ph1','ph2'])
    fl.next(id_string+'raw data - chunking coh')
    fl.image(s)
    s = s['ph1',1]['ph2',0]
    fl.next(id_string+'select pathway')
    fl.show_complex(s)
    # {{{ slice only f-domain with signal
    s.ft('t2', shift=True)
    fl.next('frequency domain')
    fl.plot(abs(s), human_units=False)# no human units to make sure
    #                                   axvline matches
    slice_f = (-1e3,1e3)
    axvline(x=slice_f[0],
            color='k')
    axvline(x=slice_f[1],
            color='k')
    text(slice_f[1], abs(s).data.max()*0.75,
            ' (slice this region)',
            ha='left')
    s = s['t2':slice_f]
    s.ift('t2')
    # }}}
    fl.next('frequency filtered')
    fl.show_complex(s)
    max_data = abs(s.data).max()
    pairs = s.contiguous(lambda x: abs(x) > max_data*0.5)
    longest_pair = diff(pairs).argmax()
    peak_location = pairs[longest_pair,:]
    axvline(x=peak_location[0],
            color='k')
    axvline(x=peak_location[1],
            color='k')
    text(peak_location[1], max_data*0.75,
            ' (lines delineate peak of echo)',
            ha='left')
    s.setaxis('t2',lambda x: x-peak_location.mean())
    # at this point, I need to get an axis that's in register with 0
    # -- this is what gives rise to "zero not in middle" below
    # I think I already have a function to do this
    fl.next('crude centering')
    fl.show_complex(s)
    max_shift = diff(peak_location).item()/2
    # {{{ just check signs of shift
    s.ft('t2')
    s_left = s * exp(+1j*2*pi*max_shift*s.fromaxis('t2'))
    s_right = s * exp(-1j*2*pi*max_shift*s.fromaxis('t2'))
    s.ift('t2')
    s_left.ift('t2')
    s_right.ift('t2')
    fl.next('illustrate shifting')
    fl.plot(abs(s), label='original',alpha=0.5)
    fl.plot(abs(s_left), label='max left',alpha=0.5)
    fl.plot(abs(s_right), label='max right',alpha=0.5)
    # }}}
    shift_t = nddata(r_[-1:1:1000j]*max_shift, 'shift')
    s.ft('t2')
    s_shifted = s * exp(-1j*2*pi*shift_t*s.fromaxis('t2'))
    s.ift('t2')
    s_shifted.ift('t2')
    s_shifted = s_shifted['t2':(-max_shift,max_shift)]
    # {{{ demand an odd number of points
    print s_shifted.getaxis('t2')[r_[0,ndshape(s_shifted)['t2']//2,ndshape(s_shifted)['t2']//2+1,-1]]
    if ndshape(s_shifted)['t2'] % 2 == 0:
        s_shifted = s_shifted['t2',:-1]
    assert s_shifted.getaxis('t2')[s_shifted.getaxis('t2').size//2+1] == 0, 'zero not in the middle! -- does your original axis contain a 0?'
    # }}}
    fl.next('first')
    fl.show_complex(s_shifted['shift',0])
    fl.next('middle')
    fl.show_complex(s_shifted['shift':0.0])
    fl.next('last')
    fl.show_complex(s_shifted['shift',-1])
    # {{{ the middle point, at t=0 must be entirely real
    ph0 = s_shifted['t2':0.0]
    ph0 /= abs(ph0)
    s_shifted /= ph0
    # }}}
    residual = abs(s_shifted - s_shifted['t2',::-1].runcopy(conj)).sum('t2')
    fl.next('cost function')
    fl.plot(residual)
fl.show()
