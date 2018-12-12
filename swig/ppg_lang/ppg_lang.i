%module ppg_lang
%{
extern int ppg_element(char *str_label, double firstarg, double secondarg);
extern char *exception_info();
%}
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
marker_names = {}
from numpy import *
def apply_cycles(ppg_in,list_of_cycles_found):
    pulse_cycles = []
    found_cycle = False
    for cycled_idx, ppg_element in enumerate(ppg_in):
        if (len(ppg_element)>3) and (ppg_element[0] == 'pulse') and (type(ppg_element[2]) is str):
            cycle_name = ppg_element[2]
            found_cycle = True
            break
    if found_cycle:
        print "found phase cycle named",cycle_name
        all_cycles = [ppg_element[3] for ppg_element in ppg_in if ((ppg_element[0] == 'pulse' and ppg_element[2] == cycle_name) if len(ppg_element)>3 else False )]
        maxlen = max(map(len,all_cycles))
        list_of_cycles_found = [(cycle_name,maxlen)] + list(list_of_cycles_found)
        print "LIST OF CYCLES FOUND NOW",list_of_cycles_found
        print "ALL CYCLES ARE",all_cycles,"WITH MAX LEN",maxlen
        ppg_out = []
        for j in xrange(maxlen):
            for k,ppg_elem in enumerate(ppg_in):
                if len(ppg_elem) > 3 and ppg_elem[2] == cycle_name:
                    elem_copy = list(ppg_elem)
                    spec_len = len(elem_copy[3])
                    c_idx = j % spec_len
                    ppg_out.append(tuple(elem_copy[:2]+[elem_copy[3][c_idx]]))
                else:
                    ppg_out.append(ppg_elem)
        del ppg_in
        print "***"
        print "AFTER CYCLING:\n",'\n'.join(map(str,ppg_out))
        return apply_cycles(ppg_out,list_of_cycles_found)
    else:
        print "***"
        print "FOUND NO CYCLING ELEMENTS"
        return ppg_in,list_of_cycles_found
def load(args):
    ppg_list = []
    for a_tuple in args:
        print "READING NEXT TUPLE"
        if a_tuple[0] == 'marker':
            a_tuple = list(a_tuple)
            marker_idx = len(marker_names)
            print "for marker, converting name",a_tuple[1].upper(),"to index",marker_idx
            marker_names[a_tuple[1]] = marker_idx 
            a_tuple[1] = marker_idx
            a_tuple = tuple(a_tuple)
        elif a_tuple[0] == 'jumpto':
            a_tuple = list(a_tuple)
            marker_idx = marker_names[a_tuple[1]]
            print "for jump, converting name",a_tuple[1].upper(),"to index",marker_idx
            a_tuple[1] = marker_idx
            a_tuple = tuple(a_tuple)
        ppg_list.append(a_tuple)
    print ppg_list
    ppg_list,list_of_cycles_found = apply_cycles(ppg_list,[])
    for a_tuple in ppg_list:
        ppg_element(*a_tuple)
%}
