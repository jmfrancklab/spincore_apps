from PyQt5 import QtWidgets
from adc_offset_ui import Ui_MainWindow
import sys
import subprocess

class mywindow(QtWidgets.QMainWindow):
    def run_adcoffset(self):
        adc_val = (subprocess.check_output("adc_offset.exe").split()[-1])
        self.ui.textEdit.setText(adc_val)
    def __init__(self):
        super(mywindow,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.run_adcoffset)

app = QtWidgets.QApplication([])
application = mywindow()
application.show()

sys.exit(app.exec_())
