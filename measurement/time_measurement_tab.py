from PyQt5 import QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import QRegExp, QThread, pyqtSignal
import pyqtgraph as pg
import time
import numpy as np
import os

class setup_time_tab():
    def __init__(self, parent):
        self.parent = parent # PSWindow, to have have connections to its methods and buttons
        self.count = 0  # count for the number of times the measurement has been run
        self.file_header = ''
        self.wavelength_txt = parent.wavelength_txt
        # validators
        self.validator1 = QRegExpValidator(QRegExp(r'[+-]?([0-9]+[.,])?[0-9]+'))  # defining validator 1: every positive and negative float number
        self.validator2 = QRegExpValidator(QRegExp(r'([0-9]+[.,])?[0-9]+'))  # defining validator 2: every positive float number
        # font styles
        normal_font = QFont('Calibri', 12)  # defining the normal font used for most texts
        big_font = QFont('Calibri', 24)  # defining the big font used to larger objects

        # Layout style of the tab
        layout = QtWidgets.QGridLayout()
        # Widgets on window
        #  Voltage
        self.time_v_lbl = QtWidgets.QLabel("Voltage in [V]:")
        self.time_v_lbl.setFont(normal_font)
        self.time_v_txt = QtWidgets.QLineEdit()
        self.time_v_txt.setFont(normal_font)
        self.time_v_txt.setValidator(self.validator1)
        #  Measurement Time
        self.time_time_lbl = QtWidgets.QLabel("Measurement time in [s]:")
        self.time_time_lbl.setFont(normal_font)
        self.time_time_txt = QtWidgets.QLineEdit()
        self.time_time_txt.setFont(normal_font)
        self.time_time_txt.setValidator(self.validator2)
        #  Step Size
        self.time_step_lbl = QtWidgets.QLabel("Step in [s]:")
        self.time_step_lbl.setFont(normal_font)
        self.time_step_txt = QtWidgets.QLineEdit()
        self.time_step_txt.setFont(normal_font)
        self.time_step_txt.setValidator(self.validator2)
        #  Gate Checkbox
        self.gate_measurement_lbl = QtWidgets.QLabel("Gate Measurement")
        self.gate_measurement_lbl.setFont(normal_font)
        self.gate_measurement_checkBox = QtWidgets.QCheckBox()
        #  Gate Voltage
        self.gate_gate_volt_lbl = QtWidgets.QLabel("Gate Voltage [V]:")
        self.gate_gate_volt_lbl.setFont(normal_font)
        self.gate_gate_volt_txt = QtWidgets.QLineEdit()
        self.gate_gate_volt_txt.setText("0")
        self.gate_gate_volt_txt.setValidator(self.validator1)
        # Option to not turn off voltage(ch.1) and reset the instrument
        self.reset_ins_lbl = QtWidgets.QLabel("Keep voltage on/don't reset")
        self.reset_ins_lbl.setFont(normal_font)
        self.reset_ins_lbl.setToolTip("Check the box if you don't want to reset the keysight and keep the voltage on after the measurement")
        self.reset_ins_checkbox = QtWidgets.QCheckBox()
        # Turn off voltage
        self.voltage_off_btn = QtWidgets.QPushButton("Turn off voltage output (Ch.1)")
        self.gate_measurement_lbl.setFont(normal_font)
        # Measurement status
        self.measurement_status_lbl = QtWidgets.QLabel("Measurement Status: ")
        self.measurement_status_lbl.setFont(normal_font)
        self.measurement_status_lbl2 = QtWidgets.QLabel()
        self.measurement_status_lbl2.setFont(normal_font)
        #  Start measurement
        self.time_start_btn = QtWidgets.QPushButton("START")
        self.time_start_btn.setFont(big_font)
        #  Clear Plot
        self.time_clear_btn = QtWidgets.QPushButton("Clear")
        self.time_clear_btn.setFont(normal_font)
        #  Plot
        pg.setConfigOption("foreground", "w")
        self.plot_graph = pg.PlotWidget()
        styles = {"font-size": "15px"}
        self.plot_graph.setBackground("black")
        self.plot_graph.setTitle("Time Dependent Current", color="w", size="20pt")
        self.plot_graph.setLabel('bottom', "Time [s]", **styles)
        self.plot_graph.setLabel('left', "Current [A]", **styles)
        self.plot_graph.showGrid(x=True, y=True)
        self.symbols = ["o", "s", "t", "d", "+", "x", "star"]
        self.pens = [pg.mkPen(255, 255, 0), pg.mkPen(255, 0, 255), pg.mkPen(0, 255, 255), pg.mkPen(255, 0, 0),
                     pg.mkPen(0, 255, 0), pg.mkPen(0, 0, 255), pg.mkPen(255, 255, 255)]
        # Layout of tab window
        layout.addWidget(self.time_v_lbl, 1, 0)
        layout.addWidget(self.time_v_txt, 1, 1)
        layout.addWidget(self.time_time_lbl, 2, 0)
        layout.addWidget(self.time_time_txt, 2, 1)
        layout.addWidget(self.time_step_lbl, 3, 0)
        layout.addWidget(self.time_step_txt, 3, 1)
        layout.addWidget(self.gate_measurement_lbl, 4, 0)
        layout.addWidget(self.gate_measurement_checkBox, 4, 1)
        layout.addWidget(self.gate_gate_volt_lbl, 5, 0)
        layout.addWidget(self.gate_gate_volt_txt, 5, 1)
        layout.addWidget(self.reset_ins_lbl, 6, 0)
        layout.addWidget(self.reset_ins_checkbox, 6, 1)
        layout.addWidget(self.voltage_off_btn, 7, 0, 1, 2)
        layout.addWidget(self.measurement_status_lbl, 9, 0)
        layout.addWidget(self.measurement_status_lbl2, 9, 1)
        layout.addWidget(self.time_start_btn, 10, 0, 1, 2)
        layout.addWidget(self.time_clear_btn, 0, 6)
        layout.addWidget(self.plot_graph, 1, 2, 10, 9)
        # Connecting Buttons to functions
        self.gate_measurement_checkBox.stateChanged.connect(self.gate_measurement_checkBox_checked)
        self.gate_measurement_checkBox_checked() # initial check
        self.time_clear_btn.clicked.connect(self.clear_btn_pressed)
        self.time_start_btn.clicked.connect(self.time_measurement)
        self.voltage_off_btn.clicked.connect(lambda: self.parent.keysight.output('off'))

        self.parent.tab_3.setLayout(layout)

    # Enable/Disable Gate measurement widgets based on checkbox is checked or not
    def gate_measurement_checkBox_checked(self):
        if self.gate_measurement_checkBox.isChecked():
            # Enable widgets
            self.gate_gate_volt_lbl.setDisabled(False)
            self.gate_gate_volt_txt.setDisabled(False)
            # Restore default text color
            self.gate_gate_volt_lbl.setStyleSheet("color: white")
            self.gate_gate_volt_txt.setStyleSheet("color: white")
        else:
            # Disable widgets
            self.gate_gate_volt_lbl.setDisabled(True)
            self.gate_gate_volt_txt.setDisabled(True)
            # Change text color to grey
            self.gate_gate_volt_lbl.setStyleSheet("color: grey")
            self.gate_gate_volt_txt.setStyleSheet("color: grey")

    # Worker thread for multithreading
    class WorkerThread(QThread):
        finished = pyqtSignal()
        plot = pyqtSignal(object)
        progress = pyqtSignal(int)

        def __init__(self, outer):
            super().__init__()
            self.outer = outer # reference to the outer class

        def run(self):
            if self.outer.parent.keysight == None:
                print("Make Sure Keysight is connected")
                self.finished.emit()
                return
            if self.outer.parent.save_file == None or self.outer.parent.save_file == " ":
                print("Make Sure You Choose File Location")
                self.finished.emit()
                return

            self.progress.emit(1) # Setting SMU
            # variables
            voltage = float(replace_separator(self.outer.time_v_txt.text()))
            measurement_time = float(replace_separator(self.outer.time_time_txt.text()))
            time_step = float(self.outer.time_step_txt.text())
            count = measurement_time / time_step
            wavelength = float(replace_separator(self.outer.wavelength_txt.text()))
            self.outer.file_header = "Time\tCurrent\tVoltage\ns\tA\tV\n\t" + str(wavelength) + "nm"  # set file header
            # set SMU
            if self.outer.reset_ins_checkbox.isChecked():
                self.outer.parent.prepareKeysight(3, voltage, False)
            else:
                self.outer.parent.prepareKeysight(3, voltage)
            self.outer.parent.keysight.measurement_trigger_count(time_step, count)

            if self.outer.gate_measurement_checkBox.isChecked():
                gate_voltage = float(replace_separator(self.outer.gate_gate_volt_txt.text()))
                self.outer.parent.keysight.apply_output_c2('Voltage', gate_voltage)
                self.outer.parent.save_file = self.outer.parent.save_file + "_GateMeasurement" # In order to indicate gate was used in the measurement

            if self.outer.parent.PS: self.outer.parent.PS.Signal_Generator(1500000)  # Generate signal if oscilloscope is open
            self.outer.parent.keysight.output('on')
            if self.outer.gate_measurement_checkBox.isChecked(): self.outer.parent.keysight.output_c2('on')

            self.outer.parent.keysight.measure()
            self.progress.emit(2) # Measurement started

            currents = self.outer.parent.keysight.retrieve_data("current")
            time.sleep(0.5)
            times = self.outer.parent.keysight.retrieve_data("time")
            time.sleep(0.5)
            voltages = self.outer.parent.keysight.retrieve_data("voltage")

            currents_floats = [float(x) for x in currents.split(',')]
            time_floats = [float(x) for x in times.split(',')]
            voltages_floats = [float(x) for x in voltages.split(',')]

            currents_arr = np.array(currents_floats)
            time_arr = np.array(time_floats)
            voltages_arr = np.array(voltages_floats)
            plot_arr = [time_arr, currents_arr]

            data = np.column_stack((time_arr, currents_arr, voltages_arr))
            self.outer.parent.save_data(data, self.outer.file_header)

            if self.outer.parent.PS: self.outer.parent.PS.Signal_Generator(0)  # Stop generating signal
            if not self.outer.reset_ins_checkbox.isChecked(): self.outer.parent.keysight.output('off')
            if self.outer.gate_measurement_checkBox.isChecked(): self.outer.parent.keysight.output_c2('off')

            self.outer.count+=1
            if self.outer.count==7: self.outer.count=0

            self.progress.emit(3) # Measurement finished
            self.finished.emit()
            self.plot.emit(plot_arr)

    def time_measurement(self):
        # Initialize thread
        self.thread = self.WorkerThread(self)
        # Quit and delete thread after measurement is done
        self.thread.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        # Connect signals to widgets
        self.thread.plot.connect(self.plot)
        self.thread.progress.connect(self.update_status)
        # Start the thread
        self.thread.start()

        # disable input lines
        self.time_start_btn.setDisabled(True)
        self.time_v_txt.setDisabled(True)
        self.time_time_txt.setDisabled(True)
        self.time_step_txt.setDisabled(True)
        self.gate_measurement_checkBox.setDisabled(True)
        self.gate_gate_volt_txt.setDisabled(True)
        # enable input lines back after measurement is done
        self.thread.finished.connect(self.postRun)

    def postRun(self):
        # enable input lines
        self.time_start_btn.setDisabled(False)
        self.time_v_txt.setDisabled(False)
        self.time_time_txt.setDisabled(False)
        self.time_step_txt.setDisabled(False)
        self.gate_measurement_checkBox.setDisabled(False)
        self.gate_gate_volt_txt.setDisabled(False)

    # Update measurement status
    def update_status(self, value):
        if value == 1:
            self.measurement_status_lbl2.setText("Setting SMU settings")
        elif value == 2:
            self.measurement_status_lbl2.setText("Measurement Started")
        else:
            self.measurement_status_lbl2.setText("Finished")

    # plot measurement graph
    def plot(self, list):
        self.plot_graph.plot(list[0], list[1], pen=self.pens[self.count], symbol=self.symbols[self.count])

    # clearing plots on Graph
    def clear_btn_pressed(self):
        self.plot_graph.clear()

def replace_separator(string1):
    string1 = string1.replace(',', '.')
    return string1
