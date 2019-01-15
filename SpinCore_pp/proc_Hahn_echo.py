from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping
fl = figlist_var()
for date,id_string in [
        ('190114','test_echo_1'),
        ('190114','test_echo_2')
        ]:
    nPoints = 64
    nEchoes = 1
    nPhaseSteps = 1
    SW_kHz = 20.0
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    fl.next('comp raw data')
    fl.plot(s.real,alpha=0.4)
    fl.plot(s.imag,alpha=0.4)
    fl.plot(abs(s),':',c='k',alpha=0.4)
fl.show()