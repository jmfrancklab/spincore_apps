from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping

fl = figlist_var()
plt.rcParams['figure.figsize'] = (8,6)
for date,id_string in [
        ('190416','T1CPMG_6_1')
        ]:

    SW_kHz = 15.0
    nPoints = 256

    nEchoes = 32
    nPhaseSteps = 2
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    fl.next('raw data - no clock correction')
    fl.image(s)
    orig_t = s.getaxis('t')
    p90_s = 4.0*1e-6
    transient_s = 500.0*1e-6
    deblank = 1.0*1e-6
    acq_time_s = orig_t[nPoints]
    tau_s = transient_s + acq_time_s*0.5
    pad_s = 2.0*tau_s - transient_s - acq_time_s - 2.0*p90_s - deblank
    tE_s = 2.0*p90_s + transient_s + acq_time_s + pad_s
    print "ACQUISITION TIME:",acq_time_s,"s"
    print "TAU DELAY:",tau_s,"s"
    print "TWICE TAU:",2.0*tau_s,"s"
    print "ECHO TIME:",tE_s,"s"
    vd_list = s.getaxis('vd')
    t2_axis = linspace(0,s.getaxis('t')[nPoints],nPoints)
    tE_axis = r_[1:nEchoes+1]*tE_s
    s.ft('t',shift=True)
    clock_correction = -10.51/6 # radians per second
    s *= exp(-1j*s.fromaxis('vd')*clock_correction)
    s.ift('t')
    fl.next('raw data - clock correction')
    fl.image(s)
    s.setaxis('t',None)
    s.chunk('t',['ph1','nEchoes','t2'],[nPhaseSteps,nEchoes,-1])
    s.setaxis('ph1',r_[0.,2.]/4)
    s.setaxis('nEchoes',r_[1:nEchoes+1])
    s.setaxis('t2',t2_axis).set_units('t2','s')
    s.setaxis('vd',vd_list).set_units('vd','s')
    fl.next('before ph ft')
    fl.image(s['t2':(2.5e-3,None)])
    s.ft(['ph1'])
    print ndshape(s)
    fl.next(id_string+' image plot coherence')
    fl.image(s['t2':(2.5e-3,None)])
    s.ft('t2',shift=True)
    fl.next(id_string+' image plot coherence -- ft')
    fl.image(s['t2':(2.5e-3,None)])
    fl.show();quit()
    s.ift('t2')
    s.reorder('vd',first=False)
    coh = s.C.smoosh(['ph1','nEchoes','t2'],'t2').reorder('t2',first=False)
    coh.setaxis('t2',orig_t).set_units('t2','s')
    s = s['ph1',1].C
    s.reorder('vd',first=True)
    echo_center = abs(s)['nEchoes',0]['vd',0].argmax('t2').data.item()
    s.setaxis('t2', lambda x: x-echo_center)
    fl.next('check center')
    fl.image(s)
    s.ft('t2')
    fl.next('before phased - real ft')
    fl.image(s.real)
    fl.next('before phased - imag ft')
    fl.image(s.imag)
    fl.show();quit()
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
    fit_T2 = True
    if fit_T2:
        for index in r_[0:len(vd_list):1]:
            data_T2 = s['vd',index].C.sum('t2')
            x = tE_axis 
            ydata = data_T2.data.real
            if ydata.sum() < 0:
                ydata *= -1
            ydata /= max(ydata)
            fl.next('T2 decay along vd: data')
            fl.plot(x,ydata, '.', alpha=0.4, label='data %d'%index, human_units=False)
            fl.next('Fit decay')
            fl.plot(x,ydata, '.', alpha=0.4, label='data %d'%index, human_units=False)
            fitfunc = lambda p, x: exp(-x/p[0])
            errfunc = lambda p_arg, x_arg, y_arg: fitfunc(p_arg, x_arg) - y_arg
            p0 = [0.2]
            p1, success = leastsq(errfunc, p0[:], args=(x, ydata))
            x_fit = linspace(x.min(),x.max(),5000)
            fl.next('T2 decay along vd: fit')
            fl.plot(x_fit, fitfunc(p1, x_fit),':', label='fit %d (T2 = %0.2f ms)'%(index,p1[0]*1e3), human_units=False)
            fl.next('Fit decay')
            fl.plot(x_fit, fitfunc(p1, x_fit),':', label='fit %d (T2 = %0.2f ms)'%(index,p1[0]*1e3), human_units=False)
            xlabel('t (sec)')
            ylabel('Intensity')
            T2 = p1[0]
            print "T2:",T2,"s"
fl.show();quit()
