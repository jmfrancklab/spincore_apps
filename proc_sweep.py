from pyspecdata import *
fl = figlist_var()
date = '181120'
id_string = 'sweep2'
filename = date+'_'+id_string+'.h5'
nodename = 'signal'
s = nddata_hdf5(filename+'/'+nodename,
        directory = getDATADIR(exp_type = 'test_equip' ))
s.set_units('t','s')
s.set_units('field','G')
s.ft('t',shift=True)
s *= exp(1j*2*pi*pi*1.05)
s.ift('t')
fl.next('imaging absolute val')
fl.image(abs(s))
fl.next('imaging')
fl.image(s)
fl.next('plot')
fl.plot(s['field':3410.0].real)
fl.plot(s['field':3410.0].imag)
s.ft('t')
print ndshape(s)
s.reorder('t',first=True)
print ndshape(s)
fl.next('plot all')
fl.plot(s)
#fl.plot(abs(s)['field':3418.0])
fl.show()
