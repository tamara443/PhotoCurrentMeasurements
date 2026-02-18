from PyQt5 import QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import QThread, pyqtSignal
import pyqtgraph as pg
import time
import numpy as np
import os

class setup_ids_vgs_tab():
    def __init__(self, parent):
        self.parent = parent
        self.count = 0 # count for the number of times the measurement has been run

        # font styles
        normal_font = QFont('Arial', 12)
        big_font = QFont('Arial', 20)

        #Layout style of the tab
        layout = QtWidgets.QGridLayout()
        layout.setVerticalSpacing(15)
        # Widgets on the tab
        #  Drain Source Voltage
        self.ds_volt_lbl = QtWidgets.QLabel("Drain-Source voltage[V]")
        self.ds_volt_lbl.setFont(normal_font)
        self.ds_volt_dsb = QtWidgets.QDoubleSpinBox()
        self.ds_volt_dsb.setFont(normal_font)
        self.ds_volt_dsb.setDecimals(3)
        self.ds_volt_dsb.setRange(-200, 200)
        #  Start Gate Voltage
        self.s_volt_lbl = QtWidgets.QLabel("Start gate voltage[V]")
        self.s_volt_lbl .setFont(normal_font)
        self.s_volt_dsb = QtWidgets.QDoubleSpinBox()
        self.s_volt_dsb.setFont(normal_font)
        self.s_volt_dsb.setRange(-200, 200)
        #  End gate Voltage
        self.e_volt_lbl = QtWidgets.QLabel("End gate voltage[V]")
        self.e_volt_lbl.setFont(normal_font)
        self.e_volt_dsb = QtWidgets.QDoubleSpinBox()
        self.e_volt_dsb.setFont(normal_font)
        self.e_volt_dsb.setRange(-200, 200)
        #  Gate voltage stepsize
        self.t_volt_lbl = QtWidgets.QLabel("Gate voltage stepsize [V]")
        self.t_volt_lbl.setFont(normal_font)
        self.t_volt_dsb = QtWidgets.QDoubleSpinBox()
        self.t_volt_dsb.setDecimals(3)
        self.t_volt_dsb.setFont(normal_font)
        self.t_volt_dsb.setRange(-200, 200)
        # Measurement status
        self.measurement_status_lbl = QtWidgets.QLabel("Measurement Status: ")
        self.measurement_status_lbl.setFont(normal_font)
        self.measurement_status_lbl2 = QtWidgets.QLabel()
        self.measurement_status_lbl2.setFont(normal_font)
        #  Start button
        self.start_btn = QtWidgets.QPushButton("START")
        self.start_btn.setFont(big_font)
        #  Graph Clear button
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.setFont(normal_font)
        #  Plot
        self.plot_graph = pg.PlotWidget()
        styles = {"color": "white", "font-size":"18px"}
        self.plot_graph.setBackground("black")
        self.plot_graph.setTitle("IdsVgs Calculation")
        self.plot_graph.setLabel('bottom', "Gate Source Voltage (V)", **styles)
        self.plot_graph.setLabel('left', "Drain Source Current", **styles)
        self.plot_graph.addLegend()
        self.plot_graph.showGrid(x=True, y=True)
        self.symbols = ["o", "s", "t", "d", "+", "x", "star"]
        self.pens = [pg.mkPen(255, 255, 0), pg.mkPen(255, 0, 255), pg.mkPen(0, 255, 255), pg.mkPen(255, 0, 0),
                     pg.mkPen(0, 255, 0), pg.mkPen(0, 0, 255), pg.mkPen(255, 255, 255)]
        # Positioning of the buttons
        layout.addWidget(self.clear_btn, 0, 4)
        layout.addWidget(self.ds_volt_lbl, 1, 0)
        layout.addWidget(self.ds_volt_dsb, 1, 1)
        layout.addWidget(self.s_volt_lbl, 2, 0)
        layout.addWidget(self.s_volt_dsb, 2, 1)
        layout.addWidget(self.e_volt_lbl, 3, 0)
        layout.addWidget(self.e_volt_dsb, 3, 1)
        layout.addWidget(self.t_volt_lbl, 4, 0)
        layout.addWidget(self.t_volt_dsb, 4, 1)
        layout.addWidget(self.measurement_status_lbl, 9, 0)
        layout.addWidget(self.measurement_status_lbl2, 9, 1)
        layout.addWidget(self.start_btn, 10, 0, 1, 2)
        layout.addWidget(self.plot_graph, 1, 2, 10, 5)

        # Button to function connections
        self.start_btn.clicked.connect(lambda: self.measurement())
        self.clear_btn.clicked.connect(lambda: self.clear_btn_pressed())

        parent.tab_4.setLayout(layout)

    class WorkerThread(QThread):
        finished = pyqtSignal()
        plot = pyqtSignal(object)
        progress = pyqtSignal(int)

        def __init__(self, outer):
            super().__init__()
            self.outer = outer

        def run(self):
            if self.outer.parent.keysight == None:
                print("Make Sure Keysight is connected")
                self.finished.emit()
                return
            if self.outer.parent.save_file == None:
                print("Make Sure You Choose File Location")
                self.finished.emit()
                return

            self.progress.emit(1)
            # Collect variables from widgets
            ds = float(self.outer.ds_volt_dsb.text())
            start = float(self.outer.s_volt_dsb.text())
            finish = float(self.outer.e_volt_dsb.text())
            stepsize = float(self.outer.t_volt_dsb.text())
            p = int(abs(finish - start) / stepsize)
            # Set SMU
            self.outer.parent.prepareKeysight(2)
            self.outer.parent.keysight.apply_output('Voltage', ds)
            self.outer.parent.keysight.source_output_mode_c2('voltage')
            self.outer.parent.keysight.sweep_output_c2('Voltage', 'up', stepsize, start, finish)
            self.outer.parent.keysight.measurement_trigger_count_auto(p + 1)
            self.outer.parent.keysight.measurement_trigger_count_auto_c2(p + 1)
            self.outer.parent.keysight.output('on')
            self.outer.parent.keysight.output_c2('on')
            # Start Measurement
            self.outer.parent.keysight.measure()
            self.outer.parent.keysight.measure_c2()
            self.progress.emit(2)
            # Fetch Data
            self.outer.parent.keysight.write("FETC:ARR:VOLT? (@1)")
            time.sleep(0.5)
            v_ds_list = self.outer.parent.keysight.read()
            self.outer.parent.keysight.write(":FETC:ARR:CURR? (@1)")
            time.sleep(0.5)
            currents_list = self.outer.parent.keysight.read()
            self.outer.parent.keysight.write("FETC:ARR:VOLT? (@2)")
            time.sleep(0.5)
            v_gs_list = self.outer.parent.keysight.read()

            v_ds_floats = [float(x) for x in v_ds_list.split(',')]
            currents_floats = [float(x) for x in currents_list.split(',')]
            v_gs_floats = [float(x) for x in v_gs_list.split(',')]

            vds_arr = np.array(v_ds_floats)
            currents_arr = np.array(currents_floats)
            vgs_arr = np.array(v_gs_floats)
            plot_arr = [vgs_arr, currents_arr]

            data = np.column_stack((vgs_arr, currents_arr, vds_arr))

            file_header = "V_G [V]\tI_DS [A]\tV_DS [V]"
            self.outer.parent.save_data(data, file_header)

            self.outer.parent.keysight.output('off')
            self.outer.parent.keysight.output_c2('off')

            self.outer.count += 1
            if self.outer.count == 7: self.count = 0

            self.progress.emit(3)
            self.finished.emit()
            self.plot.emit(plot_arr)

    def measurement(self):
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
        self.ds_volt_dsb.setDisabled(True)
        self.s_volt_dsb.setDisabled(True)
        self.e_volt_dsb.setDisabled(True)
        self.t_volt_dsb.setDisabled(True)
        # enable input lines back after measurement is done
        self.thread.finished.connect(self.postRun)

    def postRun(self):
        self.ds_volt_dsb.setDisabled(False)
        self.s_volt_dsb.setDisabled(False)
        self.e_volt_dsb.setDisabled(False)
        self.t_volt_dsb.setDisabled(False)

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
