%module ppg_temp
%{

extern char *get_time();
extern void pause(void);
extern int configureTX(int adcOffset, double carrierFreq_MHz, double tx_phase, double amplitude, unsigned int nPoints);
extern int init_ppg();
extern int stop_ppg();
extern int ppg_element(char *str_label, double firstarg, double secondarg);
extern char *exception_info();
extern int runBoard();
%}
extern char *get_time();
extern void pause(void);
extern int configureTX(int adcOffset, double carrierFreq_MHz, double tx_phase, double amplitude, unsigned int nPoints);
extern int init_ppg();
extern int stop_ppg();
%exception ppg_element{
    $action
    if (result){
        PyErr_SetString(PyExc_ValueError,exception_info());
        return NULL;
    }
}
%varargs(double secondarg=0) ppg_element;
extern int ppg_element(char *str_label, double firstarg, ...);
%pythoncode %{
# logger should work, but not tested
import logging
logger = logging.getLogger(__name__)
marker_names = {}
def loginfo(*args):# for logger
    # doesn't do anything unless you set up a logger (preferred)
    logger.info(' '.join(map(str,args)))
    # your you can hack it:
    #print (' '.join(map(str,args)))
def apply_cycles(ppg_in,list_of_cycles_found):
    """Recursively apply the phase cycles indicated by elements with tuple form
    ``('pulse',length,cyclename,cycle)``
    where ``cyclename`` is a string and ``cycle`` is a numpy array.

    Assume a list like 0, 90, 180, 270 has been loaded into the phase registers.

    All pulses with the same ``cyclename`` are cycled together.

    Though it's not a useful pulse sequence, this should demonstrate the functionality:

    >>> ppg_list = [('pulse',10,'ph1',r_[0,1,2,3]),
    >>>             ('delay',20),
    >>>             ('pulse',10,'ph1',r_[0,1]),
    >>>             ('delay',10),
    >>>             ('pulse',10,'ph2',r_[0,2]),
    >>>             ('acq',0.5e6)]

    Returns
    -------
    ppg_out: list of tuples
        New pulse program with the phase cycle applied.
    list_of_cycles_found: list of tuples
        List of cycles found that could be used to reshape the data.
        The list is given outside in, so that it's in the right order.
    """
    pulse_cycles = []
    found_cycle = False
    for cycled_idx, ppg_element in enumerate(ppg_in):
        if (len(ppg_element)>3) and (ppg_element[0] == 'pulse' and type(ppg_element[2]) is str and type(ppg_element[3]) is ndarray):
            cycle_name = ppg_element[2]
            found_cycle = True
            break
    if found_cycle:
        loginfo("found phase cycle named",cycle_name)
        # {{{ in case multiple pulses are cycling together, pull all the cycles
        all_cycles = [ppg_element[3] for ppg_element in ppg_in
                if ((ppg_element[0] == 'pulse' and ppg_element[2] == cycle_name and type(ppg_element[3]) is ndarray) if len(ppg_element)>3 else False)]
        maxlen = max(map(len,all_cycles))
        list_of_cycles_found = [(cycle_name,maxlen)] + list(list_of_cycles_found) # cycles applied later are outside, and come first
        loginfo("list of cycles found now",list_of_cycles_found)
        loginfo("all cycles are",all_cycles,"with max len",maxlen)
        # }}}
        # {{{ replace with instances of the phase cycle, and stack on top of each other
        ppg_out = []
        for j in range(maxlen):# over the length of the phase cycle (determined by the max length of each cycle given)
            for k,ppg_elem in enumerate(ppg_in):
                if len(ppg_elem) > 3 and ppg_elem[2] == cycle_name:
                    elem_copy = list(ppg_elem)
                    spec_len = len(elem_copy[3])
                    c_idx = j % spec_len # if phase cycles are different lengths, assume they are cyclical
                    ppg_out.append(tuple(elem_copy[:2] + [elem_copy[3][c_idx]]))
                else:
                    ppg_out.append(ppg_elem)
        # }}}
        del ppg_in
        loginfo("after cycling:\n",'\n'.join(map(str,ppg_out)))
        return apply_cycles(ppg_out,list_of_cycles_found)
    else:
        loginfo("found no cycled elements")
        return ppg_in,list_of_cycles_found
def load(args):
    ppg_list = []
    for a_tuple in args:
        if a_tuple[0] == 'marker':
            a_tuple = list(a_tuple)
            marker_idx = len(marker_names)
            print "for marker, converting name",a_tuple[1],"to index",marker_idx
            marker_names[a_tuple[1]] = marker_idx
            a_tuple[1] = marker_idx
            a_tuple = tuple(a_tuple)
        elif a_tuple[0] == 'jumpto':
            a_tuple = list(a_tuple)
            marker_idx = marker_names[a_tuple[1]]
            print "for jump, converting name",a_tuple[1],"to index",marker_idx
            a_tuple[1] = marker_idx
            a_tuple = tuple(a_tuple)
        ppg_list.append(a_tuple)
    ppg_list,list_of_cycles_found = apply_cycles(ppg_list,[])
    for a_tuple in ppg_list:
        ppg_element(*a_tuple)
%}
extern int runBoard();
