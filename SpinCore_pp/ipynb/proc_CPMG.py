
# coding: utf-8

# 


from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping,nnls


# 


fl = figlist_var()
for date,id_string in [
        ('190114','CPMG_ph3_p1')
        ]:
    nPoints = 64
    nEchoes = 64
    nPhaseSteps = 4
    SW_kHz = 20.0
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
    p90_s = 0.77*1e-6
    transient_s = 500.0*1e-6
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
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
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
    interleaved.copy_props(s).setaxis('t2',s.getaxis('t2').copy()).set_units('t2',s.get_units('t2'))
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
    interleaved.ift('t2')
    fl.next('interleaved')
    fl.image(interleaved)
    interleaved.ft('t2')
    fl.next('interleaved -- ft')
    fl.image(interleaved)
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
            #callback=print_fun,
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
    fl.next('interleaved -- phased ft')
    fl.image(interleaved)
    fl.next('final real data ft')
    fl.image(interleaved.real)
    fl.next('final imag data ft')
    fl.image(interleaved.imag)
    print ndshape(interleaved)
    interleaved.reorder('t2',first=True)
    fl.next('phased echoes, real - ft')
    fl.plot(interleaved.real)
    fl.next('phased echoes, real - ft waterfall')
    interleaved.real.waterfall()
    fl.next('phased echoes, imag - ft')
    fl.plot(interleaved.imag)
    interleaved = interleaved['t2':(-40e3,40e3)].C
    fl.next('phased echoes, real')
    fl.plot(interleaved.real)
    fl.next('phased echoes, imag')
    fl.plot(interleaved.imag)
    interleaved.rename('nEchoes','tE').setaxis('tE',tE_axis)
    data = interleaved.C.sum('t2')


# 


fl.next('Fit decay')
x = tE_axis 
ydata = data.data.real
ydata /= max(ydata)
fl.plot(x,ydata, '.', alpha=0.4, label='data', human_units=False)
fitfunc = lambda p, x: exp(-x/p[0]+p[1])
errfunc = lambda p_arg, x_arg, y_arg: fitfunc(p_arg, x_arg) - y_arg
p0 = [0.2,0.4]
p1, success = leastsq(errfunc, p0[:], args=(x, ydata))
x_fit = linspace(x.min(),x.max(),5000)
fl.plot(x_fit, fitfunc(p1, x_fit),':', label='fit (T2 = %0.2f ms)'%(p1[0]*1e3), human_units=False)
xlabel('t (sec)')
ylabel('Intensity')


# 


T2 = p1[0]
print "T2:",T2,"s"


# 


interleaved.reorder('t2',first=False)
d_T2 = interleaved.C#['tE':(interleaved.getaxis('tE')[0],interleaved.getaxis('tE')[16])].C
data = array(d_T2.data)


# 


Nx = 100
Nx_ax = linspace(3e-16,0.3,Nx) # T2
tau1 = d_T2.getaxis('tE')
N1_2d = reshape(tau1,(shape(tau1)[0],1)) # T1 POINTS
Nx_2d = reshape(Nx_ax,(1,shape(Nx_ax)[0])) # T1 VALUES
k1 = exp(-(N1_2d)/Nx_2d)
print "Shape of K1 (relates tau1 and x)",shape(k1)


# 


def gen_A_prime(val,dimension):
    return r_[k1, val*eye(dimension)]
A_prime = gen_A_prime(5,k1.shape[1])
b = zeros((data.shape[1],data.shape[0]))
for x in xrange(data.shape[1]):
    b[x,:] = data.real[:,x]
print shape(k1)
print shape(A_prime)
b_prime = zeros((b.shape[0],A_prime.shape[0]))
for x in xrange(b.shape[0]):
    b_prime[x,:] = r_[b[x,:],zeros(k1.shape[1])]
print shape(data)
print shape(b)
print shape(b_prime)


# 


print shape(A_prime),shape(b_prime)


# 

generate_L = False
if generate_L:
    lambda_range = logspace(log10(8e-3),log10(2e3),20)
    print shape(lambda_range)
    rnorm_list = empty_like(lambda_range)
    smoothing_list = empty_like(lambda_range)
    for index, lambda_val in enumerate(lambda_range):
        x = empty((b_prime.shape[0],k1.shape[1]))
        rnorm = empty(b_prime.shape[0])
        for z in xrange(shape(b_prime)[0]):
            x[z,:], rnorm[z] = nnls(gen_A_prime(lambda_val,k1.shape[1]),b_prime[z,:])
        temp = sum(rnorm)
        rnorm_list[index] = temp
        smoothing_list[index] = lambda_val
    figure('NNLS')
    rnorm_axis = array(rnorm_list)
    smoothing_axis = array(smoothing_list)
    plot(log10(smoothing_axis**2),rnorm_axis,'.-')


# 


heel = -0.7
heel_alpha = 10**float(heel)
heel_lambda = sqrt(heel_alpha)
print "Alpha",heel_alpha
print "Lambda",heel_lambda
guess_lambda = heel_lambda


# 


x = empty((b_prime.shape[0],k1.shape[1]))
rnorm  = empty_like(x)
for z in xrange(shape(b_prime)[0]):
    x[z,:], rnorm[z] = nnls(gen_A_prime(guess_lambda,k1.shape[1]),b_prime[z,:])


# 


nd_solution = nddata(x.T,[r'T2','shift'])
nd_solution.setaxis(r'T2',Nx_ax.copy()*1e3).set_units('T2','ms')
nd_solution.setaxis('shift',d_T2.getaxis('t2').copy()).set_units('shift','Hz')
figure();title('DATASET: %s,\n Estimated F($T_{2}$,$\Omega$), $\lambda$ = %0.4f'%(id_string,heel_lambda))
nd_solution.rename('shift',r'$\Omega$')
image(nd_solution)


# 


data_fit = k1.dot(x.T)
nd_fit = nddata(data_fit,['tE','t2'])
nd_fit.setaxis('tE',d_T2.getaxis('tE'))
nd_fit.setaxis('t2',d_T2.getaxis('t2'))
nd_residual = d_T2 - nd_fit


# 


figure(figsize=(13,8));suptitle('DATASET:%s'%id_string)
subplot(221);subplot(221).set_title('ABS DATA')
image(abs(d_T2))
subplot(222);subplot(222).set_title('ABS FIT (k * x.T)')
image(abs(nd_fit))
subplots_adjust(hspace=0.5)
subplot(223);subplot(223).set_title('DATA - FIT')
image(nd_residual)
subplot(224);subplot(224).set_title('ABS (DATA - FIT))')
image(abs(nd_residual))


# 


nd_solution[r'$\Omega$':(-3500,2600)][r'T2':(100,None)] = 0
figure();title('DATASET: %s,\n Edited F($T_{2}$,$\Omega$), $\lambda$ = %0.4f'%(id_string,heel_lambda))
image(nd_solution)


# 


x = nd_solution.data.T
data_fit = k1.dot(x.T)
nd_fit = nddata(data_fit,['tE','t2'])
nd_fit.setaxis('tE',d_T2.getaxis('tE'))
nd_fit.setaxis('t2',d_T2.getaxis('t2'))
nd_residual = d_T2 - nd_fit


# 


figure(figsize=(13,8));suptitle('DATASET: %s - Edited'%id_string)
subplot(221);subplot(221).set_title('ABS DATA')
image(abs(d_T2))
subplot(222);subplot(222).set_title('ABS FIT (k * x.T)')
image(abs(nd_fit))
subplots_adjust(hspace=0.5)
subplot(223);subplot(223).set_title('DATA - FIT')
image(nd_residual)
subplot(224);subplot(224).set_title('ABS (DATA - FIT))')
image(abs(nd_residual))
fl.show()
