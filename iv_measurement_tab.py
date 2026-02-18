from PyQt5 import QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import QRegExp, QObject, QThread, pyqtSignal
import pyqtgraph as pg
import time
import numpy as np
import os

class setup_iv_tab():
    def __init__(self, parent):
        self.parent = parent
        self.count = 0 # count for the number of times the measurement has been run
        # validators
        self.validator = QRegExpValidator(QRegExp(r'[+-]?([0-9]+[.,])?[0-9]+'))  # defining validator 1: every positive and negative float number

        # font styles
        normal_font = QFont('Calibri', 12)  # defining the normal font used for most texts
        big_font = QFont('Calibri', 24)  # defining the big font used to larger objects

        # Layout style of the tab
        layout = QtWidgets.QGridLayout()
        # Widgets on IV measurement tab:
        #  Start Voltage
        self.start_v_lbl = QtWidgets.QLabel("Start voltage in [V]:")
        self.start_v_lbl.setFont(normal_font)
        self.start_v_dsb = QtWidgets.QDoubleSpinBox()
        self.start_v_dsb.setFont(normal_font)
        self.start_v_dsb.setRange(-200, 200)
        self.start_v_dsb.setDecimals(5)
        #  End Voltage
        self.stop_v_lbl = QtWidgets.QLabel("End voltage in [V]:")
        self.stop_v_lbl.setFont(normal_font)
        self.stop_v_dsb = QtWidgets.QDoubleSpinBox()
        self.stop_v_dsb.setFont(normal_font)
        self.stop_v_dsb.setRange(-200, 200)
        self.stop_v_dsb.setDecimals(5)
        #  Step Size
        self.step_v_lbl = QtWidgets.QLabel("Step in [V]:")
        self.step_v_lbl.setFont(normal_font)
        self.step_v_dsb = QtWidgets.QDoubleSpinBox()
        self.step_v_dsb.setFont(normal_font)
        self.step_v_dsb.setRange(-200, 200)
        self.step_v_dsb.setDecimals(5)
        #  Start measurement button
        self.iv_start_btn = QtWidgets.QPushButton("START")
        self.iv_start_btn.setFont(big_font)
        #  Clear plot button
        self.iv_clear_btn = QtWidgets.QPushButton("Clear")
        self.iv_clear_btn.setFont(normal_font)
        #  Plot
        pg.setConfigOption("foreground", "w")
        self.plot_graph = pg.PlotWidget()
        styles = {"font-size": "15px"}
        self.plot_graph.setBackground("black")
        self.plot_graph.setTitle("IV-Plot", color="w", size="20pt")
        self.plot_graph.setLabel('bottom', "Voltage [V]", **styles)
        self.plot_graph.setLabel('left', "Current [A]", **styles)
        self.plot_graph.showGrid(x=True, y=True)
        self.symbols = ["o", "s", "t", "d", "+", "x", "star"]
        self.pens = [pg.mkPen(255, 255, 0), pg.mkPen(255, 0, 255), pg.mkPen(0, 255, 255), pg.mkPen(255, 0, 0),
                     pg.mkPen(0, 255, 0), pg.mkPen(0, 0, 255), pg.mkPen(255, 255, 255)]

        # Layout of IV measurement tab window, added widget: element, vertical position, horizontal position
        layout.addWidget(self.start_v_lbl, 1, 0)
        layout.addWidget(self.start_v_dsb, 1, 1)
        layout.addWidget(self.stop_v_lbl, 2, 0)
        layout.addWidget(self.stop_v_dsb, 2, 1)
        layout.addWidget(self.step_v_lbl, 3, 0)
        layout.addWidget(self.step_v_dsb, 3, 1)
        layout.addWidget(self.iv_start_btn, 7, 0, 2, 2)
        layout.addWidget(self.iv_clear_btn, 0, 6)
        layout.addWidget(self.plot_graph, 1, 2, 10, 9)

        # starting iv-measurement with pressing on start button
        self.iv_clear_btn.clicked.connect(self.clear_btn_pressed)
        self.iv_start_btn.clicked.connect(self.iv_measurement)

        self.parent.tab_1.setLayout(layout)

    # Worker class for multithreading
    class Worker(QObject):
        finished = pyqtSignal()
        plot = pyqtSignal(object)

        def __init__(self, outer):
            super().__init__()
            self.outer = outer  # Reference to the outer setup_iv_tab instance

        def measurement(self):
            if self.outer.parent.keysight == None:
                print("Make Sure Keysight is connected")
                self.finished.emit()
                return
            if self.outer.parent.save_file == None:
                print("Make Sure You Choose File Location")
                self.finished.emit()
                return

            # variables
            voltage_start = float(self.outer.start_v_dsb.text())
            voltage_end = float(self.outer.stop_v_dsb.text())
            voltage_step = float(self.outer.step_v_dsb.text())
            data_points = int((voltage_end - voltage_start) / voltage_step) + 1
            # data arrays
            voltages = np.linspace(voltage_start, voltage_end, data_points + 1)
            # set SMU
            self.outer.parent.prepareKeysight(3)
            self.outer.parent.keysight.sweep_output('Voltage', 'up', voltage_step, voltage_start, voltage_end)
            self.outer.parent.keysight.measurement_trigger_count_auto(data_points)
            time.sleep(1)

            self.outer.parent.keysight.output('on')
            self.outer.parent.keysight.measure()
            currents = self.outer.parent.keysight.retrieve_data("current")
            time.sleep(0.5)
            voltages = self.outer.parent.keysight.retrieve_data("voltage")
            time.sleep(0.5)
            times = self.outer.parent.keysight.retrieve_data("time")

            self.outer.parent.keysight.output('off')

            currents_floats = [float(x) for x in currents.split(',')]
            time_floats = [float(x) for x in times.split(',')]
            voltages_floats = [float(x) for x in voltages.split(',')]

            currents_arr = np.array(currents_floats)
            time_arr = np.array(time_floats)
            voltages_arr = np.array(voltages_floats)

            plot_arr = [voltages_arr, currents_arr]

            data = np.column_stack((voltages_arr, currents_arr, time_arr))
            file_header = "Voltage\tCurrent\tTime\nV\tA\ts"
            self.outer.parent.save_data(data, file_header)

            self.finished.emit() # signal thread is done
            self.plot.emit(plot_arr)

    # Creating the thread, moving worker to the thread, running the measurement
    def iv_measurement(self):
        # Create QThread
        self.thread = QThread()
        # Create a worker object
        self.worker = self.Worker(self)
        # Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Connect signals and slots
        self.thread.started.connect(self.worker.measurement)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.thread.deleteLater)
        # Start the thread
        self.thread.start()

        # Final re-sets
        self.start_v_dsb.setDisabled(True)
        self.stop_v_dsb.setDisabled(True)
        self.step_v_dsb.setDisabled(True)
        self.iv_start_btn.setDisabled(True)
        self.worker.finished.connect(self.postRun)
        self.worker.plot.connect(self.plot)

    def plot(self, list):
        self.plot_graph.plot(list[0], list[1], pen=self.pens[self.count], symbol=self.symbols[self.count])

    def postRun(self):
        # enable input lines
        self.start_v_dsb.setDisabled(False)
        self.stop_v_dsb.setDisabled(False)
        self.step_v_dsb.setDisabled(False)
        self.iv_start_btn.setDisabled(False)
        # adjust measurement count
        self.count+=1
        if self.count == 7: self.count = 0
        print("Finished")

    # clearing plots on Graph
    def clear_btn_pressed(self):
        self.plot_graph.clear()
