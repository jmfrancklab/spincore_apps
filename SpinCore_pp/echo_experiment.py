import sys
from echo_experiment_ui import Ui_MainWindow
import subprocess

from PyQt5 import QtWidgets

from pyspecdata import *
import os
import sys
import SpinCore_pp

class mywindow(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(mywindow,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.run_adcoffset)
        self.ui.pushButton_2.clicked.connect(self.run_Hahn_echo)
        self.ui.pushButton_3.clicked.connect(self.takeFT)
        self.ui.pushButton_4.clicked.connect(self.save_file)
        self.ui.adcoffset = None
        self.ui.data = None
        self.ui.filename = None
    def run_adcoffset(self):
        adc_val = (subprocess.check_output("../adc_offset.exe").split()[-1])
        self.ui.adcoffset = adc_val
        self.ui.textEdit.setText(adc_val)
    def takeFT(self):
        self.ui.f_widget.canvas.ax.plot(self.ui.data.getaxis('t'),self.ui.data.data.real,alpha=0.4)
        self.ui.f_widget.canvas.draw()
    def get_filename(self):
        text,ok = QtWidgets.QInputDialog.getText(self,"Filename input dialog","Enter desired file name:")
        if ok:
            self.ui.filename = str(text)
    def save_file(self):
        self.get_filename()
        try:
            print "SAVING FILE..."
            self.ui.data.hdf5_write(self.ui.filename+'.h5')
            print "FILE SAVED!"
        except Exception as e:
            print e
            print "EXCEPTION ERROR - FILE ALREADY EXISTS."
            buttonReply = QtWidgets.QMessageBox.question(self,"File Already Exists","Rename and try again?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if buttonReply == QtWidgets.QMessageBox.Yes:
                print('Yes clicked')
                self.save_file()
            if buttonReply == QtWidgets.QMessageBox.No:
                print('No clicked. Exiting...')
            if buttonReply == QtWidgets.QMessageBox.Cancel:
                print('Exiting..')

    def run_Hahn_echo(self):
        #{{{ Verify arguments compatible with board
        def verifyParams():
            if (nPoints > 16*1024 or nPoints < 1):
                print "ERROR: MAXIMUM NUMBER OF POINTS IS 16384."
                print "EXITING."
                quit()
            else:
                print "VERIFIED NUMBER OF POINTS."
            if (nScans < 1):
                print "ERROR: THERE MUST BE AT LEAST 1 SCAN."
                print "EXITING."
                quit()
            else:
                print "VERIFIED NUMBER OF SCANS."
            if (p90 < 0.065):
                print "ERROR: PULSE TIME TOO SMALL."
                print "EXITING."
                quit()
            else:
                print "VERIFIED PULSE TIME."
            if (tau < 0.065):
                print "ERROR: DELAY TIME TOO SMALL."
                print "EXITING."
                quit()
            else:
                print "VERIFIED DELAY TIME."
            return
        #}}}
        date = '200226'
        output_name = 'echo_1'
        adcOffset = int(self.ui.adcoffset)
        carrierFreq_MHz = 14.898564
        tx_phases = r_[0.0,90.0,180.0,270.0]
        amplitude = 1.0
        nScans = 1
        nEchoes = 1
        phase_cycling = False
        if phase_cycling:
            nPhaseSteps = 8
        if not phase_cycling:
            nPhaseSteps = 1
        #{{{ note on timing
        # putting all times in microseconds
        # as this is generally what the SpinCore takes
        # note that acq_time is always milliseconds
        #}}}
        p90 = 3.3
        deadtime = 5.0
        repetition = 1e6

        SW_kHz = 24
        nPoints = 1024*2

        acq_time = nPoints/SW_kHz # ms
        tau_adjust = 0.0
        deblank = 1.0
        tau = deadtime + acq_time*1e3*(1./8.) + tau_adjust
        pad = 0
        #pad = 2.0*tau - deadtime - acq_time*1e3 - deblank
        #{{{ setting acq_params dictionary
        acq_params = {}
        acq_params['adcOffset'] = adcOffset
        acq_params['carrierFreq_MHz'] = carrierFreq_MHz
        acq_params['amplitude'] = amplitude
        acq_params['nScans'] = nScans
        acq_params['nEchoes'] = nEchoes
        acq_params['p90_us'] = p90
        acq_params['deadtime_us'] = deadtime
        acq_params['repetition_us'] = repetition
        acq_params['SW_kHz'] = SW_kHz
        acq_params['nPoints'] = nPoints
        acq_params['tau_adjust_us'] = tau_adjust
        acq_params['deblank_us'] = deblank
        acq_params['tau_us'] = tau
        acq_params['pad_us'] = pad 
        if phase_cycling:
            acq_params['nPhaseSteps'] = nPhaseSteps
        #}}}
        print "ACQUISITION TIME:",acq_time,"ms"
        print "TAU DELAY:",tau,"us"
        print "PAD DELAY:",pad,"us"
        data_length = 2*nPoints*nEchoes*nPhaseSteps
        for x in xrange(nScans):
            print "*** *** *** SCAN NO. %d *** *** ***"%(x+1)
            print "\n*** *** ***\n"
            print "CONFIGURING TRANSMITTER..."
            SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
            print "\nTRANSMITTER CONFIGURED."
            print "***"
            print "CONFIGURING RECEIVER..."
            acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, 1, nEchoes, nPhaseSteps)
            acq_params['acq_time_ms'] = acq_time
            # acq_time is in msec!
            print "ACQUISITION TIME IS",acq_time,"ms"
            verifyParams()
            print "\nRECEIVER CONFIGURED."
            print "***"
            print "\nINITIALIZING PROG BOARD...\n"
            SpinCore_pp.init_ppg();
            print "PROGRAMMING BOARD..."
            print "\nLOADING PULSE PROG...\n"
            if phase_cycling:
                SpinCore_pp.load([
                    ('marker','start',1),
                    ('phase_reset',1),
                    ('delay_TTL',deblank),
                    ('pulse_TTL',p90,'ph1',r_[0,1,2,3]),
                    ('delay',tau),
                    ('delay_TTL',deblank),
                    ('pulse_TTL',2.0*p90,'ph2',r_[0,2]),
                    ('delay',deadtime),
                    ('acquire',acq_time),
                    #('delay',pad),
                    ('delay',repetition),
                    ('jumpto','start')
                    ])
            if not phase_cycling:
                SpinCore_pp.load([
                    ('marker','start',1),
                    ('phase_reset',1),
                    ('delay_TTL',deblank),
                    ('pulse_TTL',p90,0.0),
                    ('delay',tau),
                    ('delay_TTL',deblank),
                    ('pulse_TTL',2.0*p90,0.0),
                    ('delay',deadtime),
                    ('acquire',acq_time),
                    #('delay',pad),
                    ('delay',repetition),
                    ('jumpto','start')
                    ])
            print "\nSTOPPING PROG BOARD...\n"
            SpinCore_pp.stop_ppg();
            print "\nRUNNING BOARD...\n"
            SpinCore_pp.runBoard();
            raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
            raw_data.astype(float)
            data_array = []
            data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
            print "COMPLEX DATA ARRAY LENGTH:",shape(data_array)[0]
            print "RAW DATA ARRAY LENGTH:",shape(raw_data)[0]
            dataPoints = float(shape(data_array)[0])
            if x == 0:
                time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
                data = ndshape([len(data_array),nScans],['t','nScans']).alloc(dtype=complex128)
                data.setaxis('t',time_axis).set_units('t','s')
                data.setaxis('nScans',r_[0:nScans])
                data.name('signal')
                data.set_prop('acq_params',acq_params)
            data['nScans',x] = data_array
            SpinCore_pp.stopBoard();
        print "EXITING..."
        print "\n*** *** ***\n"
        save_file = True
        while save_file:
            try:
                print "SAVING FILE..."
                data.hdf5_write(date+'_'+output_name+'.h5')
                print "FILE SAVED!"
                print "Name of saved data",data.name()
                print "Units of saved data",data.get_units('t')
                print "Shape of saved data",ndshape(data)
                save_file = False
            except Exception as e:
                print e
                print "EXCEPTION ERROR - FILE MAY ALREADY EXIST."
                save_file = False
                #}}}
        self.ui.time_plot.canvas.ax.plot(data.getaxis('t'),data.data,alpha=0.4)
        self.ui.time_plot.canvas.draw()
        data.ft('t',shift=True)
        self.ui.xaxis = data.getaxis('t')
        self.ui.yaxis = data.data
        self.ui.data = data


app = QtWidgets.QApplication([])
application = mywindow()
application.show()

sys.exit(app.exec_())
