
# coding: utf-8

# 


from pyspecdata import *
from scipy.optimize import minimize,basinhopping,nnls


# 


#References
#Venkataramanan et al. - 2002 (DOI : 10.1109/78.995059)
#Mitchell et al. - 2012 (DOI : 10.1016/j.pnmrs.2011.07.002)
#{{{ Functions for inversion
def nnls_reg(val):
    r'''A function that initializes the storage arrays and performs nnls using smoothing parameter :val:
        Calls function :A_prime: which generates the smoothing matrix for the fit and :b_prime: which is
        the lexicographically ordered data, extended by zeros to match the dimensions of the fit matrix.
    Parameters
    ----------
    val : float
        The smoothing parameter lambda (= sqrt(alpha))
    '''
    r_norm = empty([1])
    x,r_norm[0] = nnls(A_prime(val,dimension),b_prime)
    return x

def chi(x_vec,val):
    r'''The function that minimizes the c_r vector derived from Kuhn-Tucker conditions.
        Eq[31] in Venkataramanan et al. - 2002.
    Parameters
    ----------
    x_vec : array
        The c_r vector
    val : float
        The smoothing parameter lambda, which is converted to alpha (i.e., lambda**2)
        in the function.
    '''
    return 0.5*dot(x_vec.T,dot(dd_chi(G(x_vec),val**2),x_vec)) - dot(x_vec.T,m_vec)

def d_chi(x_vec,val):
    r'''The derivative of :chi:, which serves as the input function to the Newton Minimization
        procedure -- i.e., we find the zeros of this function which correspond to maxima or minima
        of :chi:
        Eq[32] in Venkataramanan et al. - 2002.
    Parameters
    ----------
    x_vec : array
        The c_r vector
    val : float
        The smoothing parameter lambda, which is converted to alpha (i.e., lambda**2)
        in the function.
    '''
    return dot(dd_chi(G(x_vec),val**2),x_vec) - m_vec

def dd_chi(G,val):
    r'''The second derivative of :chi:, which serves as the derivative of the input function to the
        Newton Minimization procedure -- i.e., we find the zeros of this function which correspond to
        maxima or minima of :chi:
        Eq[33] in Venkataramanan et al. - 2002.
    Parameters
    ----------
    G : matrix
        The diagonal matrix, see :G: 
    val : float
        The smoothing parameter lambda, which is converted to alpha (i.e., lambda**2)
        in the function.
    '''
    return G + (val**2)*eye(shape(G)[0])

def G(x_vec):
    r'''The symmetric matrix used in the BRD algorithm.   
        Eq[30] in Venkataramanan et al. - 2002.
    Parameters
    ----------
    x_vec : array
        The c_r vector
    '''
    return dot(K0,dot(square_heaviside(x_vec),K0.T))

def H(product):
    r'''A simple heaviside function, used in :G:
        See eq[30] in Venkataramanan et al. - 2002.
    Parameters
    ----------
    product : float
        The product of dotting a row element of the tensor product kernel with the
        c_r vector, used in :G:.
        See eq[30] in Venkataramanan et al. - 2002.
    '''
    if product <= 0:
        return 0
    if product > 0:
        return 1

def square_heaviside(x_vec):
    r'''The diagonal matrix used in :G:
        See eq[30] in Venkataramanan et al. - 2002.
    Parameters
    ----------
    x_vec : array
        The c_r vector
    '''
    diag_heavi = []
    for q in xrange(shape(K0.T)[0]):
        pull_val = dot(K0.T[q,:],x_vec)
        temp = pull_val[0]
        temp = H(temp)
        diag_heavi.append(temp)
    diag_heavi = array(diag_heavi)
    square_heavi = diag_heavi*eye(shape(diag_heavi)[0])
    return square_heavi

def newton_min(input_vec,val):
    r'''The Newton-Raphson minimization algorithm, provided by scipy.optimize.newton,
        which needs to be redefined to enable the use of vectors and matrices in the
        minimization procedure. Performs a single minimization to optimize the c_r
        vector.
    Parameters
    ----------
    input_vec : array
        The c_r vector generated from the NNLS output.
        Eq[26] in Venkataramanan et al. - 2002.
    val : float
        The smoothing parameter lambda, which is converted to alpha (i.e., lambda**2)
        in the function.
    '''
    fder = dd_chi(G(input_vec),val)
    fval = d_chi(input_vec,val)
    newton_step = dot(linalg.inv(fder),fval)
    update_vec = input_vec + newton_step
    return update_vec

def optimize_alpha(input_vec,val):
    r'''Optimizes the smoothing parameter using eq[48] in Venkataramanan et al. - 2002.
    Parameters
    ----------
    input_vec : array
        The optimized c_r vector generated from Newton Minimization procedure.
        Eq[26] in Venkataramanan et al. - 2002.
    val : float
        The smoothing parameter lambda, which is converted to alpha (i.e., lambda**2)
        in the function.
    '''
    alpha_converged = False
    fac = sqrt(choose_s1*choose_s2)
    T = linalg.inv(dd_chi(G(input_vec),val**2))
    dot_prod = dot(input_vec.T,dot(T,input_vec))
    ans = dot_prod*fac
    ans = ans/linalg.norm(input_vec)
    ans = ans/(dot_prod)
    tol = 1e-3
    if abs(ans-val**2) <= tol:
        print "ALPHA HAS CONVERGED"
        alpha_converged = True
        return ans,alpha_converged
    return ans,alpha_converged

def mod_BRD(guess,maxiter=20):
    r'''The modified BRD method presented in Venkataramanan et al. - 2002
        for optimizing the smoothing parameter using to regualrize the NNLS fit.
    Parameters
    ----------
    guess : float
        The initial smoothing parameter as lambda - i.e., sqrt(alpha). Algorithm
        should converge within a few steps irrespective of this guess.
    maxiter : int
        The maximum number of iterations for the algorithm, set to 20 by default.
        Should not need to be more than this.
     '''
    smoothing_param = guess
    alpha_converged = False
    for iter in xrange(maxiter):
        print "*** *** ITERATION NO.",iter,"*** ***"
        print "*** CURRENT LAMBDA",smoothing_param," *** "
        x_norm = empty([1])
        r_norm = empty([1])
        soln,r_norm = nnls(A_prime(smoothing_param,dimension),b_prime)
        f_vec = soln[:,newaxis]
        alpha = smoothing_param**2
        c_vec = dot(K0,f_vec) - m_vec
        c_vec /= -alpha
        new_c = newton_min(c_vec,smoothing_param)
        new_alpha,alpha_converged = optimize_alpha(new_c,smoothing_param)
        new_lambda = sqrt(new_alpha[0,0])
        if alpha_converged:
            print "*** OPTIMIZED LAMBDA",new_lambda," *** "
            break  
        if not alpha_converged:
            print "*** UPDATED LAMBDA",new_lambda," *** "
            smoothing_param = new_lambda
        if iter == maxiter-1:
            print "DID NOT CONVERGE."
    return new_lambda
#}}}


# 


# Initializing dataset


# 


fl = figlist_var()
date = '190116'
id_string = 'T1CPMG_1'

absvis = lambda x: abs(x).convolve('t2',10).real
phvis = lambda x: x.C.convolve('t2',10)

def cropvis(d, at=1e-3):
    retval = phvis(d)
    newabs = abs(retval)
    level = newabs.data.max()*at
    newabs[lambda x: x>level] = level
    retval *= newabs/abs(retval)
    return retval
SW_kHz = 60.0
nPoints = 64
nEchoes = 64
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
s.ft(['ph1'])
print ndshape(s)
fl.next(id_string+' image plot coherence')
fl.image(s)

s.ft('t2',shift=True)
fl.next(id_string+' image plot coherence -- ft')
fl.image(s)
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
fl.show()


# 


# CHECKPOINT


# 


checkpoint = s.C


# 


# IF WANTING TO FIND T2 DECAY


# 


T2_fits = True
if T2_fits:
    data_T2 = checkpoint.C
    data_T2.rename('nEchoes','tE').setaxis('tE',tE_axis)
    for index in r_[0:len(vd_list):1]:
        temp = data_T2['vd',index].C.sum('t2')
        #fl.next('Fit decay')
        x = tE_axis 
        ydata = temp.data.real
        if ydata.sum() < 0:
            ydata *= -1
        ydata /= max(ydata)
        #fl.plot(x,ydata, '.', alpha=0.4, label='data %d'%index, human_units=False)
        fitfunc = lambda p, x: exp(-x/p[0])
        errfunc = lambda p_arg, x_arg, y_arg: fitfunc(p_arg, x_arg) - y_arg
        p0 = [0.2]
        p1, success = leastsq(errfunc, p0[:], args=(x, ydata))
        x_fit = linspace(x.min(),x.max(),5000)
        #fl.plot(x_fit, fitfunc(p1, x_fit),':', label='fit %d (T2 = %0.2f ms)'%(index,p1[0]*1e3), human_units=False)
        fl.next('T2 Decay: Fit')
        fl.plot(x_fit, fitfunc(p1, x_fit),':', label='fit %d (T2 = %0.2f ms)'%(index,p1[0]*1e3), human_units=False)
        xlabel('t (sec)')
        ylabel('Intensity')
        T2 = p1[0]
        print "T2:",T2,"s"


# CHECKPOINT

# 


d = checkpoint.C


# For determining 'NOISE FLOOR' as described in Mitchell et al. - 2012.

# 


d.ft('t2')


# 


#d = d['t2':(-3.5e3,4e3)].C
d.setaxis('vd',vd_list)
d.rename('nEchoes','tE').setaxis('tE',tE_axis)
print ndshape(d)


# 


find_noise_floor = False
if find_noise_floor:
    d.sum('t2')
    floor = d.imag['nEchoes':(d.getaxis('nEchoes')[0],d.getaxis('nEchoes')[-1])]
    devi_list = []
    for x in xrange(len(floor.getaxis('vd'))):
        devi_list.append(std(floor['vd',x].data))
    noise_floor = sum(devi_list)/len(devi_list)
    print "Noise floor (standard deviation of imaginary channel) is ",noise_floor


# Sum along T2

# 


figure()
image(d.real)
figure()
image(d.imag)


# 


d_sum = d.C.sum('t2')
d_sum = d_sum.real


# 


data = d_sum.C
data.rename('vd','tau1') # T1 timing
data.rename('tE','tau2') # T2 timing
print ndshape(data)


# 


image(data)


# Load interactive plotting

# 


get_ipython().run_line_magic('matplotlib', 'notebook')


# 


data_nd = data.C
data_nd.meshplot(cmap=cm.viridis)
show()
print ndshape(data_nd)
data = data_nd.data
print shape(data)


# 


get_ipython().run_line_magic('matplotlib', 'inline')


# 


print ndshape(data_nd)


# Entire 2D ILT procedure (as described in Venkataramanan et al. 2002) below

# 


print "Constructing kernels..."
Nx = 50
Ny = 50
Nx_ax = linspace(1e-6,0.3,Nx) # T1 
Ny_ax = linspace(3e-16,0.3,Ny) # T2
# USED PARAMS BELOW - GOT GOOD DATA WITHOUT ZOOMING IN ON PEAKS OF INTEREST
# VERY GOOD PARAMS
#log_Nx_ax = linspace(log10(0.120),log10(0.145),Nx) # T1
#log_Ny_ax = linspace(log10(0.003),log10(0.1),Ny) # T2
# GOOD PARAMS
#Nx = 30
#Ny = 30
#log_Nx_ax = linspace(log10(0.090),log10(0.9),Nx) # T1
#log_Ny_ax = linspace(log10(0.009),log10(0.099),Ny) # T2
tau1 = data_nd.getaxis('tau1')
tau2 = data_nd.getaxis('tau2')
N1_4d = reshape(tau1,(shape(tau1)[0],1,1,1))
N2_4d = reshape(tau2,(1,shape(tau2)[0],1,1))
Nx_4d = reshape(Nx_ax,(1,1,shape(Nx_ax)[0],1))
Ny_4d = reshape(Ny_ax,(1,1,1,shape(Ny_ax)[0]))
print "Shape of parameter of interest (x) axis",shape(Nx_ax),shape(Nx_4d)
print "Shape of parameter of interest (y) axis",shape(Ny_ax),shape(Ny_4d)
print "Shape of indirect dimension (tau1) axis",shape(tau1),shape(N1_4d)
print "Shape of indirect dimension (tau2) axis",shape(tau2),shape(N2_4d)


# 


k1 = (1.-2*exp(-N1_4d/Nx_4d))
k2 = exp(-N2_4d/Ny_4d)
print "Shape of K1 (relates tau1 and x)",shape(k1)
print "Shape of K2 (relates tau2 and y)",shape(k2)
k1_sqz = squeeze(k1)
k2_sqz = squeeze(k2)
U1,S1_row,V1 = np.linalg.svd(k1_sqz,full_matrices=False)
print "SVD of K1",map(lambda x: x.shape, (U1, S1_row, V1))
U2,S2_row,V2 = np.linalg.svd(k2_sqz,full_matrices=False)
print "SVD of K2",map(lambda x: x.shape, (U2, S2_row, V2))


# 


print ""
print "*** BEGINNING COMPRESSION ***"
print ""
#data_max = amax(data_nd.data)
#print "Maximum in the data",data_max
#s_cutoff = noise_floor/data_max
#print "Cutoff singular values below",s_cutoff 
if find_noise_floor:
    for S1_i in xrange(shape(S1_row)[0]):
        if S1_row[S1_i] < s_cutoff:
            print "Truncate S1 at index",S1_i
            choose_s1 = S1_i
            break
    for S2_i in xrange(shape(S2_row)[0]):
        if S2_row[S2_i] < s_cutoff:
            print "Truncate S2 at index",S2_i
            choose_s2 = S2_i
            break


# 


with figlist_var() as fl:
    fl.next('singular values',figsize=(12,8))
    semilogy(S1_row,'o-',label='S1',alpha=0.2)
    semilogy(S2_row,'o-',label='S2',alpha=0.2)
    for j,val in enumerate(S1_row):
        annotate('%0.3f'%(val),(j,val),
                ha='left',va='bottom',rotation=10)
    for j,val in enumerate(S2_row):
        annotate('%0.3f'%(val),(j,val),
                ha='left',va='bottom',rotation=10)
    xlabel('Index')
    ylabel('Singular values')
    grid(b=True)
    legend()


# 


choose_s1 = 7
choose_s2 = 6


# 


print "Uncompressed singular row vector for K1",S1_row.shape
S1_row = S1_row[0:choose_s1]
print "Compressed singular value row vector for K1",S1_row.shape
V1 = V1[0:choose_s1,:]
U1 = U1[:,0:choose_s1]
print "Compressed V matrix for K1",V1.shape
print "Comrpessed U matrix for K1",U1.shape

print "Uncompressed singular row vector for K2",S2_row.shape
S2_row = S2_row[0:choose_s2]
print "Compressed singular value row vector for K2",S2_row.shape
V2 = V2[0:choose_s2,:]
U2 = U2[:,0:choose_s2]
print "Compressed V matrix for K2",V2.shape
print "Compressed U matrix for K2",U2.shape

I_S1 = eye(S1_row.shape[0])
S1 = S1_row*I_S1
print "Non-zero singular value matrix for K1",S1.shape

I_S2 = eye(S2_row.shape[0])
S2 = S2_row*I_S2
print "Non-zero singular value matrix for K2",S2.shape

data_proj = U1.dot(U1.T.dot(data.dot(U2.dot(U2.T))))

for tau1_index in xrange(shape(data_proj)[0]):
    title('projected data')
    plot(data_proj[tau1_index,:])
show()


# 


get_ipython().run_line_magic('matplotlib', 'notebook')


# 


nd_proj = nddata(data_proj,['N1','N2'])
nd_proj.name('Projected data')
nd_proj.setaxis('N1',data_nd.getaxis('tau1')).rename('N1',r'$\tau_{1}$')
nd_proj.setaxis('N2',data_nd.getaxis('tau2')).rename('N2',r'$\tau_{2}$')
nd_proj.meshplot(cmap=cm.viridis)


# 


get_ipython().run_line_magic('matplotlib', 'inline')


# 


print "Projected data dimensions:",shape(data_proj)
data_compr = U1.T.dot(data.dot(U2))
print "Compressed data dimensioins:",shape(data_compr)

comp = reshape(data_compr,(shape(data_compr))[0]*(shape(data_compr))[1])

figure()
title("S2 plotted against S1 kernel")
for x in xrange((shape(data_compr))[1]):
    plot(data_compr[:,x],'-.',label='%d'%x)
ylabel('Compressed data')
xlabel('Index')
legend()
show()


# 


figure()
plot(comp,'-.')
ylabel('Compressed data')
xlabel('Index')
show()


# 


K1 = S1.dot(V1)
K2 = S2.dot(V2)
print "Compressed K1",shape(K1)
print "Compressed K2",shape(K2)

K1 = reshape(K1, (shape(K1)[0],1,shape(K1)[1],1))
K2 = reshape(K2, (1,shape(K2)[0],1,shape(K2)[1]))
K0 = K1*K2
K0 = reshape(K0, (shape(K1)[0]*shape(K2)[1],shape(K1)[2]*shape(K2)[3]))
print "Compressed tensor kernel",shape(K0)
print "* Should be (",shape(S1)[0],"*",shape(S2)[0],") x (",shape(Nx_4d)[2],"*",shape(Ny_4d)[3],")"
#END COMPRESSION

print ""
print "*** FINISHED COMPRESSION ***"
print ""


# 


datac_lex = []
for m in xrange(shape(data_compr)[0]):
    for l in xrange(shape(data_compr)[1]):
        temp = data_compr[m][l]
        datac_lex.append(temp)
print "Dimension of lexicographically ordered data:",shape(datac_lex)[0]
print "Should match first dimension of compressed tensor kernel K0 which is",shape(K0)[0]

x, rnorm = nnls(K0,datac_lex)
solution = reshape(x,(Nx,Ny))
figure()
title('Estimate, no regularization')
image(solution)
show()


# 


print ""
print "*** BEGINNING REGULARIZATION ***"
print ""

datac_lex = array(datac_lex)
datac_lex = datac_lex[:,newaxis]
print "Lexicographically orderd data:",shape(datac_lex)

dimension = K0.shape[1]
def A_prime(val,dimension):
    A_prime = r_[K0, val*eye(dimension)]
    return A_prime

b_prime = r_[datac_lex,zeros((dimension,1))]
b_prime = b_prime.squeeze()
print "Shape of b vector",shape(b_prime)
m_vec = datac_lex


# 


do_this = False
if do_this:
    lambda_range = logspace(log10(8e-4),log10(2e4),5)
    rnorm_list = empty_like(lambda_range)
    smoothing_list = empty_like(lambda_range)
    alt_norm_list = empty_like(lambda_range)
    for index,lambda_val in enumerate(lambda_range):
        print "index",index
        soln,temp_rn = nnls(A_prime(lambda_val,dimension),b_prime)
        rnorm_list[index] = temp_rn
        f_vec = soln[:,newaxis]
        alpha = lambda_val**2
        c_vec = dot(K0,f_vec) - m_vec
        c_vec /= -alpha
        alt_temp = linalg.norm(c_vec)*alpha
        alt_norm_list[index] = alt_temp
        smoothing_list[index] = lambda_val


# 


if do_this:
    figure('using NNLS output norm')
    rnorm_axis = array(rnorm_list)
    smoothing_axis = array(smoothing_list)
    plot(log10(smoothing_axis**2),rnorm_axis)
    show()
    figure();title('using LV norm')
    altnorm_axis = array(alt_norm_list)
    smoothing_axis = array(smoothing_list)
    plot(log10(smoothing_axis**2),altnorm_axis,'-.',c='k')
    xlabel(r'log($\alpha$)')
    ylabel(r'$\chi$($\alpha$)')
    gridandtick(gca())
    show()


# 


heel = -5
heel_alpha = 10**float(heel)
heel_lambda = sqrt(heel_alpha)
print "Alpha",heel_alpha
print "Lambda",heel_lambda
guess_lambda = heel_lambda
print ""
print "*** BEGINNING MODIFIED BRD OPTIMIZATION ***"
print ""
#opt_val = mod_BRD(guess=guess_lambda,maxiter=20)
opt_val = mod_BRD(guess=heel_lambda,maxiter=20)
print "OPTIMIZED LAMBDA:",opt_val
print ""
print "*** FINDING OPTIMIZED SOLUTION ***"
print ""
opt_vec = nnls_reg(opt_val)
solution = reshape(opt_vec,(Nx,Ny))
nd_solution = nddata(solution.T,['T2','T1'])
nd_solution.setaxis('T1',Nx_ax.copy()*1e3).set_units('T1','ms')
nd_solution.setaxis('T2',Ny_ax.copy()*1e3).set_units('T2','ms')
figure();title(r'Estimated F($T_{1}$,$T_{2}$), $\lambda$ = %0.4f'%opt_val)
image(nd_solution)
gcf().subplots_adjust(bottom=0.15)


# 


data_fit = K0.dot(x.T)


# 


nd_fit = nddata(data_fit,['tE','t2'])


# 


print ndshape(d)


# 


print ndshape(K0)


# 


nd_fit.setaxis('tE',d.getaxis('tE'))
nd_fit.setaxis('t2',d.getaxis('t2'))
nd_residual = d - nd_fit

