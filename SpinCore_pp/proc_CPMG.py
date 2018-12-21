from pyspecdata import *
from scipy.optimize import leastsq
from scipy.optimize import minimize 
fl = figlist_var()
for date,id_string in [
        ('181221','CPMG_4')
        ]:
    nPoints = 128
    nEchoes = 32
    nPhaseSteps = 4
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    fl.next(id_string+' raw data')
    fl.plot(s.real,alpha=0.4)
    fl.plot(s.imag,alpha=0.4)
    t2_axis = linspace(0,s.getaxis('t')[nPoints],nPoints)
    s.setaxis('t',None)
    s.chunk('t',['ph1','nEchoes','t2'],[nPhaseSteps,nEchoes,-1])
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    s.setaxis('nEchoes',r_[1:nEchoes+1])
    s.setaxis('t2',t2_axis)
    s.ft(['ph1'])
    fl.next(id_string+' image plot coherence')
    fl.image(s)
    phasing = False
    if phasing:
        sample = s['ph1',1]['nEchoes',0].C
        fl.next('phase plot')
        fl.plot(sample.real,',',alpha=0.4,label='real')
        fl.plot(sample.imag,',',alpha=0.4,label='imag')
        sample.ft('t2',shift=True)
        f_axis = sample.getaxis('t2')
        sample.ift('t2')
        SWH = diff(r_[f_axis[0],f_axis[-1]])[0]
        ph0 = 51.3e-3#+0.3e-3
        ph1 = 277e-6#-5.8e-6
        ph0_corr = exp(-1j*2*pi*ph0)
        ph1_corr = 1j*2*pi*ph1
        sample.ft('t2')
        sample *= ph0_corr
        sample *= exp(sample.fromaxis('t2')*ph1_corr)
        sample *= exp(1j*0.5*pi)
        sample.ift('t2')
        fl.next('phase plot')
        fl.plot(sample.real,alpha=0.4,label='real ph')
        fl.plot(sample.imag,alpha=0.4,label='imag ph')
        gen_cost = False
        if gen_cost:
            sample.ft('t2')
            N = 100
            dw = 100
            x = nddata(r_[-0.3:0.3:N*1j],'phi0').set_units('phi0','cyc')
            phi0 = exp(-1j*2*pi*x)
            x = nddata(r_[-3e-1*dw/SWH/2:3e-1*dw/SWH/2:N*1j],'phi1').set_units('phi1','s')
            phi1 = -1j*2*pi*x
            sample *= phi0
            sample *= exp(phi1*sample.fromaxis('t2'))
            sample_absr = sample.C
            sample_absr.data = abs(sample_absr.data.real)
            sample_absr.sum('t2')
            fl.next('abs real cost')
            fl.image(sample_absr)
            fl.show();quit()
        fl.show();quit()
    ph0 = 51.3e-3
    ph1 = 277e-6
    ph0_corr = exp(-1j*2*pi*ph0)
    ph1_corr = 1j*2*pi*ph1
    s.ft('t2')
    s *= ph0_corr
    s *= exp(s.fromaxis('t2')*ph1_corr)
    s *= exp(1j*0.5*pi)
    s.ift('t2')
    interleaved = ndshape([2,16,128],['evenodd','nEchoes','t2']).alloc()
    interleaved.setaxis('evenodd',r_[0:3])
    interleaved.setaxis('nEchoes',r_[1:nEchoes/2+1])
    interleaved.setaxis('t2',s.getaxis('t2').copy())
    interleaved['evenodd',0] = s['ph1',1]['nEchoes',0::2].C.run(conj)
    interleaved['evenodd',1] = s['ph1',-1]['nEchoes',1::2].C
    fl.next('interleaved')
    fl.image(interleaved)
    interleaved.ft('t2')
    phdiff = interleaved['evenodd',1]/interleaved['evenodd',0]*abs(interleaved['evenodd',0])
    fl.next('ph diff')
    fl.image(phdiff)
    phdiff *= abs(interleaved['evenodd',1])
    f_axis = interleaved.getaxis('t2')
    def costfun(firstorder):
        phshift = exp(-1j*2*pi*f_axis*firstorder)
        return -1*abs((phdiff * phshift).data[:].sum())
    sol = minimize(costfun, ([0],),
            method='L-BFGS-B',
            bounds=((-1e-3,1e-3),))
    firstorder = sol.x[0]
    phshift = exp(-1j*2*pi*f_axis*firstorder)
    phdiff_corr = phdiff.C
    phdiff_corr *= phshift
    zeroorder = phdiff_corr.data[:].sum().conj()
    zeroorder /= abs(zeroorder)
    phdiff_corr *= zeroorder
    print "relative phase shift was",firstorder/1e-6,"microseconds and,",angle(zeroorder)/pi*180,"degrees"
    interleaved['evenodd',1] *= zeroorder
    interleaved['evenodd',1] *= exp(-1j*2*pi*interleaved['evenodd',1].fromaxis('t2')*firstorder)
    interleaved.ift('t2')
    interleaved.reorder('evenodd',first=False)
    interleaved.smoosh(['nEchoes','evenodd'],noaxis=True)
    interleaved.reorder('t2',first=False)
    fl.next('interleaved, smooshed')
    fl.image(interleaved)
fl.show();quit()
