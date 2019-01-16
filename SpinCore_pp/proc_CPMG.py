from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping
fl = figlist_var()
for date,id_string in [
        ('190116','CPMG_3_')
        ]:
    SW_kHz = 20.0
    nPoints = 64
    nEchoes = 64
    nPhaseSteps = 2
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    fl.next(id_string+'raw data ')
    fl.plot(s.real,alpha=0.4)
    fl.plot(s.imag,alpha=0.4)
    fl.plot(abs(s),':',c='k',alpha=0.4)
    orig_t = s.getaxis('t')
    p90_s = 0.87*1e-6
    transient_s = 100.0*1e-6
    acq_time_s = orig_t[nPoints]
    tau_s = transient_s + acq_time_s*0.5
    pad_s = 2.0*tau_s - transient_s - acq_time_s - 2.0*p90_s
    tE_s = 2.0*p90_s + transient_s + acq_time_s + pad_s
    print "ACQUISITION TIME:",acq_time_s,"s"
    print "TAU DELAY:",tau_s,"s"
    print "TWICE TAU:",2.0*tau_s,"s"
    print "ECHO TIME:",tE_s,"s"
    t2_axis = linspace(0,acq_time_s,nPoints)
    tE_axis = r_[1:nEchoes+1]*tE_s
    s.setaxis('t',None)
    s.chunk('t',['ph1','tE','t2'],[nPhaseSteps,nEchoes,-1])
    s.setaxis('ph1',r_[0.,2.]/4)
    #tE_axis = r_[1:nEchoes+1]*tE_s
    s.setaxis('tE',tE_axis)
    s.setaxis('t2',t2_axis)
    fl.next(id_string+'raw data - chunking')
    fl.image(s)
    s.ft('t2', shift=True)
    fl.next(id_string+'raw data - chunking ft')
    fl.image(s)
    clock_correction = -10.51/6 # radians per second
    s * exp(-1j*s.fromaxis('tE')*clock_correction)
    fl.next(id_string+'raw data - chunking, clock correction ft')
    fl.image(s)
    s.ift('t2')
    fl.next(id_string+'raw data - chunking, clock correction')
    fl.image(s)
    s.ft(['ph1'])
    fl.next(id_string+' image plot coherence')
    fl.image(s)
    fl.next(id_string+' image plot coherence -- ft')
    s.ft('t2')
    fl.image(s)
    s.ift('t2')
    s = s['ph1',1].C
    echo_center = abs(s)['tE',0].argmax('t2').data.item()
    s.setaxis('t2', lambda x: x-echo_center)
    s.rename('tE','nEchoes').setaxis('nEchoes',r_[1:nEchoes+1])
    fl.next('check center')
    fl.image(s)
    s.ft('t2')
    fl.next('before phased - real ft')
    fl.image(s.real)
    fl.next('before phased - imag ft')
    fl.image(s.imag)
    f_axis = s.fromaxis('t2')
    def costfun(p):
        zeroorder_rad,firstorder = p
        phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
        phshift *= exp(-1j*2*pi*zeroorder_rad)
        corr_test = phshift * s
        return (abs(corr_test.data.imag)**2)[:].sum()
    iteration = 0
    def print_fun(x, f, accepted):
        global iteration
        iteration += 1
        print (iteration, x, f, int(accepted))
        return
    sol = basinhopping(costfun, r_[0.,0.],
            minimizer_kwargs={"method":'L-BFGS-B'},
            callback=print_fun,
            stepsize=100.,
            niter=100,
            T=1000.
            )
    zeroorder_rad, firstorder = sol.x
    phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
    phshift *= exp(-1j*2*pi*zeroorder_rad)
    s *= phshift
    print "RELATIVE PHASE SHIFT WAS {:0.1f}\us and {:0.1f}$^\circ$".format(
            firstorder,angle(zeroorder_rad)/pi*180)
    if s['nEchoes',0].data[:].sum().real < 0:
        s *= -1
    print ndshape(s)
    fl.next('after phased - real ft')
    fl.image(s.real)
    fl.next('after phased - imag ft')
    fl.image(s.imag)
    s.ift('t2')
    fl.next('after phased - real')
    fl.image(s.real)
    fl.next('after phased - imag')
    fl.image(s.imag)
    fl.next('real waterfall')
    s.real.waterfall()
    fl.next('imag waterfall')
    s.imag.waterfall()
    s.rename('nEchoes','tE').setaxis('tE',tE_axis)
    data = s.C.sum('t2')
    fl.next('Fit decay')
    x = tE_axis 
    ydata = data.data.real
    ydata /= max(ydata)
    fl.plot(x,ydata, '.', alpha=0.4, label='data', human_units=False)
    fitfunc = lambda p, x: exp(-x/p[0])
    errfunc = lambda p_arg, x_arg, y_arg: fitfunc(p_arg, x_arg) - y_arg
    p0 = [0.2]
    p1, success = leastsq(errfunc, p0[:], args=(x, ydata))
    x_fit = linspace(x.min(),x.max(),5000)
    fl.plot(x_fit, fitfunc(p1, x_fit),':', label='fit (T2 = %0.2f ms)'%(p1[0]*1e3), human_units=False)
    xlabel('t (sec)')
    ylabel('Intensity')
    T2 = p1[0]
    print "T2:",T2,"s"
    fl.show();quit()
    s.ift('t2')
    even_echo_center = abs(s)['ph1',1]['tE',0].argmax('t2').data.item()
    odd_echo_center = abs(s)['ph1',-1]['tE',1].argmax('t2').data.item()
    print "EVEN ECHO CENTER:",even_echo_center,"s"
    print "ODD ECHO CENTER:",odd_echo_center,"s"
    s.setaxis('t2',lambda x: x-even_echo_center)
    s.rename('tE','nEchoes').setaxis('nEchoes',r_[1:nEchoes+1])
    fl.next('check center before interleaving')
    fl.image(s)
    interleaved = ndshape(s)
    interleaved['ph1'] = 2
    interleaved['nEchoes'] /= 2
    interleaved = interleaved.rename('ph1','evenodd').alloc()
    #interleaved.copy_props(s).setaxis('t2',s.getaxis('t2').copy()).set_units('t2',s.get_units('t2'))
    interleaved.setaxis('t2',s.getaxis('t2').copy()).set_units('t2',s.get_units('t2'))
    interleaved.ft('t2',shift=True)
    interleaved.ift('t2')
    interleaved['evenodd',0] = s['ph1',1]['nEchoes',0::2].C.run(conj)['t2',::-1]
    interleaved['evenodd',1] = s['ph1',-1]['nEchoes',1::2]
    interleaved.ft('t2')
    fl.next('even and odd')
    fl.image(interleaved)
    phdiff = interleaved['evenodd',1]/interleaved['evenodd',0]*abs(interleaved['evenodd',0])
    fl.next('phdiff')
    fl.image(phdiff)
    phdiff *= abs(interleaved['evenodd',1])
    f_axis = interleaved.fromaxis('t2')
    def costfun(firstorder):
        phshift = exp(-1j*2*pi*f_axis*firstorder)
        return -1*abs((phdiff * phshift).data[:].sum())
    sol = minimize(costfun, ([0],),
            method='L-BFGS-B',
            bounds=((-1e-3,1e-3),)
            )
    firstorder = sol.x[0]
    phshift = exp(-1j*2*pi*f_axis*firstorder)
    phdiff_corr = phdiff.C
    phdiff_corr *= phshift
    zeroorder = phdiff_corr.data[:].sum().conj()
    zeroorder /= abs(zeroorder)
    fl.next('phdiff -- corrected')
    fl.image(phdiff_corr)
    print "Relative phase shift (for interleaving) was "        "{:0.1f}\us and {:0.1f}$^\circ$".format(
                firstorder/1e-6,angle(zeroorder)/pi*180)
    interleaved['evenodd',1] *= zeroorder*phshift
    interleaved.smoosh(['nEchoes','evenodd'],noaxis=True).reorder('t2',first=False)
    interleaved.setaxis('nEchoes',r_[1:nEchoes+1])
    f_axis = interleaved.fromaxis('t2')
    def costfun(p):
        zeroorder_rad,firstorder = p
        phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
        phshift *= exp(-1j*2*pi*zeroorder_rad)
        corr_test = phshift * interleaved
        return (abs(corr_test.data.imag)**2)[:].sum()
    iteration = 0
    def print_fun(x, f, accepted):
        global iteration
        iteration += 1
        print (iteration, x, f, int(accepted))
        return
    sol = basinhopping(costfun, r_[0.,0.],
            minimizer_kwargs={"method":'L-BFGS-B'},
            callback=print_fun,
            stepsize=100.,
            niter=100,
            T=1000.
            )
    zeroorder_rad, firstorder = sol.x
    phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
    phshift *= exp(-1j*2*pi*zeroorder_rad)
    interleaved *= phshift
    print "RELATIVE PHASE SHIFT WAS {:0.1f}\us and {:0.1f}$^\circ$".format(
            firstorder,angle(zeroorder_rad)/pi*180)
    if interleaved['nEchoes',0].data[:].sum().real < 0:
        interleaved *= -1
    print ndshape(interleaved)
    interleaved.reorder('t2',first=True)
    fl.next('phased echoes, real - ft')
    fl.plot(interleaved.real)
    fl.next('phased echoes, imag - ft')
    fl.plot(interleaved.imag)
    interleaved = interleaved['t2':(-4e3,4e3)].C
    fl.next('phased echoes, real')
    fl.plot(interleaved.real)
    fl.next('phased echoes, imag')
    fl.plot(interleaved.imag)
    interleaved.rename('nEchoes','tE').setaxis('tE',tE_axis)
    data = interleaved.C.sum('t2')
    fl.next('Fit decay')
    x = tE_axis 
    ydata = data.data.real
    ydata /= max(ydata)
    fl.plot(x,ydata, '.', alpha=0.4, label='data', human_units=False)
    fitfunc = lambda p, x: exp(-x/p[0])
    errfunc = lambda p_arg, x_arg, y_arg: fitfunc(p_arg, x_arg) - y_arg
    p0 = [0.2]
    p1, success = leastsq(errfunc, p0[:], args=(x, ydata))
    x_fit = linspace(x.min(),x.max(),5000)
    fl.plot(x_fit, fitfunc(p1, x_fit),':', label='fit (T2 = %0.2f ms)'%(p1[0]*1e3), human_units=False)
    xlabel('t (sec)')
    ylabel('Intensity')
    T2 = p1[0]
    print "T2:",T2,"s"
fl.show();quit()
