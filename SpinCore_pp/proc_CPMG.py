from pyspecdata import *
from scipy.optimize import leastsq
from scipy.optimize import minimize 
fl = figlist_var()
for date,id_string in [
        ('181221','CPMG_4'),
        ('181231','CPMG_1')
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
    orig_t = s.getaxis('t')
    fl.next(id_string+' raw data')
    s = s['t':(0,164e-3)]
    fl.plot(s.real,alpha=0.4)
    fl.plot(s.imag,alpha=0.4)
    fl.next(id_string+' abs raw data')
    s = s['t':(0,164e-3)]
    fl.plot(abs(s),alpha=0.4)
fl.show();quit()
