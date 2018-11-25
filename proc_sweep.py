from pyspecdata import *
fl = figlist_var()
date = '181121'
id_string = 'sweep1'
filename = date+'_'+id_string+'.h5'
nodename = 'signal'
s = nddata_hdf5(filename+'/'+nodename,
        directory = getDATADIR(exp_type = 'test_equip' ))
s.set_units('t','s')
s.set_units('field','G')
print ndshape(s)
s.reorder('t',first=True)
s.ft('t',shift=True)
s *= exp(1j*2*pi*pi*1.05)
offset_plot = s.C
offset_plot.setaxis('t', lambda x: x/(2*pi*gammabar_H)*1e4).set_units('t','G')
offset_plot.rename('t',r'$\frac{\Omega}{2 \pi \gamma_{H}}$')
fl.next('offset')
fl.plot(offset_plot[r'$\frac{\Omega}{2 \pi \gamma_{H}}$':(-326e-3,282e-3)],alpha=0.35)
print ndshape(offset_plot)
offset_plot.reorder('field', first=True)
fl.next('sweep, image plot abs (offset)')
fl.image(abs(offset_plot))
fl.next('sweep, image plot (offset)')
fl.image(offset_plot)
s.ift('t')
s.reorder('t', first=False)
fl.next('sweep, image plot abs (time)')
fl.image(abs(s['t':(0,4e-3)]))
fl.next('sweep, image plot (time)')
fl.image(s['t':(0,4e-3)])
fl.show();quit()
s.ft('t')
print ndshape(s)
s.reorder('t',first=True)
print ndshape(s)
#fl.plot(abs(s)['field':3418.0])
fl.show()
