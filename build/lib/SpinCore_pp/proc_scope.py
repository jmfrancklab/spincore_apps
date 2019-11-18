from pyspecdata import *
fl = figlist_var()
def convert_to_power(date, id_string):
    return
for date,id_string in [
    ('190201','pulses_1'),
    ('190201','pulses_2'),
    ]:
    filename = date+'_'+id_string+'.h5'
    nodename = 'accumulated_'+date
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    s = s['ch',0].C
    s.reorder('t',first=False)
    fl.next(id_string+'raw signal')
    fl.image(s)
    #fl.plot(s,alpha=0.4)
    #s.ft('t',shift=True)
    #s = s['t':(0,None)]
    #s['t':(0,0.5e6)] = 0
    #s['t':(28e6,None)] = 0
    #s.ift('t')
    #fl.next(id_string+'abs filtered analytic signal')
    #fl.plot(abs(s*2),alpha=0.4)
    #fl.next(id_string+'sum')
    #if id_string == 'pulses_1':
    #    fl.plot(abs(s['t':(4e-6,6e-6)]).sum('t'),'o')
    #elif id_string == 'pulses_2':
    #    fl.plot(abs(s['t':(5e-6,20e-6)]).sum('t'),'o')
fl.show();quit()
