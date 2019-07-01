#!/usr/bin/env python
# coding: utf-8

# 


#%load_ext pyspecdata.ipy
from pyspecdata import *
from scipy.optimize import minimize,basinhopping,nnls
#init_logging(level='debug')


# Initializing dataset

# 


fl = figlist_var()
date = '190423'
id_string = 'T1CPMG_1'


# 


absvis = lambda x: abs(x).convolve('t2',10).real
phvis = lambda x: x.C.convolve('t2',10)

def cropvis(d, at=1e-3):
    retval = phvis(d)
    newabs = abs(retval)
    level = newabs.data.max()*at
    newabs[lambda x: x>level] = level
    retval *= newabs/abs(retval)
    return retval
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


# 


orig_t = s.getaxis('t')
p90_s = 3.75*1e-6
transient_s = 50.0*1e-6
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
t2_axis = linspace(0,acq_time_s,nPoints)
tE_axis = r_[1:nEchoes+1]*tE_s
s.setaxis('t',None)
s.chunk('t',['ph1','nEchoes','t2'],[nPhaseSteps,nEchoes,-1])
s.setaxis('ph1',r_[0.,2.]/4)
s.setaxis('nEchoes',r_[1:nEchoes+1])
s.setaxis('t2',t2_axis).set_units('t2','s')
s.setaxis('vd',vd_list).set_units('vd','s')
fl.next('before ph ft')
fl.image(s)


# 


s.ft(['ph1'])
fl.next(id_string+' image plot coherence')
fl.image(s)


# 


s.ft('t2',shift=True)
fl.next(id_string+' image plot coherence -- ft')
fl.image(s)


# 


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


# 


s *= -1
s.ft('t2')
fl.next('after phased - real ft')
fl.image(s.real)
fl.next('after phased - imag ft')
fl.image(s.imag)
s.ift('t2')
fl.next('after phased - real')
fl.image(s.real)
fl.next('after phased - imag')
fl.image(s.imag)


# CHECKPOINT

# 


checkpoint = s.C


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
d = d.C.sum('t2')
d = d.real


# 


print "Constructing kernels..."
Nx = 30
Ny = 30
#Nx_ax = nddata(linspace(0.02,0.2,Nx),'T1') # T1 
#Ny_ax = nddata(linspace(0.02,0.2,Ny),'T2') # T2
T1_axis = nddata(logspace(-3,1,Nx),'T1')
T2_axis = nddata(logspace(-3,1,Ny),'T2')
data = d.C
data.rename('vd','tau1').setaxis('tau1',vd_list)
data.rename('nEchoes','tau2').setaxis('tau2',tE_axis)


# 


this = lambda x1,x2,y1,y2: (1-2*exp(-x1/y1),exp(-x2/y2))

x = data.C.nnls(('tau1','tau2'),
       (T1_axis,T2_axis),
       (lambda x1,x2: 1.-2*exp(-x1/x2),
        lambda y1,y2: exp(-y1/y2)),
                 l='BRD')
# why is the following necessary?? it shouldn't be necessary!
x.setaxis('T1',T1_axis.data).set_units('T1','s')
x.setaxis('T2',T2_axis.data).set_units('T2','s')
# the following overrides, anyways, and is needed for the log-log plot
x.setaxis('T1',log10(T1_axis.data)).set_units('T1',None)
x.setaxis('T2',log10(T1_axis.data)).set_units('T2',None)


# 



fl.next('T1-T2 distribution for Water-IPA with Ni(II)')
fl.image(x,human_units=False)


# 


from matplotlib.colors import ListedColormap
from matplotlib.tri import Triangulation, TriAnalyzer, UniformTriRefiner
cmdata = load(getDATADIR(exp_type='test_equip')+'contourcm.npz')
cm = ListedColormap(cmdata['cm'],
        name='test')
figure(figsize=(8,6),facecolor=(1,1,1,0))
# {{{ I do this very manually,  but we should just integrate into pyspecdata;
# probably wait for after
tri_x = (x.getaxis('T2')[newaxis,:]*ones(
    (len(x.getaxis('T1')),1))).ravel()
tri_y = (x.getaxis('T1')[:,newaxis]*ones(
    (1,len(x.getaxis('T2'))))).ravel()
tri_z = x.reorder('T1').data.ravel()
tri = Triangulation(tri_x,
        tri_y)
refiner = UniformTriRefiner(tri)
subdiv = 3  # Number of recursive subdivisions of the initial mesh for smooth
            # plots. Values >3 might result in a very high number of triangles
            # for the refine mesh: new triangles numbering = (4**subdiv)*ntri
tri_refi, tri_z_refi = refiner.refine_field(tri_z, subdiv=subdiv)
#mask = TriAnalyzer(tri_refi).get_flat_tri_mask(10)
#tri_refi = tri_refi.set_mask(~mask)
tri_z_refi[tri_z_refi<0] = 0
tricontourf(tri_refi,tri_z_refi,
        levels=linspace(tri_z_refi.min(),tri_z_refi.max(),100),
        cmap=cm
        )
colorbar()
xlabel(r'$log(T_2/$s$)$')
ylabel(r'$log(T_1/$s$)$')
# }}}
savefig(r"water_IPA.png",
        dpi=300,facecolor=(1,1,1,0),bbox_inches='tight')


# 


fl.next('T1,T2 distribution for Water and IPA with Ni(II)')
fl.image(x)
fl.show()
