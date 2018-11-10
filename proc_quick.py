from pyspecdata import *
fl = figlist_var()
for date,id_string in [
        ('181109','SE_2'), # SW = 10 kHz
        ('181109','test_2') # SW = 10 kHz
        ]:
    print "BEGINNING WITH "+id_string
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    label=id_string
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    fl.next('capture, t')
    fl.plot(s)
    s.ft('t',shift=True)
    fl.next('capture, f')
    fl.plot(s,alpha=0.4,label='%s'%label)
fl.show()
