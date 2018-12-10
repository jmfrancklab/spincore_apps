%module ppg
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
def load(args):
    for a_tuple in args:
        ppg_element(*a_tuple)
%}
