from pyspecdata import *
from scipy.optimize import minimize
fl = figlist_var()
date = '190104'
id_string = 'nutation_1'
filename = date+'_'+id_string+'.h5'
nodename = 'nutation'
s = nddata_hdf5(filename+'/'+nodename,
        directory = getDATADIR(exp_type = 'test_equip' ))
s.rename('t','t2').set_units('t2','s')
s.set_units('p_90','s')
s.ft('t2',shift=True)
f_axis = s.getaxis('t2')
s.ift('t2')
SWH = diff(r_[f_axis[0],f_axis[-1]])[0]
test_plot = False
if test_plot:
    fl.next('plot')
    for x in r_[0:int(len(s.getaxis('p_90'))):5]:
        fl.plot(s['p_90',x],alpha=0.5,label='%d'%x)
        fl.show();quit()
s.ft('t2')
#{{{
phasing = False
if phasing:
    gen_cost = False 
    if gen_cost:
        sample = s['p_90',7].C
        N = 100
        dw = 100
        x = nddata(r_[-0.3:0.3:N*1j],'phi0').set_units('phi0','cyc')
        phi0 = exp(1j*2*pi*x)
        x = nddata(r_[-3e-1*dw/SWH/2:3e-1*dw/SWH/2:N*1j],'phi1').set_units('phi1','s')
        phi1 = 1j*2*pi*x
        sample *= phi0
        sample *= exp(phi1*sample.fromaxis('t2'))
        sample_absr = sample.C
        sample_absr.data = abs(sample_absr.data.real)
        sample_absr.sum('t2')
        fl.next('abs real cost')
        fl.image(sample_absr)
        fl.show();quit()
    ph0 = 215e-3-9.75e-3
    ph1 = 11.5e-6+0.152e-6
    ph0_c = exp(1j*2*pi*ph0)
    ph1_c = 1j*2*pi*ph1
    s *= ph0_c
    s *= exp(ph1_c*s.fromaxis('t2'))
    s.ift('t2')
    fl.next('plot phase corrected data')
    fl.plot(s['p_90',7].real,alpha=0.4,label='real')
    fl.plot(s['p_90',7].imag,alpha=0.4,label='imag')
    #}}}
fl.next('image')
fl.image(s)
fl.next('image abs')
fl.image(abs(s))
fl.show();quit()
