import sys
#from echo_experiment_ui import Ui_MainWindow
import echo_experiment_ui
import subprocess

from PyQt5 import QtWidgets

class mywindow(QtWidgets.QMainWindow,echo_experiment_ui.Ui_MainWindow):
    def __init__(self):
        super(mywindow,self).__init__()
        self.ui = echo_experiment_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.openPlot)
    def run_adcoffset(self):
        adc_val = (subprocess.check_output("../adc_offset.exe").split()[-1])
        self.ui.textEdit.setText(adc_val)
        return adc_val
    def openPlot(self):
        x=range(0,10)
        y=range(0,20,2)
        self.plotWidget.canvas.ax.plot(x,y)
        self.plotWidget.canvas.draw()

app = QtWidgets.QApplication([])
application = mywindow()
application.show()

sys.exit(app.exec_())
