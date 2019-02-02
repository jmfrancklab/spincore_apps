from pyspecdata import *
fl = figlist_var()
for date,id_string,PW in [
        ('190201','SpinCore_pulses','0.88'),
        ]:
    filename = date+'_'+id_string+'.h5'
    id_string = id_string.replace('MWE_','Example ') # for plotting purposes
    nodename = 'accumulated_'+date
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    s = s['ch',0].C
    print ndshape(s)
    fl.next('idk')
    for i,x in enumerate(s.getaxis('capture')):
        fl.plot(s['capture',i],alpha=0.2)
    fl.show();quit()
