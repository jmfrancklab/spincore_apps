from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping
fl = figlist_var()
for date,id_string in [
        ('191007','echo_1'),
        ]:
    title_string = 'unenhanced'
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    print ndshape(s)
    nPoints = s.get_prop('acq_params')['nPoints']
    nEchoes = s.get_prop('acq_params')['nEchoes']
    nPhaseSteps = s.get_prop('acq_params')['nPhaseSteps']
    SW_kHz = s.get_prop('acq_params')['SW_kHz']
    s.set_units('t','s')
    orig_t = s.getaxis('t')
    acq_time_s = orig_t[nPoints]
    t2_axis = linspace(0,acq_time_s,nPoints)
    s.setaxis('t',None)
    s.reorder('t',first=True)
    s.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    s.setaxis('ph2',r_[0.,2.]/4)
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    s.setaxis('t2',t2_axis)
    s.reorder('t2',first=False)
    s.ft('t2',shift=True)
    s.ft(['ph1','ph2'])
    fl.next(id_string+'raw data - chunking coh')
    fl.image(s)
    s = s['ph1',1]['ph2',0].C
    s.setaxis('t2',s.getaxis('t2'))
    s.ift('t2')
    # Center the time-domain echo at t = 0
    t2_max = abs(s).argmax('t2',raw_index=True).data
    s.setaxis('t2',lambda t: t - s.getaxis('t2')[int(t2_max)])
    # Get rid of negative time points, and scale first time point appropriately
    s = s['t2':(0,None)]
    s['t2',0] *= 0.5
    fl.next('sliced')
    fl.plot(s)
    fl.next('Visualize sliced peak')
    fl.plot(s.C.ft('t2'),human_units=False)
    s.ft('t2')
    df = diff(s.getaxis('t2')[r_[0,1]])[0]
    max_hwidth = 6
    window_hwidth = 5
    max_shift = (max_hwidth - window_hwidth)*df
    center_index = where(abs(s.getaxis('t2'))==abs(s.getaxis('t2')).min())[0][0]
    print center_index
    slice_ = s['t2',int(center_index-max_hwidth) : int(center_index+max_hwidth+1)].C
    slice_center_index = where(abs(slice_.getaxis('t2'))==abs(slice_.getaxis('t2')).min())[0][0]
    fl.plot(slice_,':',human_units=False)
    print slice_center_index
    f_axis = slice_.fromaxis('t2')
    temp = s.C
    def hermitian_costfunc(p):
        zerorder_rad,firstorder = p
        phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
        phshift *= exp(-1j*2*pi*zerorder_rad)
        temp = phshift * slice_
        deviation = temp['t2',slice_center_index - window_hwidth:slice_center_index+window_hwidth+1].C
        deviation -= deviation['t2',::-1].C.run(conj)
        return (abs(deviation.data)**2)[:].sum()

    iteration = 0

    def print_func(x,f,accepted):
        global iteration
        print(iteration,x,int(accepted))
        iteration = iteration+1

    sol = basinhopping(hermitian_costfunc, r_[0.,0.],
            minimizer_kwargs={"method":'L-BFGS-B'},
            callback=print_func,
            stepsize=100.,
            niter=25,
            T=1000.
            )
    zerorder_rad,firstorder = sol.x
    f_axis = s.getaxis('t2')
    phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
    phshift *= exp(-1j*2*pi*zerorder_rad)

    s *= phshift

    #fl.next('freq, phased')
    fl.plot(s,c='black',alpha=0.8,human_units=False)
       
    fl.show();quit()
    center_index = where(abs(s.getaxis('t2'))==abs(temp.getaxis('t2')).min())[0][0]

    fl.show();quit()
    df = diff(s.getaxis('t2')[r_[0,1]])[0]
    #max_hwidth = 
    s.ft('t2')
    fl.next('freq-signal '+title_string)
    fl.plot(s.real,alpha=0.7,label='real')
    fl.plot(s.imag,alpha=0.7,label='imag')
    fl.plot(abs(s),':')
    s.ift('t2')
    fl.next('time-signal '+title_string)
    fl.plot(s.real,alpha=0.7,label='real')
    fl.plot(s.imag,alpha=0.7,label='imag')
    fl.plot(abs(s),':')
fl.show()
