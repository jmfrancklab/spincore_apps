#!/usr/bin/env python
# coding: utf-8

# In[1]:


#%load_ext pyspecdata.ipy
from pyspecdata import *
from scipy.optimize import minimize,basinhopping,nnls
init_logging(level='debug')


# In[2]:


# Initializing dataset


# In[3]:


fl = figlist_var()
date = '190710'
id_string = 'T1CPMG_3'


# In[4]:


filename = date+'_'+id_string+'.h5'
nodename = 'signal'
s = nddata_hdf5(filename+'/'+nodename,
        directory = getDATADIR(
            exp_type = 'test_equip'))

nPoints = s.get_prop('acq_params')['nPoints']
nEchoes = s.get_prop('acq_params')['nEchoes']
nPhaseSteps = s.get_prop('acq_params')['nPhaseSteps']
SW_kHz = s.get_prop('acq_params')['SW_kHz']

s.set_units('t','s')
fl.next('raw data - no clock correction')
fl.image(s)


# In[5]:


clock_corr = True 
if clock_corr:
    s.ft('t',shift=True)
    #clock_correction = 1.479/0.993471 # rad/sec
    #clock_correction = 2.17297/0.982767 # rad/sec
    #clock_correction = 1.04611/3.00005 # rad/sec
    clock_correction = -1.9/6 + 2/1.
    s *= exp(-1j*s.fromaxis('vd')*clock_correction)
    s.ift('t')
    fl.next('raw data - clock correction')
    fl.image(s)


# In[6]:


orig_t = s.getaxis('t')
p90_s = s.get_prop('acq_params')['p90_us']*1e-6
transient_s = s.get_prop('acq_params')['deadtime_us']*1e-6
deblank = 1.0*1e-6
acq_time_s = orig_t[nPoints]
tau_s = s.get_prop('acq_params')['tau_us']*1e-6
pad_s = s.get_prop('acq_params')['pad_us']*1e-6
tE_s = 2.0*p90_s + transient_s + acq_time_s + pad_s
print "ACQUISITION TIME:",acq_time_s,"s"
print "TAU DELAY:",tau_s,"s"
print "TWICE TAU:",2.0*tau_s,"s"
print "ECHO TIME:",tE_s,"s"
vd_list = s.getaxis('vd')
t2_axis = linspace(0,acq_time_s,nPoints)
tE_axis = r_[1:nEchoes+1]*tE_s
s.setaxis('t',None)
s.chunk('t',['ph1','nEchoes','t2'],[nPhaseSteps,nEchoes,-1])
s.setaxis('ph1',r_[0.,2.]/4)
s.setaxis('nEchoes',r_[1:nEchoes+1])
s.setaxis('t2',t2_axis).set_units('t2','s')
s.setaxis('vd',vd_list).set_units('vd','s')
with figlist_var() as fl:
    fl.next('before ph ft')
    fl.image(s)


# In[7]:


print ndshape(s)


# In[8]:


s.ft(['ph1'])
with figlist_var() as fl:
    fl.next(id_string+' image plot coherence')
    fl.image(s)


# In[9]:


s.ft('t2',shift=True)
fl.next(id_string+' image plot coherence -- ft')
fl.image(s)


# In[10]:


s.ift('t2')
s.reorder('vd',first=False)
coh = s.C.smoosh(['ph1','nEchoes','t2'],'t2').reorder('t2',first=False)
coh.setaxis('t2',orig_t).set_units('t2','s')
s = s['ph1',1].C


# In[11]:


with figlist_var() as fl:
    s.ft('t2')
    fl.next('plotting f')
    fl.plot(s['nEchoes',0]['vd',0])
    s.ift('t2')
    fl.next('plotting t')
    fl.plot(s['nEchoes',0]['vd',0])


# In[12]:


s.reorder('vd',first=True)
echo_center = abs(s)['nEchoes',0]['vd',0].argmax('t2').data.item()
s.setaxis('t2', lambda x: x-echo_center)
with figlist_var() as fl:
    fl.next('check center')
    fl.image(s)


# In[13]:


with figlist_var() as fl:
    fl.next('plotting t')
    fl.plot(s['nEchoes',0]['vd',0])
    s.ft('t2')
    fl.next('plotting f')
    fl.plot(s['nEchoes',0]['vd',0])
    s.ift('t2')


# In[14]:


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
        niter=200,
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


# In[15]:


# CHECKPOINT


# In[16]:


checkpoint = s.C


# In[17]:


# IF WANTING TO FIND T2 DECAY


# In[ ]:


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

# In[18]:


d = checkpoint.C
d = d.C.sum('t2')
d = d.real


# In[19]:


print "Constructing kernels..."
Nx = 100
Ny = 100
#Nx_ax = nddata(linspace(0.02,0.2,Nx),'T1') # T1 
#Ny_ax = nddata(linspace(0.02,0.2,Ny),'T2') # T2
Nx_ax = nddata(logspace(-3,1,Nx),'T1')
Ny_ax = nddata(logspace(-3,1,Ny),'T2')
data = d.C
data.rename('vd','tau1').setaxis('tau1',vd_list)
data.rename('nEchoes','tau2').setaxis('tau2',tE_axis)


# In[20]:


this = lambda x1,x2,y1,y2: (1-2*exp(-x1/y1),exp(-x2/y2))

x = data.C.nnls(('tau1','tau2'),
       (Nx_ax,Ny_ax),
       (lambda x1,x2: 1.-2*exp(-x1/x2),
        lambda y1,y2: exp(-y1/y2)),
                 l='BRD')

x.setaxis('T1',log10(Nx_ax.data)).set_units('T1',None)
x.setaxis('T2',log10(Ny_ax.data)).set_units('T2',None)


# In[21]:


image(x)
xlabel(r'$log(T_2/$s$)$')
ylabel(r'$log(T_1/$s$)$')
title('Higher SNR, repeat July 9, 2019 T1-T2 measurement')


# In[32]:


# Pull this from the log file, for now
s1 = 12
s2 = 7


# In[72]:


# In order to generate the residual, need the compressed data
# however this relies on being given the individual compressed kernels,
# which right now I do not return, thus this needs to be added into the method
# for now, I construct the kernels separately ( and redundantly )


# In[29]:


soln_vec = array(x.data)
datac_lex = []
for m in xrange(shape(soln_vec)[0]):
    for l in xrange(shape(soln_vec)[1]):
        temp = soln_vec[m][l]
        datac_lex.append(temp)
print "Dimension of lexicographically ordered data:",shape(datac_lex)[0]
K0 = x.get_prop('nnls_kernel')


# In[59]:


tau1 = data.getaxis('tau1')
tau2 = data.getaxis('tau2')
N1_4d = reshape(tau1,(shape(tau1)[0],1,1,1))
N2_4d = reshape(tau2,(1,shape(tau2)[0],1,1))
Nx_4d = reshape(logspace(-3,1,Nx),(1,1,shape(logspace(-3,1,Nx))[0],1))
Ny_4d = reshape(logspace(-3,1,Ny),(1,1,1,shape(logspace(-3,1,Ny))[0]))


# In[61]:


k1 = (1.-2*exp(-1*N1_4d/Nx_4d))
k2 = exp(-N2_4d/Ny_4d)
print "Shape of K1 (relates tau1 and x)",shape(k1)
print "Shape of K2 (relates tau2 and y)",shape(k2)
k1_sqz = squeeze(k1)
k2_sqz = squeeze(k2)
U1,S1_row,V1 = np.linalg.svd(k1_sqz,full_matrices=False)
print "SVD of K1",map(lambda x: x.shape, (U1, S1_row, V1))
U2,S2_row,V2 = np.linalg.svd(k2_sqz,full_matrices=False)
print "SVD of K2",map(lambda x: x.shape, (U2, S2_row, V2))


# In[62]:


print "Uncompressed singular row vector for K1",S1_row.shape
S1_row = S1_row[0:s1]
print "Compressed singular value row vector for K1",S1_row.shape
V1 = V1[0:s1,:]
U1 = U1[:,0:s1]
print "Compressed V matrix for K1",V1.shape
print "Comrpessed U matrix for K1",U1.shape

print "Uncompressed singular row vector for K2",S2_row.shape
S2_row = S2_row[0:s2]
print "Compressed singular value row vector for K2",S2_row.shape
V2 = V2[0:s2,:]
U2 = U2[:,0:s2]
print "Compressed V matrix for K2",V2.shape
print "Compressed U matrix for K2",U2.shape

I_S1 = eye(S1_row.shape[0])
S1 = S1_row*I_S1
print "Non-zero singular value matrix for K1",S1.shape

I_S2 = eye(S2_row.shape[0])
S2 = S2_row*I_S2
print "Non-zero singular value matrix for K2",S2.shape


# In[67]:


data_compr = U1.T.dot(data.data.dot(U2))
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


# In[68]:


nd_comp = nddata(reshape(comp,(s1,s2)),['$\widetilde{N_{1}}$','$\widetilde{N_{2}}$'])
nd_fit = nddata(reshape(K0.dot(datac_lex),(s1,s2)),['$\widetilde{N_{1}}$','$\widetilde{N_{2}}$'])


# In[69]:


nd_residual = nd_comp - nd_fit


# In[70]:


figure(figsize=(13,8));suptitle('DATASET: %s_%s'%(date,id_string))
subplot(221);subplot(221).set_title('COMPRESSED DATA\n $\widetilde{m}$')
image(nd_comp)
subplot(222);subplot(222).set_title('FIT\n $(\widetilde{K_{1}}\otimes\widetilde{K_{2}})x$')
image(nd_fit)
subplots_adjust(hspace=0.5)
subplot(223);subplot(223).set_title('DATA - FIT\n $\widetilde{m}$ - $(\widetilde{K_{1}}\otimes\widetilde{K_{2}})x$')
image(nd_residual)
subplot(224);subplot(224).set_title('|DATA - FIT|\n |$\widetilde{m}$ - $(\widetilde{K_{1}}\otimes\widetilde{K_{2}})x$|')
image(abs(nd_residual))


# In[ ]:


from matplotlib.colors import ListedColormap
from matplotlib.tri import Triangulation, TriAnalyzer, UniformTriRefiner
#cmdata = load(getDATADIR(exp_type='test_equip')+'contourcm.npz')
#cm = ListedColormap(cmdata['cm'],name='test')
figure(figsize=(8,6),facecolor=(1,1,1,0))
tri_x = (x.getaxis('T2')[newaxis,:]*ones(
    (len(x.getaxis('T1')),1))).ravel()
tri_y = (x.getaxis('T1')[:,newaxis]*ones((1,len(x.getaxis('T2'))))).ravel()
tri_z = x.reorder('T1').data.ravel()
tri = Triangulation(tri_x,tri_y)
refiner = UniformTriRefiner(tri)
subdiv = 3
tri_refi, tri_z_refi = refiner.refine_field(tri_z,subdiv=subdiv)
tri_z_refi[tri_z_refi<0] = 0
tricontourf(tri_refi,tri_z_refi,
           levels=linspace(tri_z_refi.min(),tri_z_refi.max(),100),
           
           )
colorbar()
xlabel(r'$log(T_2/$s$)$')
ylabel(r'$log(T_1/$s$)$')
title('T1-T2 Distribution for Ni-doped Water/IPA mixture (July 9, 2019)')


# In[ ]:




