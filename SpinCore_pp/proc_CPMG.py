from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping
fl = figlist_var()
for date,id_string in [
        ('190114','CPMG_ph3'),
        #('190114','CPMG_ph3_m1'),
        #('190114','CPMG_ph3_m2'),
        ('190114','CPMG_ph3_m3'),
        ('190114','CPMG_ph3_m4'),
        ('190114','CPMG_ph3_m5'),
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
    fl.next('compare')
    #fl.plot(s.real,alpha=0.4)
    #fl.plot(s.imag,alpha=0.4)
    fl.plot(abs(s),':',alpha=0.4,label='%s'%id_string)
fl.show();quit() 
