from pyspecdata import *
from scipy.optimize import minimize
fl = figlist_var()
date = '190515'
for id_string in [
    'nutation_1',
    ]:
    filename = date+'_'+id_string+'.h5'
    nodename = 'nutation'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(exp_type = 'test_equip' ))
    orig_t = s.getaxis('t')
    s.set_units('p_90','s')
    nPoints = 128
    acq_time_s = orig_t[nPoints]
    t2_axis = linspace(0,acq_time_s,nPoints)
    s.setaxis('t',None)
    s.reorder('t',first=True)
    s.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    s.setaxis('ph2',r_[0.,2.]/4)
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    s.setaxis('t2',t2_axis)
    s.reorder('t2',first=False)
    s.ft('t2',shift=True)
    #s *= exp(1j*2*pi*0.42) # manually determined ph correction
    fl.next('image, raw')
    fl.image(s)
    s.ft(['ph2','ph1'])
    fl.next('image, all coherence channels')
    fl.image(s)
    #fl.next('image, $\Delta c_{1}$ = 1,$\Delta c_{2}$ = 0')
    #fl.image(s['t2':(None,-30000)]['ph2',0]['ph1',1])
    #fl.next('image, $\Delta c_{1}$ = 0,$\Delta c_{2}$ = -1')
    #fl.image(s['ph2',1]['ph1',0])
    #fl.next('image, $\Delta c_{1}$ = -1,$\Delta c_{2}$ = 0')
    #fl.image(s['t2':(None,-30e-3)]['ph2',0]['ph1',-1])
    s = s['ph2',0]['ph1',1].C
    fl.next(id_string+'image')
    fl.image(s)
    fl.next(id_string+'image -- $B_1$ distribution')
    fl.image(abs(s.C.ft('p_90',shift=True)))
    fl.next(id_string+'image abs')
    fl.image(abs(s))
fl.show();quit()
