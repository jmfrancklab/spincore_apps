from pyspecdata import *
from scipy.optimize import leastsq
fl = figlist_var()
for date,id_string in [
        ('181121','CPMG_5'),
        #('181121','nutation_10'),
        ]:
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    with open(getDATADIR(exp_type='test_equip')+date+'_'+id_string+'_params.txt', "r") as F:
        for line in F:
            if 'nPoints=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                nPoints = float(temp[1])
            if 'nEchoes=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                nEchoes = float(temp[1])
            if 'nPoints_Nutation=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                nPoints_Nutation = int(temp[1])
            if 'tauDelay_us=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                tauDelay_us = float(temp[1])
            if 'nScans=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                nScans = int(temp[1])
            if 'nutation_step=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                nutation_step = float(temp[1])
            if 'p90Time_us=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                p90Time_us = float(temp[1])
    label=r'$\tau$=%0.1f ms'%(tauDelay_us/1e3)
    is_Nutation = False
    if 'nutation' in id_string:
        is_Nutation = True
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
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
    #fl.next('SpinCore Spin Echo, %d scan(s)'%nScans)
    s.ft('t',shift=True)
    s *= exp(1j*2*pi*0.3)
    s.ift('t')
    fl.next('CPMG')
    fl.plot(s.real,alpha=0.4,c='r',label='real')
    fl.plot(s.imag,alpha=0.4,c='blue',label='imag')
    fl.next('CPMG, abs')
    fl.plot(abs(s),alpha=0.4)
    with open(getDATADIR(exp_type='test_equip')+date+'_'+id_string+'.txt', "r") as F:
        for line in F:
            temp = line.strip().split()
            if temp[0] == 'SPECTRAL':
                SW = float(temp[-1])
        F.close()
    indirect_points = nEchoes
    indirect_acq_time = nPoints/SW
    indirect_dt = indirect_acq_time/indirect_points
    indirect_time_axis = linspace(0.0,indirect_acq_time,nPoints)
    print ndshape(s)
    CPMG_data = s.C
    CPMG_data.setaxis('t',None)
    CPMG_data.chunk('t',['echo','t2'],[int(indirect_points),len(indirect_time_axis)])
    CPMG_data.setaxis('echo',r_[0:indirect_points:1])
    CPMG_data.setaxis('t2',indirect_time_axis).set_units('t2','s')
    print ndshape(CPMG_data)
    fl.next('image CPMG')
    fl.image(CPMG_data)
    even_echo = ndshape([len(r_[0:indirect_points/2.0:1]),len(indirect_time_axis)],
            ['echo','t2']).alloc(dtype=complex128)
    odd_echo = ndshape([len(r_[0:indirect_points/2.0:1]),len(indirect_time_axis)],
            ['echo','t2']).alloc(dtype=complex128)
    even_echo.setaxis('echo',r_[0:indirect_points/2.0:1])
    even_echo.setaxis('t2',indirect_time_axis).set_units('t2','s')
    odd_echo.setaxis('echo',r_[0:indirect_points/2.0:1])
    odd_echo.setaxis('t2',indirect_time_axis).set_units('t2','s')
    print ndshape(even_echo)
    print ndshape(odd_echo)
    for index,echo_count in enumerate(r_[0:int(indirect_points):2]):
        even_echo['echo',index] = CPMG_data['echo',echo_count].C
        odd_echo['echo',index] = CPMG_data['echo',echo_count+1].C
    fl.next('image CPMG, even echo')
    fl.image(even_echo)
    fl.next('image CPMG, odd echo')
    fl.image(odd_echo)
    x = even_echo.getaxis('echo')
    even_echo.sum('t2')
    odd_echo.sum('t2')
    fl.next('CPMG, even echo')
    fl.plot(even_echo,'.')
    fl.next('CPMG, odd echo')
    fl.plot(odd_echo,'.')
    #x = CPMG_data.getaxis('echo')
    CPMG_data.sum('t2')
    max_val = amax(abs(even_echo).data)
    avg_min = abs(even_echo['echo':(10,-1)]).data.mean()
    print avg_min
    #even_echo /= amax(abs(even_echo).data)
    #min_val = amin(abs(even_echo).data)
    #ydata = (abs(even_echo).data) - min_val
    ydata_abs = (abs(even_echo).data) - avg_min
    ydata = ((even_echo).data) - avg_min
    print shape(ydata)
    new_y = []
    for x in r_[0:len(ydata):1]:
        print x
        if 3 < x < 5:
            print "Rejecting"
        else:
            new_y.append(ydata[x])
    fl.next('CPMG, only even echoes')
    fl.plot(x, ydata_abs,'.', label='data', human_units=False)
    fitfunc = lambda p, x: p[0]*exp(-1*x/p[1])-p[2]
    fl.plot(x, fitfunc(r_[max_val,0.1,avg_min],x), ':', label='initial fit', human_units=False)
    errfunc = lambda p_arg, x_arg, y_arg: fitfunc(p_arg, x_arg) - y_arg
    p0 = [max_val,0.2,avg_min]
    p1, success = leastsq(errfunc, p0[:], args=(x, ydata_abs))
    x_fit = linspace(x.min(), x.max(), 5000)
    fl.plot(x_fit, fitfunc(p1, x_fit), ':', c='k', label='final fit, T2=%f'%p1[1])
    print p0
    print p1
    fitfunc2 = lambda q, x: p1[0]*exp(-1*x/q[0])-p1[2]
    fl.plot(x, fitfunc2([0.2],x), ':', label='fit 2', human_units=False)
    errfunc2 = lambda q_arg, x_arg, y_arg: fitfunc2(q_arg, x_arg) - y_arg
    q0 = [0.2]
    q1, success = leastsq(errfunc2, q0[:], args=(x, ydata_abs))
    x_fit = linspace(x.min(), x.max(), 5000)
    fl.plot(x_fit, fitfunc(p1, x_fit), ':', label='second fit, T2=%f'%q1[0])

    fl.show();quit()
fl.show()
