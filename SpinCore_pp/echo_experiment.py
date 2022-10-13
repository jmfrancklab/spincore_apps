import sys
from echo_experiment_ui import Ui_MainWindow
import subprocess
from PyQt5 import QtWidgets
from pyspecdata import *
import os
import sys
from datetime import datetime
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
        self.ui.pushButton_5.clicked.connect(self.open_acqparams)
        self.ui.adcoffset = None
        self.ui.data = None
        self.ui.filename = None
        self.ui.carrierFreq_MHz = None
    def run_adcoffset(self):
        adc_val = (subprocess.check_output("../adc_offset.exe").split()[-1])
        self.ui.adcoffset = adc_val
        self.ui.textEdit.setText(adc_val.decode('utf-8'))
    def takeFT(self):
        self.ui.f_widget.canvas.ax.plot(self.ui.data.getaxis('t'),self.ui.data.data.real)
        self.ui.f_widget.canvas.draw()
    def open_acqparams(self):
        layout = QtWidgets.QFormLayout()
        self.btn = QtWidgets.QPushButton("Params")
        self.btn.clicked.connect(None)

        self.le = QtWidgets.QLineEdit()
        layout.addRow(self.btn,self.le)
        self.btn1 = QtWidgets.QPushButton("Carrier Frequency:")
        self.btn1.clicked.connect(self.getCarrier())
    def getCarrier(self):
        text,ok = QtWidgets.QInputDialog.getText(self,"Input dialog","Enter desired carrier freq in MHz:")
        if ok:
            self.ui.carrierFreq_MHz = float(text)
    def get_filename(self):
        text,ok = QtWidgets.QInputDialog.getText(self,"Filename input dialog","Enter desired file name:")
        if ok:
            self.ui.filename = str(text)
    def save_file(self):
        self.get_filename()
        try:
            print("SAVING FILE...")
            self.ui.data.hdf5_write(self.ui.filename+'.h5')
            print("FILE SAVED!")
        except Exception as e:
            print(e)
            print("EXCEPTION ERROR - FILE ALREADY EXISTS.")
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
        config_dict=SpinCore_pp.configuration("active.ini")
        #}}}
        date = datetime.now().strftime("%y%m%d")
        config_dict['type'] = 'echo'
        output_name = f'{date}_{type}'
        adcOffset = int(self.ui.adcoffset)
        carrierFreq_MHz = config_dict['carrierFreq_MHz']
        tx_phases = r_[0.0,90.0,180.0,270.0]
        amplitude = config_dict['amplitude']
        nScans = config_dict['nScans']#128
        nEchoes = config_dict['nEchoes']
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
        nPoints = int(config_dict['acq_time_mw']*config_dict['SW_kHz']+0.5)
        tau_adjust = 0.0
        tau = config_dict['tau_us']
        data_length = 2*nPoints*config_dict['nEchoes']*nPhaseSteps
        for x in range(config_dict['nScans']):
            print("*** *** *** SCAN NO. %d *** *** ***"%(x+1))
            print("\n*** *** ***\n")
            print("CONFIGURING TRANSMITTER...")
            SpinCore_pp.configureTX(config_dict['adcOffset'], config_dict['carrierFreq_MHz'], 
                    tx_phases, config_dict['amplitude'], nPoints)
            print("\nTRANSMITTER CONFIGURED.")
            print("***")
            print("CONFIGURING RECEIVER...")
            acq_time = SpinCore_pp.configureRX(config_dict['SW_kHz'], nPoints, 1, 
                    config_dict['nEchoes'], nPhaseSteps)
            acq_params['acq_time_ms'] = config_dict['acq_time']
            # acq_time is in msec!
            print("ACQUISITION TIME IS",acq_time,"ms")
            print("\nRECEIVER CONFIGURED.")
            print("***")
            print("\nINITIALIZING PROG BOARD...\n")
            SpinCore_pp.init_ppg();
            print("PROGRAMMING BOARD...")
            print("\nLOADING PULSE PROG...\n")
            if phase_cycling:
                SpinCore_pp.load([
                    ('marker','start',1),
                    ('phase_reset',1),
                    ('delay_TTL',config_dict['deblank_us']),
                    ('pulse_TTL',config_dict['p90_us'],'ph1',r_[0,1,2,3]),
                    ('delay',config_dict['tau_us']),
                    ('delay_TTL',config_dict['deblank']),
                    ('pulse_TTL',2.0*config_dict['p90_us'],'ph2',r_[0,2]),
                    ('delay',config_dict['deadtime_us']),
                    ('acquire',config_dict['acq_time_ms']),
                    ('delay',config_dict['repetition_us']),
                    ('jumpto','start')
                    ])
            if not phase_cycling:
                SpinCore_pp.load([
                    ('marker','start',1),
                    ('phase_reset',1),
                    ('delay_TTL',config_dict['deblank_us']),
                    ('pulse_TTL',config_dict['p90_us'],0),
                    ('delay',config_dict['tau_us']),
                    ('delay_TTL',config_dict['deblank_us']),
                    ('pulse_TTL',2.0*config_dict['p90_us'],0),
                    ('delay',config_dict['deadtime_us']),
                    ('acquire',config_dict['acq_time_ms']),
                    ('delay',config_dict['repetition_us']),
                    ('jumpto','start')
                    ])
            print("\nSTOPPING PROG BOARD...\n")
            SpinCore_pp.stop_ppg();
            print("\nRUNNING BOARD...\n")
            SpinCore_pp.runBoard();
            raw_data = SpinCore_pp.getData(data_length, nPoints, config_dict['nEchoes'], nPhaseSteps)
            raw_data.astype(float)
            data_array = []
            data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
            print("COMPLEX DATA ARRAY LENGTH:",shape(data_array)[0])
            print("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
            dataPoints = float(shape(data_array)[0])
            if x == 0:
                time_axis = linspace(0.0,config_dict['nEchoes']*nPhaseSteps*config_dict['acq_time_ms']*1e-3,dataPoints)
                data = ndshape([len(data_array),config_dict['nScans']],['t','nScans']).alloc(dtype=complex128)
                data.setaxis('t',time_axis).set_units('t','s')
                data.setaxis('nScans',r_[0:config_dict['nScans']])
                data.name('signal')
                data.set_prop('acq_params',config_dict.asdict())
            data['nScans',x] = data_array
            SpinCore_pp.stopBoard();
        data.mean('nScans')
        print("EXITING...")
        print("\n*** *** ***\n")
        save_file = True
        while save_file:
            try:
                print("SAVING FILE...")
                data.hdf5_write(date+'_'+output_name+'.h5')
                print("FILE SAVED!")
                print("Name of saved data",data.name())
                print("Units of saved data",data.get_units('t'))
                print("Shape of saved data",ndshape(data))
                save_file = False
            except Exception as e:
                print(e)
                print("EXCEPTION ERROR - FILE MAY ALREADY EXIST.")
                save_file = False
                #}}}
        self.ui.time_plot.canvas.ax.plot(data.getaxis('t'),data.data)
        self.ui.time_plot.canvas.draw()
        data.ft('t',shift=True)
        self.ui.xaxis = data.getaxis('t')
        self.ui.yaxis = data.data
        self.ui.data = data
        config_dict.write()


app = QtWidgets.QApplication([])
application = mywindow()
application.show()

sys.exit(app.exec_())
