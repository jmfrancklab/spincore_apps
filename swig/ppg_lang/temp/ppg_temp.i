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
marker_names = {}
def load(args):
    for a_tuple in args:
        if a_tuple[0] == 'marker':
            a_tuple = list(a_tuple)
            marker_names[a_tuple[1]] = len(marker_names)
            a_tuple[1] = len(marker_names)-1
        elif a_tuple[0] == 'jumpto':
            a_tuple = list(a_tuple)
            a_tuple[1] = marker_names[a_tuple[1]]
        ppg_element(*a_tuple)
%}
extern int runBoard();
