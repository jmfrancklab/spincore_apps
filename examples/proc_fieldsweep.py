from pylab import *
from pyspecdata import *
from pyspecProcScripts import *
from sympy import symbols
fl = figlist_var()
signal_pathway = {'ph1':1}
for thisfile,exp_type,nodename,postproc,label_str in [
        ('220725_70mM_TEMPOL_field.h5',
            'ODNP_NMR_comp/field_dependent',
            'field_1',
            'TEMPOL field sweep')
        ]:
    s = find_file(thisfile,exp_type=exp_type,expno=nodename)
    #{{{Obtain ESR frequency and chunk/reorder dimensions
    nu_B12 = s.get_prop('acq_params')['mw_freqs']/1e9
    s.reorder(['ph1','indirect','t2'])
    #}}}
    #{{{DC offset correction
    s.ift('t2')
    s.ift(['ph1'])
    t2_max = s.getaxis('t2')[-1]
    rx_offset_corr = s['t2':(t2_max*0.75,None)]
    rx_offset_corr = rx_offset_corr.mean(['t2'])
    s -= rx_offset_corr
    fl.next('Time Domain')
    s.ft(['ph1'])
    fl.image(s['t2':(None,0.05)])
    s.ft('t2')
    #}}}
    fl.next('Frequency Domain')
    fl.image(s)
    #{{{frequency filtering and rough center
    s = s['t2':(-1.5e3,1.5e3)]
    s.ift('t2')
    s.set_units('t2','s')
    best_shift,cost_fun = hermitian_function_test(select_pathway(s.C,signal_pathway),
            echo_before =s.get_prop('acq_params')['tau_us']*1e-6*1.5,
            )
    actual_tau = IR.get_prop('acq_params')['tau_us']/1e6
    if (best_shift < actual_tau-1e-3) or (best_shift > actual_tau+1e-3):
            best_shift = hermitian_function_test(select_pathway(IR.C,
                IR_signal_pathway),
                echo_before=IR.get_prop('acq_params')['tau_us']*1e-6*1.5,
                fl=fl)
        best_shift = actual_tau
    s.setaxis('t2', lambda x: x-best_shift).register_axis({'t2':0})
    s /= zeroth_order_ph(select_pathway(s,signal_pathway))
    s = select_pathway(s,signal_pathway)
    s.ft('t2')
    nu_NMR=[]
    all_offsets = zeros(len(s.getaxis('indirect')))
    for z in range(len(s.getaxis('indirect'))):
        offset = s['indirect',z].C.mean('nScans').argmax('t2').item()
        all_offsets[z] = offset
        carrier_freq_MHz = s.getaxis('indirect')[z]['carrierFreq']
        nu_rf = carrier_freq_MHz - offset/1e6
        nu_NMR.append(nu_rf) 
    s.ift('t2')
    s *= exp(-1j*2*pi*nddata(all_offsets, [-1],['indirect'])*s.fromaxis('t2'))
    s.ft('t2')
    frq_slice = s.C.mean('nScans').mean('indirect').contiguous(lambda x: x.real > 0.15*s.real.data.max())[0]
    fl.next('Field Slicing')
    fl.plot(s.C.mean('nScans'))
    plt.axvline(x = frq_slice[0])
    plt.axvline(x = frq_slice[-1])
    s = s['t2':frq_slice].mean('nScans').integrate('t2')
    #}}}
    #{{{convert x axis to ppt = v_NMR/v_ESR
    ppt = np.asarray(nu_NMR) / np.asarray(nu_B12) 
    s.setaxis('indirect',ppt)
    s.rename('indirect','ppt')
    #}}}
    #{{{Fitting
    fl.next('fit')
    fl.plot(s,'o')
    fitting = s.polyfit('ppt',order=4)
    x_min = s.getaxis('ppt')[0]
    x_max = s.getaxis('ppt')[-1]
    Field = nddata(r_[x_min:x_max:100j],'ppt')
    fl.plot(Field.eval_poly(fitting,'ppt'),label='fit')
    #}}}
    print("ESR frequency is %f"%(nu_B12))
    print('The fit finds a max with ppt value:',
        Field.eval_poly(fitting,'ppt').argmax().item())
    print('The data finds a ppt value', abs(s).argmax().item())
fl.show()
