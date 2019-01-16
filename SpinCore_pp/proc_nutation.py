from pyspecdata import *
from scipy.optimize import minimize
fl = figlist_var()
date = '190115'
for id_string in [
    'nutation_3',
    'nutation_4',
    'nutation_5',
    'nutation_6',
    ]:
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
    s.setaxis('t2', lambda x: x-2.55e-3)
    fl.next(id_string+'image t')
    fl.image(s)
    s.ft('t2')
    fl.next(id_string+'image')
    fl.image(s)
    fl.next(id_string+'image -- $B_1$ distribution')
    fl.image(abs(s.C.ft('p_90',shift=True)))
    fl.next(id_string+'image abs')
    fl.image(abs(s))
fl.show();quit()
