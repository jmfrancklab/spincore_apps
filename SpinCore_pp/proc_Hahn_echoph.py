from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping
fl = figlist_var()
for date,id_string,label_str in [
        ('191111','echo_4','gradient off'),
        ('191111','echo_4_2','gradient off'),
        ('191111','echo_4_3','gradient off'),
        ('191111','echo_4_on','gradient on'),
        ('191111','echo_4_on_2','gradient on'),
        ('191111','echo_4_on_3','gradient on'),
        ]:
    #title_string = 'unenhanced'
    title_string = ''
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    acq_params = s.get_prop('acq_params')
    for j in ['nPoints', 'nEchoes', 'nPhaseSteps', 'SW_kHz']:
        globals()[j] = acq_params[j]
    s.reorder('t',first=True)
    I_require_validation = False
    if I_require_validation:
        print ndshape(s)
        t2_axis = s.getaxis('t')[0:nPoints/nPhaseSteps]
        print len(t2_axis)
        print t2_axis
    s.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    if I_require_validation:
        print ndshape(s)
        assert all(isclose(t2_axis,s.getaxis('t2')[0:nPoints/nPhaseSteps]))
    s.setaxis('ph2',r_[0.,2.]/4)
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    # s.setaxis('t2',t2_axis) <-- in the most recent version of pyspecdata (1) this is not needed and (2) it will fail, because t2_axis here is the wrong length
    s.ft(['ph1','ph2'])
    show_coherence = True
    if show_coherence:
        fl.next(id_string+'raw data - chunking coh')
        fl.image(s)
    s.ft('t2',shift=True)
    if show_coherence:
        fl.next(id_string+'raw data - FT')
        fl.image(s)
    s = s['ph1',1]['ph2',0]
    s = s['t2':(-1e3,1e3)]
    fl.next('f domain -- raw')
    fl.plot(s)
    s.ift('t2')
    # Center the time-domain echo at t = 0
    max_data = abs(s.data).max()
    pairs = s.contiguous(lambda x: abs(x) > max_data*0.5)
    longest_pair = diff(pairs).argmax()
    peak_location = pairs[longest_pair,:]
    s.setaxis('t2',lambda x: x-peak_location.mean())
    s.register_axis({'t2':0})
    s = s['t2':(0,None)]
    s['t2',0] *= 0.5
    fl.next('Crude centering - time domain')
    fl.plot(s,alpha=0.8,label='%s'%label_str)
    legend()
    savefig('191111_gradient_test_tdomain.png',
            transparent=True,
            bbox_inches='tight',
            pad_inches=False)
    s.ft('t2')#,pad=True)
    fl.next('Crude centering - ft + filtering + correction')
    fl.plot(s,alpha=0.8,label='%s'%label_str)
    legend()
    savefig('191111_gradient_test_fdomain.png',
            transparent=True,
            bbox_inches='tight',
            pad_inches=False)
    max_val = argmax(s.data)
    print max_val
fl.show();quit()
for date,id_string in [
        ('191031','echo_4'),
        ('191031','echo_4_2'),
        ('191031','echo_4_3'),
        ('191031','echo_4_on'),
        ('191031','echo_4_2_on'),
        ('191031','echo_4_3_on'),
        ]:
    abs_val_real = False
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
        thisph1 = nddata(r_[-4:4:2048j]/SW,'phi1').set_units('phi1','s')
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
    hermit_phasing = True
    #{{{ Hermitian symmetry cost function phasing algorithm
    if hermit_phasing:
        print "*** *** ***"
        print "BEGIN HERMITIAN SYMMETRY PHASING..."
        print "*** *** ***"
        fl.next('sliced')
        fl.plot(s,alpha=0.5)
        fl.plot(abs(s),alpha=0.5)
        df = diff(s.getaxis('t2')[r_[0,1]])[0]
        max_hwidth = 1
        window_hwidth = 10
        max_shift = (max_hwidth - window_hwidth)*df
        print s.getaxis('t2')
        # the following is for a peak centered at f = 0 Hz
        on_0 = False
        if on_0:
            center_index = where(abs(s.getaxis('t2'))==abs(s.getaxis('t2')).min())[0][0]
        else:
            center_index = argmax(s.data)
        slice_ = s['t2',int(center_index-max_hwidth) : int(center_index+max_hwidth+1)].C
        if on_0:
            slice_center_index = where(abs(slice_.getaxis('t2'))==abs(slice_.getaxis('t2')).min())[0][0]
        else:
            slice_center_index = argmax(slice_.data)
            print slice_center_index
        fl.plot(slice_,':',human_units=False)
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
                niter=100,
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
    fl.next('AER ODNP - ft + filtering + correction + phasing')
    fl.plot(s,label='%s'%label_string)
    #{{{ for plotting
    plot_this = True
    if plot_this:
        legend()
        savefig('aer_ODNP_ft_phasing_191112.png',
                transparent=True,
                bbox_inches='tight',
                pad_inches=0)
    #}}}
fl.show();quit()
    #s.ift('t2')
    #fl.next('Aer ODNP - NMR signal time'+title_string)
    #fl.plot(s,alpha=0.7,label='%s'%label_string)
fl.show()
