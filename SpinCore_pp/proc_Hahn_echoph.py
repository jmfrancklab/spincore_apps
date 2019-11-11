from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping
class flv(figlist_var):
    def show_complex(fl,d,**kwargs):
        fl.plot(abs(d),'k',alpha=0.75,**kwargs)
        fl.plot(d.real,'b',alpha=0.75,**kwargs)
        fl.plot(d.imag,'r',alpha=0.75,**kwargs)
        return
fl = flv()
for date,id_string,label_string in [
        ('191007','echo_2','1007_echo'),
        ]:
    #title_string = 'unenhanced'
    title_string = ''
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    nPoints = s.get_prop('acq_params')['nPoints']
    nEchoes = s.get_prop('acq_params')['nEchoes']
    nPhaseSteps = s.get_prop('acq_params')['nPhaseSteps']
    SW_kHz = s.get_prop('acq_params')['SW_kHz']
    s.reorder('t',first=True)
    t2_axis = s.getaxis('t')[0:nPoints/nPhaseSteps]
    s.setaxis('t',None)
    s.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    s.setaxis('ph2',r_[0.,2.]/4)
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    s.setaxis('t2',t2_axis)
    s.reorder('t2',first=False)
    s.ft(['ph1','ph2'])
    show_coherence = False
    if show_coherence:
        fl.next(id_string+'raw data - chunking coh')
        fl.image(s)
    s.ft('t2',shift=True)
    if show_coherence:
        fl.next(id_string+'raw data - FT')
        fl.image(s)
    s = s['ph1',1]['ph2',0].C
    s = s['t2':(-1e3,1e3)].C
    fl.next('f domain')
    fl.show_complex(s)
    s.ift('t2')
    # Center the time-domain echo at t = 0
    max_data = abs(s.data).max()
    pairs = s.contiguous(lambda x: abs(x) > max_data*0.5)
    longest_pair = diff(pairs).argmax()
    peak_location = pairs[longest_pair,:]
    s.setaxis('t2',lambda x: x-peak_location.mean())
    s.register_axis({'t2':0})
    s_none = s.C
    s_sliced = s['t2':(0,None)].C
    s_sliced['t2',0] *= 0.5
    fl.next('Crude centering')
    fl.show_complex(s)
    s.ft('t2',pad=128)
    s_none.ft('t2')
    s_sliced.ft('t2',pad=True)
    fl.next('Crude + cutoff')
    fl.show_complex(s_sliced)
    fl.next('Crude centering - ft')
    fl.show_complex(s_none)
    fl.next('Crude centering, pad - ft')
    fl.show_complex(s)
    abs_val_real = True
    #{{{ Absolute value of the real phasing procedure 
    if abs_val_real:
        print "*** *** ***"
        print "BEGIN ABSOLUTE VALUE OF THE REAL PHASING..."
        print "*** *** ***"
        before = s.C
        fl.next('(Abs Val Real) Pre-phasing: real and imag (Without Enhancement)')
        fl.plot(s.real,c='black',alpha=0.8,label='real')
        fl.plot(s.imag,c='red',alpha=0.8,label='imag')
        s.ift('t2')
        temp = s.C
        temp.ft('t2')
        SW = diff(temp.getaxis('t2')[r_[0,-1]]).item()
        thisph1 = nddata(r_[-6:6:2048j]/SW,'phi1').set_units('phi1','s')
        phase_test_r = temp * exp(-1j*2*pi*thisph1*temp.fromaxis('t2'))
        phase_test_rph0 = phase_test_r.C.sum('t2')
        phase_test_rph0 /= abs(phase_test_rph0)
        phase_test_r /= phase_test_rph0
        cost = abs(phase_test_r.real).sum('t2')
        ph1_opt = cost.argmin('phi1').data
        temp *= exp(-1j*2*pi*ph1_opt*temp.fromaxis('t2'))
        ph0 = temp.C.sum('t2')
        ph0 /= abs(ph0)
        temp /= ph0
        s.ft('t2')
        s *= exp(-1j*2*pi*ph1_opt*s.fromaxis('t2'))
        s /= ph0
        fl.next('(Abs Val Real) Post-phasing: real and imag (Without Enhancement)')
        fl.plot(s.real,c='black',alpha=0.8,label='real')
        fl.plot(s.imag,c='red',alpha=0.8,label='imag')
        fl.next('Compare before and after - real')
        fl.plot(before.real,alpha=0.8,label='before',human_units=False)
        fl.plot(s.real,alpha=0.8,label='after',human_units=False)
        fl.next('Compare before and after - imag')
        fl.plot(before.imag,alpha=0.8,label='before',human_units=False)
        fl.plot(s.imag,alpha=0.8,label='after',human_units=False)
        print "*** *** ***"
        print "FINISHED ABSOLUTE VALUE OF THE REAL PHASING"
        print "*** *** ***"
    #}}}
    fl.show();quit()
    hermit_phasing = False
    #{{{ Hermitian symmetry cost function phasing algorithm
    if hermit_phasing:
        print "*** *** ***"
        print "BEGIN HERMITIAN SYMMETRY PHASING..."
        print "*** *** ***"
        # Get rid of negative time points, and scale first time point appropriately
        s.ift('t2')
        s = s['t2':(0,None)]
        s['t2',0] *= 0.5
        fl.next('sliced')
        fl.plot(s)
        fl.next('Visualize sliced peak')
        fl.plot(s.C.ft('t2'),human_units=False)
        s.ft('t2')
        df = diff(s.getaxis('t2')[r_[0,1]])[0]
        max_hwidth = 6
        window_hwidth = 2
        max_shift = (max_hwidth - window_hwidth)*df
        center_index = where(abs(s.getaxis('t2'))==abs(s.getaxis('t2')).min())[0][0]
        slice_ = s['t2',int(center_index-max_hwidth) : int(center_index+max_hwidth+1)].C
        slice_center_index = where(abs(slice_.getaxis('t2'))==abs(slice_.getaxis('t2')).min())[0][0]
        fl.plot(slice_,':',human_units=False)
        print slice_center_index
        f_axis = slice_.fromaxis('t2')
        fl.next('Pre-phasing: real and imag (Without Enhancement)')
        fl.plot(s.real,c='black',alpha=0.8,label='real')
        fl.plot(s.imag,c='red',alpha=0.8,label='imag')
        temp = s.C
        def hermitian_costfunc(p):
            zerorder_rad,firstorder = p
            phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
            phshift *= exp(-1j*2*pi*zerorder_rad)
            temp = phshift * slice_
            deviation = temp['t2',(slice_center_index - window_hwidth):(slice_center_index+window_hwidth+1)].C
            deviation -= deviation['t2',::-1].C.run(conj)
            return (abs(deviation.data)**2)[:].sum()
        iteration = 0
        def print_func(x,f,accepted):
            global iteration
            print(iteration,x,int(accepted))
            iteration = iteration+1

        sol = basinhopping(hermitian_costfunc, r_[0.,0.],
                minimizer_kwargs={"method":'L-BFGS-B'},
                callback=print_func,
                stepsize=100.,
                niter=500,
                T=1000.
                )
        zerorder_rad,firstorder = sol.x
        f_axis = s.getaxis('t2')
        phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
        phshift *= exp(-1j*2*pi*zerorder_rad)

        s *= phshift
        # If phasing algorithm gives negative result, correct it here
        max_data_index = where(abs(s.data)==abs(s.data).max())
        if s.data[max_data_index] < 0:
            s *= -1.0
        fl.next('Visualize sliced peak')
        fl.plot(s,c='black',alpha=0.8,human_units=False)
        fl.next('Post-phasing: real and imag (Without Enhancement)')
        fl.plot(s.real,c='black',alpha=0.8,label='real')
        fl.plot(s.imag,c='red',alpha=0.8,label='imag')
        print "*** *** ***"
        print "FINISHED HERMITIAN SYMMETRY PHASING"
        print "*** *** ***"
        fl.show();quit()
    #}}}
    fl.next('Aer ODNP - freq domain '+title_string)
    fl.plot(s.real,alpha=0.7,label='%s'%label_string)
    #fl.plot(s.imag,alpha=0.7,label='imag')
    #fl.plot(abs(s),':')
    s.ift('t2')
    fl.next('time-signal '+title_string)
    fl.plot(s.real,alpha=0.7,label='%s'%label_string)
    #fl.plot(s.imag,alpha=0.7,label='imag')
    #fl.plot(abs(s),':')
fl.show()
