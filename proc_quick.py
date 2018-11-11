from pyspecdata import *
fl = figlist_var()
for date,id_string in [
        #('181109','SE_2'), # SW = 10 kHz
        #('181109','test_2') # SW = 10 kHz
        #('181109','test_3'), # SW = 1 kHz
        #('181109','SE_3') # SW = 1 kHz
        #('181109','SE_4'), # SW = 200 kHz
        #('181109','test_4') # SW = 200 kHz
        #('181109','SE_5') # SW = 200 kHz
        #('181110','SE_1'), # SW = 200 kHz
        ('181110','noise_1'), # SW = 200 kHz
        ]:
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    label=id_string
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    fl.next('capture, t')
    fl.plot(s,alpha=0.4,label='%s'%label)
    s.ft('t',shift=True)
    fl.next('capture, f')
    fl.plot(s,alpha=0.4,label='%s'%label)
fl.show()
