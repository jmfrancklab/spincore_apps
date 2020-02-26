from PyQt5.QtWidgets import QApplication,QMainWindow
import echo_experiment_ui
import subprocess
import sys

class MyApp(QMainWindow,echo_experiment_ui.Ui_MainWindow):
    def __init__(self):
        super(self.__class__,self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.openPlot)
    def run_adcoffset(self):
        adc_val = (subprocess.check_output("../adc_offset.exe").split()[-1])
        self.textEdit.setText(adc_val)
        return adc_val
    def openPlot(self):
        x=range(0,10)
        y=range(0,20,2)
        self.plotWidget.canvas.ax.plot(x,y)
        self.plotWidget.canvas.draw()

