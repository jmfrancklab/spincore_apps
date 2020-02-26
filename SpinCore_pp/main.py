from PyQt5 import QtWidgets
import sys

import app_framework as af

app = QtWidgets.QApplication(sys.argv)
form = af.MyApp()
form.show()
app.exec_()
