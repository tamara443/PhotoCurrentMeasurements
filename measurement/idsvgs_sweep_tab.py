from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QScrollArea, QApplication, QProgressBar
from PyQt5.QtGui import *
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
import pyqtgraph as pg
import time
import numpy as np
import os

class setup_idsvgs_sweep_tab():
    def __init__(self, parent):
        self.parent = parent
        self.count = 0 # measurement count value
        self._mutex = QMutex() # Parallel access to a variable
        # font styles
        normal_font = QFont('Arial', 12)
        big_font = QFont('Arial', 20)

        #Layout style of the tab
        self.layout = QtWidgets.QGridLayout()
        self.layout.setVerticalSpacing(10)
        # Widgets on the tab
        #  Start Drain Source Voltage
        self.ds_s_lbl = QtWidgets.QLabel("Start Drain-Source voltage [V]")
        self.ds_s_lbl.setFont(normal_font)
        self.ds_s_dsb = QtWidgets.QDoubleSpinBox()
        self.ds_s_dsb.setFont(normal_font)
        self.ds_s_dsb.setRange(-200, 200)
        #  End Drain Source Voltage
        self.ds_e_lbl = QtWidgets.QLabel("End Drain-Source voltage [V]")
        self.ds_e_lbl.setFont(normal_font)
        self.ds_e_dsb = QtWidgets.QDoubleSpinBox()
        self.ds_e_dsb.setFont(normal_font)
        self.ds_e_dsb.setRange(-200, 200)
        #  End Drain Source Voltage
        self.ds_t_lbl = QtWidgets.QLabel("Drain-Source Step size [V]")
        self.ds_t_lbl.setFont(normal_font)
        self.ds_t_dsb = QtWidgets.QDoubleSpinBox()
        self.ds_t_dsb.setFont(normal_font)
        self.ds_t_dsb.setRange(-200, 200)
        #  Start Gate Voltage
        self.g_s_lbl = QtWidgets.QLabel("Start gate voltage[V]")
        self.g_s_lbl .setFont(normal_font)
        self.g_s_dsb = QtWidgets.QDoubleSpinBox()
        self.g_s_dsb.setFont(normal_font)
        self.g_s_dsb.setRange(-200, 200)
        #  End gate Voltage
        self.g_e_lbl = QtWidgets.QLabel("End gate voltage[V]")
        self.g_e_lbl.setFont(normal_font)
        self.g_e_dsb = QtWidgets.QDoubleSpinBox()
        self.g_e_dsb.setFont(normal_font)
        self.g_e_dsb.setRange(-200, 200)
        #  Gate voltage stepsize
        self.g_t_lbl = QtWidgets.QLabel("Gate voltage stepsize in [V]")
        self.g_t_lbl.setFont(normal_font)
        self.g_t_dsb = QtWidgets.QDoubleSpinBox()
        self.g_t_dsb.setFont(normal_font)
        self.g_t_dsb.setRange(-200, 200)
        # Progress Bar
        self.progress_bar = QProgressBar()
        #  Interrupt measurement
        self.idsvgs_interrput_btn = QtWidgets.QPushButton("Interrupt")
        self.idsvgs_interrput_btn.setFont(big_font)
        self.idsvgs_interrput_btn.setToolTip("It might take couple of seconds for the measurement to stop. Be patient!")
        self.idsvgs_interrput_btn.setDisabled(True)
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
        self.plot_graph.setTitle("IdsVgs Sweep Calculation")
        self.plot_graph.setLabel('bottom', "Drain Source Voltage", **styles)
        self.plot_graph.setLabel('left', "Drain Source Current", **styles)
        self.plot_graph.addLegend(offset=(0, 0))
        self.plot_graph.showGrid(x=True, y=True)
        self.symbols = ["o", "s", "t", "d", "+", "x", "star"]
        self.pens = [pg.mkPen(255, 255, 0), pg.mkPen(255, 0, 255), pg.mkPen(0, 255, 255), pg.mkPen(255, 0, 0),
                     pg.mkPen(0, 255, 0), pg.mkPen(0, 0, 255), pg.mkPen(255, 255, 255)]
        # Positioning of the buttons
        self.layout.addWidget(self.clear_btn, 0, 4)
        self.layout.addWidget(self.ds_s_lbl, 1, 0)
        self.layout.addWidget(self.ds_s_dsb, 1, 1)
        self.layout.addWidget(self.ds_e_lbl, 2, 0)
        self.layout.addWidget(self.ds_e_dsb, 2, 1)
        self.layout.addWidget(self.ds_t_lbl, 3, 0)
        self.layout.addWidget(self.ds_t_dsb, 3, 1)
        self.layout.addWidget(self.g_s_lbl, 4, 0)
        self.layout.addWidget(self.g_s_dsb, 4, 1)
        self.layout.addWidget(self.g_e_lbl, 5, 0)
        self.layout.addWidget(self.g_e_dsb, 5, 1)
        self.layout.addWidget(self.g_t_lbl, 6, 0)
        self.layout.addWidget(self.g_t_dsb, 6, 1)
        self.layout.addWidget(self.progress_bar, 8, 0, 1, 2)
        self.layout.addWidget(self.idsvgs_interrput_btn, 9, 0, 1, 2)
        self.layout.addWidget(self.start_btn, 10, 0, 1, 2)
        self.layout.addWidget(self.plot_graph, 1, 2, 10, 5)

        # Button to function connections
        self.start_btn.clicked.connect(lambda: self.measurement())
        self.clear_btn.clicked.connect(lambda: self.clear_btn_pressed())
        self.idsvgs_interrput_btn.clicked.connect(self.raiseFlag)

        parent.tab_5.setLayout(self.layout)

    # Worker thread for multithreading
    class WorkerThread(QThread):
        finished = pyqtSignal()
        progress = pyqtSignal(int)
        plot = pyqtSignal(object)

        def __init__(self, outer):
            super().__init__()
            self.outer = outer
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
            # Get variable from widgets
            ds_s = float(self.outer.ds_s_dsb.text())
            ds_e = float(self.outer.ds_e_dsb.text())
            ds_t = float(self.outer.ds_t_dsb.text())
            g_s = float(self.outer.g_s_dsb.text())
            g_e = float(self.outer.g_e_dsb.text())
            g_t = float(self.outer.g_t_dsb.text())
            p_ds = int((ds_e - ds_s) / ds_t)
            p_g = int((g_e - g_s) / g_t)
            # Set SMU
            self.outer.parent.prepareKeysight(2)
            self.outer.parent.keysight.source_output_mode_c2('voltage')
            self.outer.parent.keysight.sweep_output('Voltage', "up", ds_t, ds_s, ds_e)
            self.outer.parent.keysight.measurement_trigger_count_auto(p_ds + 1)
            self.outer.parent.keysight.measurement_trigger_count_auto_c2(p_ds + 1)
            v_g = np.linspace(g_s, g_e, int(p_g + 1))

            file_header = "V_DS [V]\tI_DS [A]\tV_G [V]"
            og_file_name = self.outer.parent.save_file
            # Start measurement
            for i in v_g:
                # Check flag raised or not
                self.outer._mutex.lock() # Lock the variable to prevent errors caused by accessing the same variable from different threads
                if self.flag == True:
                    self.flag = False
                    self.finished.emit()
                    self.outer._mutex.unlock()
                    print("Interrupt Called")
                    return
                self.outer._mutex.unlock() # unlock the variable

                self.outer.parent.save_file = self.outer.parent.save_file + str(round(i, 2)) + "V"
                self.outer.parent.keysight.write(":SOUR2:VOLT:TRIG " + str(i))
                self.outer.parent.keysight.output('on')
                self.outer.parent.keysight.output_c2('on')
                self.outer.parent.keysight.measure()
                self.outer.parent.keysight.measure_c2()
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
                plot_arr = [v_ds_floats, currents_floats]

                data = np.column_stack((vds_arr, currents_arr, vgs_arr))

                self.outer.parent.save_data(data, file_header)  # save data
                self.outer.parent.keysight.output('off')  # turn off channel1 output
                self.outer.parent.keysight.output_c2('off')  # turn off channel2 output

                self.outer.parent.save_file = og_file_name  # Set file name to back to original so that voltages values reset after the original name
                self.progress.emit(int((100 * (i)) / len(v_g))) # Signal progress for progress bar
                self.plot.emit(plot_arr)
            self.finished.emit() # signal thread is done

    def measurement(self):
        # Initialize thread
        self.thread = self.WorkerThread(self)
        # Quit and delete thread after measurement is done
        self.thread.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        # Connect progress signal to progress bar
        self.thread.progress.connect(self.progress_bar_edit)
        self.thread.plot.connect(self.plot)
        # Start the thread
        self.thread.start()

        # Disable input lines
        self.ds_s_dsb.setDisabled(True)
        self.ds_e_dsb.setDisabled(True)
        self.ds_t_dsb.setDisabled(True)
        self.g_s_dsb.setDisabled(True)
        self.g_e_dsb.setDisabled(True)
        self.g_t_dsb.setDisabled(True)
        self.idsvgs_interrput_btn.setDisabled(False)
        # Enable input lines back after measurement
        self.thread.finished.connect(self.postRun)

    def postRun(self):
        self.ds_s_dsb.setDisabled(False)
        self.ds_e_dsb.setDisabled(False)
        self.ds_t_dsb.setDisabled(False)
        self.g_s_dsb.setDisabled(False)
        self.g_e_dsb.setDisabled(False)
        self.g_t_dsb.setDisabled(False)
        self.idsvgs_interrput_btn.setDisabled(True)

    # raise flag to interrupt the measurement
    def raiseFlag(self):
        self._mutex.lock() # Lock the variable to prevent errors caused by accessing the same variable from two different threads
        self.thread.flag = True
        self._mutex.unlock()

    # Edit progress bar and process all events
    def progress_bar_edit(self, value):
        self.progress_bar.setValue(value)
        QApplication.processEvents()

    # plot measurement graph
    def plot(self, list):
        self.plot_graph.plot(list[0], list[1], pen=self.pens[self.count], symbol=self.symbols[self.count])
        QApplication.processEvents()
        self.count += 1
        if self.count == 7: self.count = 0

    # clearing plots on Graph
    def clear_btn_pressed(self):
        self.plot_graph.clear()

