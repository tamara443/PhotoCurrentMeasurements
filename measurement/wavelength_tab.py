from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QSizePolicy, QProgressBar, QApplication
from PyQt5.QtGui import *
from PyQt5.QtCore import QRegExp, Qt, QThread, pyqtSignal, QObject, QMutex
import pyqtgraph as pg
import time
import numpy as np
import NKTP_DLL
import os

class setup_wavelenght_tab():
    def __init__(self, parent):
        self.parent = parent
        self.count = 0 # count for the number of times the measurement has been run
        self.power_filename = parent.power_filename
        # validators
        self.validator1 = QRegExpValidator(QRegExp(r'[+-]?([0-9]+[.,])?[0-9]+'))  # defining validator 1: every positive and negative float number
        self.validator2 = QRegExpValidator(QRegExp(r'([0-9]+[.,])?[0-9]+'))  # defining validator 2: every positive float number
        # Parallel access to a variable
        self._mutex = QMutex()

        # font styles
        normal_font = QFont('Calibri', 12)  # defining the normal font used for most texts
        big_font = QFont('Calibri', 24)  # defining the big font used to larger objects

        # Layout style of the tab
        layout = QtWidgets.QGridLayout()
        # Widgets on wavelength dependent measurement tab:
        #  Voltage
        self.voltage_lbl = QtWidgets.QLabel("Voltage in [V]:")
        self.voltage_lbl.setFont(normal_font)
        self.voltage_txt = QtWidgets.QLineEdit()
        self.voltage_txt.setFont(normal_font)
        self.voltage_txt.setValidator(self.validator1)
        #  Start Wavelength
        self.start_wavelength_lbl = QtWidgets.QLabel("Start wavelength in [nm]:")
        self.start_wavelength_lbl.setFont(normal_font)
        self.start_wavelength_txt = QtWidgets.QLineEdit()
        self.start_wavelength_txt.setFont(normal_font)
        self.start_wavelength_txt.setValidator(self.validator2)
        #  End Wavelength
        self.end_wavelength_lbl = QtWidgets.QLabel("End wavelength in [nm]:")
        self.end_wavelength_lbl.setFont(normal_font)
        self.end_wavelength_txt = QtWidgets.QLineEdit()
        self.end_wavelength_txt.setFont(normal_font)
        self.end_wavelength_txt.setValidator(self.validator2)
        #  Wavelength Step
        self.step_wavelength_lbl = QtWidgets.QLabel("Step in [nm]:")
        self.step_wavelength_lbl.setFont(normal_font)
        self.step_wavelength_txt = QtWidgets.QLineEdit()
        self.step_wavelength_txt.setFont(normal_font)
        self.step_wavelength_txt.setValidator(self.validator2)
        #  Measurement Time
        self.wavelength_time_lbl = QtWidgets.QLabel("Measurement time in [s]:")
        self.wavelength_time_lbl.setFont(normal_font)
        self.wavelength_time_txt = QtWidgets.QLineEdit()
        self.wavelength_time_txt.setFont(normal_font)
        self.wavelength_time_txt.setValidator(self.validator2)
        #  Time Step
        self.wavelength_time_step_lbl = QtWidgets.QLabel("Time step in [s]:")
        self.wavelength_time_step_lbl.setFont(normal_font)
        self.wavelength_time_step_txt = QtWidgets.QLineEdit()
        self.wavelength_time_step_txt.setFont(normal_font)
        self.wavelength_time_step_txt.setValidator(self.validator2)
        #  Start measurement
        self.wavelength_start_btn = QtWidgets.QPushButton("START")
        self.wavelength_start_btn.setFont(big_font)
        #  Interrupt measurement
        self.wavelength_interrput_btn = QtWidgets.QPushButton("Interrupt")
        self.wavelength_interrput_btn.setFont(big_font)
        self.wavelength_interrput_btn.setToolTip("It might take couple of seconds for the measurement to stop. Be patient!")
        self.wavelength_interrput_btn.setDisabled(True)
        # Progress Bar
        self.progress_bar = QProgressBar()
        #  Clear plot
        self.wavelength_clear_btn = QtWidgets.QPushButton("Clear")
        self.wavelength_clear_btn.setFont(normal_font)
        #  Plot (Currently Not used)
        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setTitle("NOT FUNCTIONAL", color="w", size="20pt")
        # Layout of tab window (wavelength dependent measurement)
        layout.addWidget(self.voltage_lbl, 1, 0)
        layout.addWidget(self.voltage_txt, 1, 1)
        layout.addWidget(self.start_wavelength_lbl, 2, 0)
        layout.addWidget(self.start_wavelength_txt, 2, 1)
        layout.addWidget(self.end_wavelength_lbl, 3, 0)
        layout.addWidget(self.end_wavelength_txt, 3, 1)
        layout.addWidget(self.step_wavelength_lbl, 4, 0)
        layout.addWidget(self.step_wavelength_txt, 4, 1)
        layout.addWidget(self.wavelength_time_lbl, 5, 0)
        layout.addWidget(self.wavelength_time_txt, 5, 1)
        layout.addWidget(self.wavelength_time_step_lbl, 6, 0)
        layout.addWidget(self.wavelength_time_step_txt, 6, 1)
        layout.addWidget(self.progress_bar, 8, 0, 1, 2)
        layout.addWidget(self.wavelength_interrput_btn, 9, 0, 1, 2)
        layout.addWidget(self.wavelength_start_btn, 10, 0, 1, 2)
        layout.addWidget(self.plot_graph, 1, 2, 10, 9)
        # button pressed tab window (wavelength dependent measurement)
        self.wavelength_start_btn.clicked.connect(self.wavelength_measurement)
        self.wavelength_interrput_btn.clicked.connect(self.raiseFlag)

        parent.tab_2.setLayout(layout)

    # Worker thread for multithreading
    class WorkerThread(QThread):
        finished = pyqtSignal()
        progress = pyqtSignal(int)

        def __init__(self, outer):
            super().__init__()
            self.outer = outer  # Reference to the outer class
            self.flag = False

        def run(self):
            if self.outer.parent.keysight == None:
                print("Make Sure parent.Keysight is connected")
                self.finished.emit()
                return
            if self.outer.parent.save_file == None:
                print("Make Sure You Choose File Location")
                self.finished.emit()
                return

            # variables
            voltage = float(replace_separator(self.outer.voltage_txt.text()))
            measurement_time = float(replace_separator(self.outer.wavelength_time_txt.text()))
            time_step = float(replace_separator(self.outer.wavelength_time_step_txt.text()))
            count = measurement_time / time_step

            # Set SMU
            self.outer.parent.prepareKeysight(3, voltage)
            self.outer.parent.keysight.measurement_trigger_count(time_step, count)

            # Gather data from UI
            if self.outer.start_wavelength_txt.text() != '':
                self.wavelength_start = float(replace_separator(self.outer.start_wavelength_txt.text()))
            else:
                self.wavelength_start = 0
            if self.outer.end_wavelength_txt.text() != '':
                self.wavelength_end = float(replace_separator(self.outer.end_wavelength_txt.text()))
            else:
                self.wavelength_end = 0
            if self.outer.step_wavelength_txt.text() != '':
                self.wavelength_step = float(replace_separator(self.outer.step_wavelength_txt.text()))
            else:
                self.wavelength_step = 0
            if self.wavelength_start != 0 and self.wavelength_end != 0 and self.wavelength_step != 0:
                self.data_points = int((self.wavelength_end - self.wavelength_start) / self.wavelength_step)
            else:
                self.data_points = 0

            if self.outer.power_filename != '':
                with open(self.outer.power_filename) as power_file:
                    power_array = np.loadtxt(power_file, delimiter="\t")
                if self.wavelength_start in power_array:
                    b = np.where(power_array == self.wavelength_start)
                    power_array = power_array[b[0][0]:, :]
                if self.wavelength_end in power_array:
                    e = np.where(power_array == self.wavelength_end)
                    power_array = power_array[:e[0][0] + 1, :]
                else:
                    power_array = power_array[:, :]
            elif self.outer.power_filename == '':
                wavelengths = np.linspace(self.wavelength_start, self.wavelength_end, self.data_points + 1)
                powers = np.zeros_like(wavelengths) + 1000
                power_array = np.column_stack((wavelengths, powers))
            else:
                return
            power_array = power_array * 10
            power_array = power_array.astype('int32')

            og_file_name = self.outer.parent.save_file

            for i in range(len(power_array)):
                self.outer._mutex.lock() # Lock the variable to prevent errors caused by accessing the same variable from different threads
                if self.flag == True:
                    self.flag = False
                    self.finished.emit()
                    self.outer._mutex.unlock()
                    print("Interrupt Called")
                    return
                self.outer._mutex.unlock()

                NKTP_DLL.registerWriteU16('COM3', 16, 0x34, int(power_array[i, 0] - 50), -1)
                NKTP_DLL.registerWriteU16('COM3', 16, 0x33, int(power_array[i, 0] + 50), -1)
                NKTP_DLL.registerWriteU16('COM3', 15, 0x37, int(power_array[i, 1]), -1)
                time.sleep(2)  # wait for 2 sec

                if self.outer.parent.PS: self.parent.PS.Signal_Generator(1500000)  # Generate signal if oscilloscope is open
                self.outer.parent.keysight.output('on')
                self.outer.parent.keysight.measure()
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

                data = np.column_stack((time_arr, currents_arr, voltages_arr))
                self.outer.parent.save_file = self.outer.parent.save_file + "_" + str(power_array[i, 0]) + "nm" + str(
                    power_array[i, 1]) + "p"
                file_header = "Time\tCurrent\tVoltage\ns\tA\tV\n\t" + str(power_array[i, 0] / 10) + "nm"
                self.outer.parent.save_data(data, file_header)

                if self.outer.parent.PS: self.outer.parent.PS.Signal_Generator(0)  # Stop generating signal
                self.outer.parent.keysight.output('off')

                self.outer.parent.save_file = og_file_name  # Set file name to back to original so that new naming of the file does not keep adding up
                self.progress.emit(int((100 * (i+1)) / len(power_array))) # Signal progress for progress bar
                time.sleep(2)

            print("Finished")
            self.finished.emit() # signal thread is done

    def wavelength_measurement(self):
        # Initialize thread
        self.thread = self.WorkerThread(self)
        # Quit and delete thread after measurement is done
        self.thread.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        # Connect progress signal to progress bar
        self.thread.progress.connect(self.progress_bar_edit)

        # Start the thread
        self.thread.start()

        # disable input lines
        self.wavelength_start_btn.setDisabled(True)
        self.voltage_txt.setDisabled(True)
        self.start_wavelength_txt.setDisabled(True)
        self.end_wavelength_txt.setDisabled(True)
        self.step_wavelength_txt.setDisabled(True)
        self.wavelength_time_txt.setDisabled(True)
        self.wavelength_time_step_txt.setDisabled(True)
        self.wavelength_interrput_btn.setDisabled(False)

        # enable input lines back after measurement is done
        self.thread.finished.connect(self.postRun)

    def postRun(self):
        # enable input lines
        self.wavelength_start_btn.setDisabled(False)
        self.voltage_txt.setDisabled(False)
        self.start_wavelength_txt.setDisabled(False)
        self.end_wavelength_txt.setDisabled(False)
        self.step_wavelength_txt.setDisabled(False)
        self.wavelength_time_txt.setDisabled(False)
        self.wavelength_time_step_txt.setDisabled(False)
        self.wavelength_interrput_btn.setDisabled(True)

    # raise flag to interrupt the measurement
    def raiseFlag(self):
        self._mutex.lock() # Lock the variable to prevent errors caused by accessing the same variable from two different threads
        self.thread.flag = True
        self._mutex.unlock()

    # Edit progress bar and process all events
    def progress_bar_edit(self, value):
        self.progress_bar.setValue(value)
        QApplication.processEvents()

def replace_separator(string1):
    string1 = string1.replace(',', '.')
    return string1
