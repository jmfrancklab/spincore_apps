from pyspecdata import *
from scipy.optimize import leastsq
fl = figlist_var()
for date,id_string in [
        ('181214','Hahn_echo_1'),
        ('181214','Hahn_echo_2'),
        ('181214','Hahn_echo_3')
        ]:
    nPoints = 128
    nScans = 4
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    is_Nutation = False
    #{{{ for nutation data
    if is_Nutation:
        fl.next('raw data pull')
        fl.plot(s.real,alpha=0.5,label='real')
        fl.plot(s.imag,alpha=0.5,label='imag')
        fl.next('raw data, abs')
        fl.plot(abs(s))
        #{{{ Try to phase
        phase = True
        if phase:
            s.ft('t',shift=True)
            ph_corr = exp(1j*2*pi*0.29)
            s *= ph_corr
            s.ift('t')
            fl.next('phased data')
            fl.plot(s.real,alpha=0.5,label='real')
            fl.plot(s.imag,alpha=0.5,label='imag')
        #}}}
        t_axis = s.getaxis('t')
        s.setaxis('t',None)
        s.chunk('t',['PW','t2'],[nPoints_Nutation,nPoints])
        t2_axis = t_axis[0:int(nPoints)]
        PW_axis = []
        for x in xrange(nPoints_Nutation):
            print x
            temp = p90Time_us*x*1e-6
            PW_axis.append(temp)
        print PW_axis
        s.setaxis('t2',t2_axis).set_units('t2','s')
        s.setaxis('PW',PW_axis).set_units('PW','s')
        s.reorder('t2',first=False)
        fl.next('image nutation, abs')
        fl.image(abs(s))
        fl.next('image nutation')
        fl.image(s)
        fl.show();quit()
        fl.next('Plotting nutation')
        fl.plot(abs(s))
        s.ft('t',shift=True)
        fl.next('F plot')
        fl.plot(s)
        s *= exp(1j*2*pi*pi*1.01)
        s = s['t':(-5e3,5e3)]
        s.ift('t')
        fl.next('Filtered')
        fl.plot(s.real)
        fl.plot(s.imag)
        fl.show();quit()
        #}}}
    #fl.next(id_string+' raw data')
    #fl.plot(s.real,alpha=0.4)
    #fl.plot(s.imag,alpha=0.4)
    s.ft('t',shift=True)
    #s *= exp(1j*(pi/2.0))
    s.ift('t')
    #fl.next(id_string+' proc data')
    #fl.plot(s.real,alpha=0.4)
    #fl.plot(s.imag,alpha=0.4)
    print ndshape(s)
    t2_axis = linspace(0,s.getaxis('t')[nPoints],nPoints)
    nIndirect = shape(s.getaxis('t'))[0]/nPoints
    s.setaxis('t',None)
    s.chunk('t',['indirect','t2'],[nIndirect,-1])
    s.setaxis('indirect',r_[1:nIndirect+1])
    s.setaxis('t2',t2_axis)
    fl.next(id_string+' raw data, indirect chunk - abs')
    fl.image(abs(s))
    ##fl.next(id_string+' raw data, indirect chunk - real')
    ##fl.image(s.real)
    ##fl.next(id_string+' raw data, indirect chunk - imag')
    ##fl.image(s.imag)
    s.setaxis('indirect',None)
    s.chunk('indirect',['indirect','nScans'],[-1,nScans])
    print ndshape(s)
    s.chunk('indirect',['ph2','ph1'],[2,4])
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    s.setaxis('ph2',r_[0.,2.]/4)
    s.setaxis('nScans',r_[1.:float(nScans)+1.0])
    #fl.next(id_string+' ph cyc data, indirect chunk - abs')
    #fl.image(abs(s))
    #fl.next(id_string+' ph cyc data, indirect chunk - real')
    #fl.image(s.real)
    #fl.next(id_string+' ph cyc data, indirect chunk - imag')
    #fl.image(s.imag)
    print ndshape(s)
    #s.reorder(['nScans','t2'],first=False)
    s.ft(['ph2','ph1'])
    fl.next(id_string+' image plot coherence')
    fl.image(s)
    #fl.next(id_string+' image plot coherence zoomed')
    #fl.image(s['t2':(5e-3,15e-3)])
    #s.ft('t2', shift=True)
    #s.ift('t2')
    #fl.next(id_string+' signal')
    #fl.plot(s['ph1',1]['ph2',0]['t2':(9.4e-3,10.6e-3)],label='real')
    #fl.plot(s.imag['ph1',1]['ph2',0]['t2':(9.4e-3,10.6e-3)],label='imag')
fl.show();quit()
