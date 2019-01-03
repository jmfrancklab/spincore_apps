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

# Initializing dataset

from pyspecdata import *
from scipy.optimize import nnls

fl = figlist_var()
date = '190103'
id_string = 'T1CPMG_ph2'

absvis = lambda x: abs(x).convolve('t2',10).real
phvis = lambda x: x.C.convolve('t2',10)

def cropvis(d, at=1e-3):
    retval = phvis(d)
    newabs = abs(retval)
    level = newabs.data.max()*at
    newabs[lambda x: x>level] = level
    retval *= newabs/abs(retval)
    return retval
nPoints = 128
nEchoes = 32
nPhaseSteps = 4
filename = date+'_'+id_string+'.h5'
nodename = 'signal'
s = nddata_hdf5(filename+'/'+nodename,
        directory = getDATADIR(
            exp_type = 'test_equip'))
s.set_units('t','s')
fl.next('raw data - no clock correction')
fl.image(s)
s.ft('t',shift=True)
clock_correction = -10.51/6 # radians per second
s *= exp(-1j*s.fromaxis('vd')*clock_correction)
s.ift('t')
fl.next('raw data - clock correction')
fl.image(s)
vd_len = len(s.getaxis('vd'))
orig_t = s.getaxis('t')
t2_axis = linspace(0,s.getaxis('t')[nPoints],nPoints)
s.setaxis('t',None)
s.chunk('t',['ph1','nEchoes','t2'],[nPhaseSteps,nEchoes,-1])
s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
s.setaxis('nEchoes',r_[1:nEchoes+1])
s.setaxis('t2',t2_axis).set_units('t2','s')
fl.next(id_string+' chunked, no ft')
fl.image(s)
s.ft(['ph1'])
print ndshape(s)
fl.next(id_string+' image plot coherence')
fl.image(s['vd',0])
s.ft('t2',shift=True)
fl.next(id_string+' image plot coherence -- ft')
fl.image(s['vd',0])
s.ift('t2')
fl.show();quit()


















d = find_file(exp_name, exp_type='NMR_Data_EGR', dimname='indirect', expno=expno)
n_indirect = d.get_prop('acq')['L'][23] # changed to l23 from pp
print "number of delays (tau 1):",n_indirect
with figlist_var() as fl:
    # convolving to visualize better
    plot_raw = True
    absvis = lambda x: abs(x).convolve('t2',0.1).real
    use_bad_hack = True
    if use_bad_hack:
        # this is a hack to at least get rid of the large data in Emily's bad dataset
        for j in r_[65,131,197]:
            d['t2':(6,None)]['indirect',j] = 0
            d['t2',0]['indirect',j] = 0
            d['t2',-1]['indirect',j] = 0
    if plot_raw:
        fl.next('raw data', figsize=(4,14))
        fl.image(absvis(d))
        fl.show()
    d.setaxis('indirect',None)
    print "shape before chunking along indirect",ndshape(d)
    d.chunk('indirect',['indirect','phcyc'],[n_indirect,-1])
    print "shape after chunking along indirect",ndshape(d)
    fl.next('after chunk',figsize=(8,30))
    fl.image(abs(d))
    d.chunk('phcyc',['ph3','ph2','ph1'],[2,4,2])
chunk_checkpoint = d.C


# Checkpoint

# 


d = chunk_checkpoint.C
orig_t = d.getaxis('t2').copy()
d.setaxis('ph1',r_[0,2.]/4)
d.setaxis('ph2',r_[0,1,2,3.]/4)
d.setaxis('ph3',r_[0,2.]/4)
print "vdlist is:",d.get_prop('vd')
d.setaxis('indirect',d.get_prop('vd'))
d.ft(['ph3','ph2','ph1'])
d.reorder(['indirect','t2'],first=False)
visualize_ph_cycling = False
if visualize_ph_cycling:
    with figlist_var() as fl:
        fl.next('after phase cycle',figsize=(8,14))
        fl.image(absvis(d))
        fl.next('after phase cycle, ph',figsize=(8,14))
        fl.image(d)
phcyc_checkpoint = d.C


# Pulling signal

# 


d = phcyc_checkpoint.C
d = d['ph3',0]['ph1',0]


# Pulling parameters

# 


n_echoes = d.get_prop('acq')['L'][12]
n_delays = len(d.getaxis('indirect'))
SW = d.get_prop('acq')['SW']
SFO1 = d.get_prop('acq')['SFO1']
SWH = SW*SFO1
DW = 1.0/SWH
t2 = len(d.getaxis('t2'))
tau2 = t2/n_delays
print "Number of echoes:",n_echoes
d.setaxis('t2',None)
ndshape(d.chunk('t2',['echo','t2'],[n_echoes,-1]))
d.setaxis('t2',orig_t[:ndshape(d)['t2']])
t2_len = d.getaxis('t2')[-1]
d.setaxis('t2', lambda x: x-t2_len/2)
d.setaxis('echo',r_[:n_echoes])
echochunk_checkpoint = d.C
figure(figsize=(8,18))
image(abs(d)['ph2',1]);show()


# Checkpoint

# 


d = echochunk_checkpoint.C
d.ft('t2',shift=True)
d *= exp(1j*(140.*pi/180)/2.1e3*d.fromaxis('t2'))
d_forplot = d.C.convolve('t2',10)
d_ph = d_forplot['indirect',-1].C.run(sum,'t2')
d_ph /= abs(d_ph)
d_forplot /= d_ph
#NOTE: ['ph2',1] are odd echoes and ['ph2',-1] are even echoes
#Thus here we only image the odd echoes
figure(figsize=(20,18))
image(cropvis(d_forplot['ph2',1],at=0.1), black=True);show()
figure(figsize=(20,18))
image(d_forplot['ph2',1].real);show()
figure(figsize=(20,18))
image(d_forplot['ph2',1].imag);show()
#image(d_forplot['ph2',1], black=True);show()
ph_checkpoint = d_forplot.C


# Interleaving echoes

# 


d = ph_checkpoint.C

#figure(figsize=(10,10));image(d['ph2',1]['echo',1::2],black=True);show()
#figure();image(d['ph2',-1]['echo',0::2],black=True);show()

with figlist_var() as fl:
    for indirect_idx,indirect_val in enumerate(d.getaxis('indirect')):
        even = d['ph2',-1]['echo',1::2]
        odd = d['ph2',1]['echo',0::2]
        fl.next('image even')
        fl.image(cropvis(even))
        fl.next('image odd')
        fl.image(cropvis(odd))
        #}}}
        phdiff = even/odd*abs(odd)
        fl.next('phase diff')
        fl.image(cropvis(phdiff))
        even_minus_odd_ph = phdiff.data.mean()
        even_minus_odd_ph /= abs(even_minus_odd_ph)
        print "FOR DELAY",indirect_idx,"=",indirect_val,"s PHASE DIFF IS",format(angle(even_minus_odd_ph)*180/pi)
        fl.next('Interleaving echoes')
        d_interleaved = d['ph2',1]
        d_interleaved['echo',1::2] = d['ph2',-1]['echo',1::2].run(conj)
        fl.image(cropvis(d_interleaved))
print ndshape(d_interleaved) 
fl.show()


# Checkpoint

# 


d = d_interleaved.C


# For determining 'NOISE FLOOR' as described in Mitchell et al. - 2012.

# 


d.sum('t2')
floor = d.imag['echo':(d.getaxis('echo')[5],d.getaxis('echo')[-1])]
devi_list = []
for x in xrange(len(floor.getaxis('indirect'))):
    devi_list.append(std(floor['indirect',x].data))
noise_floor = sum(devi_list)/len(devi_list)
print "Noise floor (standard deviation of imaginary channel) is ",noise_floor


# Sum along T2

# 


d = d_interleaved
t2 = len(d.getaxis('t2'))
n_tau2 = len(d.getaxis('echo'))
d_sum = d.C.sum('t2')
d_sum = d_sum.real
data = d_sum.C
data.rename('indirect','tau1')
data.rename('echo','tau2')
print ndshape(data)


# Load interactive plotting

# 


get_ipython().run_line_magic('matplotlib', 'notebook')


# Checkpoint

# 


data_nd = data.C
data_nd.meshplot(cmap=cm.viridis)
show()
print ndshape(data_nd)
data = data_nd.data
print shape(data)


# Turn off interactive plotting

# 


get_ipython().run_line_magic('matplotlib', 'inline')


# Entire 2D ILT procedure (as described in Venkataramanan et al. 2002) below

# 


#Note notation is consistent with that used in Venkataramanan et al. 2002, but varies from ref to ref
#Note importance of using properly phased data as input (see Mitchell et al. 2012)
#Implements singular value truncation at cutoff defined by noise (see Mitchell et al. 2012)

#Here are several booleans which can be used to follow the algorithm
plot_s_decay = False
plot_projected = True
plot_projected_3d = False
plot_compressed = True
plot_compressed_ordered = True
numpy_image = False
visualize_guess = False
S_curve = False # Must be True to use any of the booleans below
gen_S_curve_data = False # Time intensive
plot_S_curve = False
S_curve_guess = False

print "Constructing kernels..."
Nx = 40
Ny = 40
log_Nx_ax = linspace(log10(3e-3),log10(30),Nx) # T1
log_Ny_ax = linspace(log10(3e-3),log10(30),Ny) # T2
tau1 = data_nd.getaxis('tau1')
tau2 = data_nd.getaxis('tau2')
N1_4d = reshape(tau1,(shape(tau1)[0],1,1,1))
N2_4d = reshape(tau2,(1,shape(tau2)[0],1,1))
Nx_4d = reshape(10**log_Nx_ax,(1,1,shape(log_Nx_ax)[0],1))
Ny_4d = reshape(10**log_Ny_ax,(1,1,1,shape(log_Ny_ax)[0]))
print "Shape of parameter of interest (x) axis",shape(log_Nx_ax),shape(Nx_4d)
print "Shape of parameter of interest (y) axis",shape(log_Ny_ax),shape(Ny_4d)
print "Shape of indirect dimension (tau1) axis",shape(tau1),shape(N1_4d)
print "Shape of indirect dimension (tau2) axis",shape(tau2),shape(N2_4d)
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

print ""
print "*** BEGINNING COMPRESSION ***"
print ""
data_max = amax(data_nd.data)
print "Maximum in the data",data_max
s_cutoff = noise_floor/data_max
print "Cutoff singular values below",s_cutoff 
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
        
if plot_s_decay:
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

if plot_projected:
    for tau1_index in xrange(shape(data_proj)[0]):
        title('projected data')
        plot(data_proj[tau1_index,:])
    show()
if plot_projected_3d:
    nd_proj = nddata(data_proj,['N1','N2'])
    nd_proj.name('Projected data')
    nd_proj.setaxis('N1',data_nd.getaxis('tau1')).rename('N1',r'$\tau_{1}$')
    nd_proj.setaxis('N2',data_nd.getaxis('tau2')).rename('N2',r'$\tau_{2}$')
    nd_proj.meshplot(cmap=cm.viridis)

print "Projected data dimensions:",shape(data_proj)
data_compr = U1.T.dot(data.dot(U2))
print "Compressed data dimensioins:",shape(data_compr)

comp = data_compr
comp = reshape(comp,(shape(data_compr))[0]*(shape(data_compr))[1])

if plot_compressed:
    figure()
    for x in xrange((shape(data_compr))[1]):
        plot(data_compr[:,x],'-.')
    ylabel('Compressed data')
    xlabel('Index')
    show()

if plot_compressed_ordered:
    figure()
    plot(comp,'-.')
    ylabel('Compressed data')
    xlabel('Index')
    show()

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

datac_lex = []
for m in xrange(shape(data_compr)[0]):
    for l in xrange(shape(data_compr)[1]):
        temp = data_compr[m][l]
        datac_lex.append(temp)
print "Dimension of lexicographically ordered data:",shape(datac_lex)[0]
print "Should match first dimension of compressed tensor kernel K0 which is",shape(K0)[0]

nnls_noreg = False
if nnls_noreg:
    x, rnorm = nnls(K0,datac_lex)
    solution = reshape(x,(Nx,Ny))
    figure()
    title('Estimate, no regularization')
    image(solution)
    show()
    
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



if S_curve:
    if gen_S_curve_data:
        lambda_range = logspace(log10(8e-4),log10(2e4),3)
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
    if plot_S_curve:  
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
    if S_curve_guess:
        heel = raw_input("heel of S curve: ")
        heel_alpha = 10**heel
        heel_lambda = sqrt(heel_alpha)
        print "Alpha",heel_alpha
        print "Lambda",heel_lambda
        guess_lambda = heel_lambda

if not S_curve:
    guess_lambda = 600 # Set to any desired variable
    alpha = guess_lambda**2
    print "Alpha",alpha
    print "Lambda",guess_lambda

if visualize_guess:
    print "Estimating solution for guessed smoothing parameter..."
    opt_vec = nnls_reg(guess_lambda)
    solution = reshape(opt_vec,(Nx,Ny))
    figure()
    title(r'Est F(log$(T_{1}$),log$(T_{2})$, $\lambda$ = %0.3f'%(guess_lambda))
    image(solution);show()
print ""
print "*** BEGINNING MODIFIED BRD OPTIMIZATION ***"
print ""
opt_val = mod_BRD(guess=guess_lambda,maxiter=20)
print "OPTIMIZED LAMBDA:",opt_val
print ""
print "*** FINDING OPTIMIZED SOLUTION ***"
print ""
opt_vec = nnls_reg(opt_val)
solution = reshape(opt_vec,(Nx,Ny))
if numpy_image:
    figure()
    title(r'Est F(log$(T_{1}$),log$(T_{2})$, $\lambda$ = %0.2f'%(opt_val))
    image(solution);show()
nd_solution = nddata(solution,['log(T1)','log(T2)'])
nd_solution.setaxis('log(T1)',log_Nx_ax.copy())
nd_solution.setaxis('log(T2)',log_Ny_ax.copy())
figure();title(r'Peak #1: Estimated F(log$(T_{1})$,log($T_{2}$)), $\lambda$ = %0.2f'%opt_val)
nd_solution.contour(labels=False)
gcf().subplots_adjust(bottom=0.15)

