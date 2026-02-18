import sys
import os
from keithley2600 import Keithley2600
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPalette, QColor, QFont, QRegExpValidator
from PyQt5.QtCore import Qt, QRegExp
from PSWindow import PSWindow

# design color palette (dark fusion)
dark_palette = QPalette()  # naming the palette dark_palette
dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))  # setting window color
dark_palette.setColor(QPalette.WindowText, Qt.white)  # setting window text color
dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))  # setting base color (text edit background ect.)
dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))  # setting alternate base color (for alternating backgrounds ect.)
dark_palette.setColor(QPalette.ToolTipBase, Qt.white)  # setting background color for tooltips
dark_palette.setColor(QPalette.ToolTipText, Qt.white)  # setting text color for tooltips
dark_palette.setColor(QPalette.Text, Qt.white)  # setting window text color
dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))  # setting button color
dark_palette.setColor(QPalette.ButtonText, Qt.white)  # setting button text color
dark_palette.setColor(QPalette.BrightText, Qt.red)  # setting bright text color for better contrasts
dark_palette.setColor(QPalette.Link, QColor(42, 139, 218))  # setting hyperlink color
dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))  # setting color for selected item
dark_palette.setColor(QPalette.HighlightedText, Qt.black)  # setting highlight color text (contrasts highlight color)

# font styles
normal_font = QFont('Calibri', 12)  # defining the normal font used for most texts
big_font = QFont('Calibri', 24)  # defining the big font used to larger objects

# starting Window with measurement methods to choose from (photo current, PL, EL, EQE)
class StartWindow(QtWidgets.QWidget):
    def __init__(self):
        super(StartWindow, self).__init__()

        # starting Window design
        self.setWindowTitle('Welcome')  # setting window title
        self.start_window_layout = QtWidgets.QVBoxLayout()  # defining the window layout as a vertical box layout
        self.setLayout(self.start_window_layout)  # setting the layout as the previous defined one

        # Widgets on Window
        self.ps_button = QtWidgets.QPushButton(self)  # push button for photo current measurements
        self.ps_button.setFont(big_font)  # setting font for button to big font (photo current)
        self.pl_button = QtWidgets.QPushButton(self)  # push button for photo luminescence measurements
        self.pl_button.setFont(big_font)  # setting font for button to big font (photo luminescence)
        self.el_button = QtWidgets.QPushButton(self)  # push button for electro luminescence
        self.el_button.setFont(big_font)  # setting font for button to big font (electro luminescence)
        self.eqe_button = QtWidgets.QPushButton(self)  # push button for EQE measurement
        self.eqe_button.setFont(big_font)  # setting font for button to big font (EQE)
        self.cancel_button = QtWidgets.QPushButton('Press Ctrl + C', self)  # push button to cancel program
        self.cancel_button.setFont(normal_font)  # setting font on cancel button

        # Labels on Buttons
        self.ps_button.setText("Photo current")  # setting text on button (photo current)
        self.pl_button.setText("Photo luminescence ")  # setting text on button (photo luminescence)
        self.el_button.setText("Electro luminescence")  # setting text on button (electro luminescence)
        self.eqe_button.setText("EQE")  # setting text on button (EQE)
        self.cancel_button.setText("&Cancel")  # setting text on cancel button

        # Layout of window
        self.start_window_layout.addWidget(self.ps_button)  # adding photo current button to start window layout
        self.start_window_layout.addWidget(self.pl_button)  # adding photo luminescence button to start window layout
        self.start_window_layout.addWidget(self.el_button)  # adding electro luminescence button to start window layout
        self.start_window_layout.addWidget(self.eqe_button)  # adding eqe button to start window layout
        self.start_window_layout.addWidget(self.cancel_button)  # adding cancel button to start window layout
        self.start_window_layout.setSpacing(25)  # setting the spacing between objects
        self.start_window_layout.setContentsMargins(25, 25, 25, 25)  # setting margins in window layout

        # Events when buttons are pushed
        self.w = None  # giving variable w no defined value
        self.ps_button.clicked.connect(self.ps_button_clicked)  # connecting the photo current button to opening function when clicked
        self.cancel_button.clicked.connect(self.close)  # connecting the cancel button with closing function when clicked

    # Event when photo current button is clicked
    def ps_button_clicked(self):
        if self.w is None:  # variable w (window) is None
            self.w = PSWindow()  # the class of the photo current measurement window  will be assigned to variable w
            self.w.location_on_the_screen()
            self.w.show()  # showing variable w (photo current measurement window)
            self.hide()  # hide the start window
            self.w.keysight_control_check_changed()
        else:  # if variable w is not None
            self.w.close()  # close variable w (whatever is assigned to variable w)
            self.w = None  # set variable w to None

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setPalette(dark_palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
    ex = StartWindow()
    ex.show()
    sys.exit(app.exec_())

