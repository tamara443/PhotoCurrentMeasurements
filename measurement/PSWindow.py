import numpy as np
import pandas as pd
import pyvisa
import os
from keithley2600 import Keithley2600
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPalette, QColor, QFont, QRegExpValidator
from PyQt5.QtCore import Qt, QRegExp
import LedIndicatorWidget
import pyqtgraph as pg
import NKTP_DLL
import time
from Keysight_B2902A_2channel import Agilent
from quantulum3 import parser
from PicoScope import PicoScope
# include tabs
from iv_measurement_tab import setup_iv_tab
from wavelength_tab import setup_wavelenght_tab
from time_measurement_tab import setup_time_tab
from idsvgs_tab import setup_ids_vgs_tab
from idsvgs_sweep_tab import setup_idsvgs_sweep_tab

echo_commands = 0  # echo needed for certain functions

# photo current measurement window
class PSWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.w = None  # set variable w (window) to None
        self.wavelength = 400  # set variable wavelength to 400
        self.bandwidth = 10  # set variable bandwidth to 10
        self.keithley = None  # set variable keithley (SMU measurement system) to None
        self.keysight = None  # Agilent()
        self.PS = None # PicoScope()
        # font styles
        self.normal_font = QFont('Calibri', 12)  # defining the normal font used for most texts
        # validators
        self.validator1 = QRegExpValidator(QRegExp(r'[+-]?([0-9]+[.,])?[0-9]+'))  # defining validator 1: every positive and negative float number
        self.validator2 = QRegExpValidator(QRegExp(r'([0-9]+[.,])?[0-9]+'))  # defining validator 2: every positive float number
        self.validator3 = QRegExpValidator(QRegExp(r'[0-9]+'))  # defining validator 3: every positive integer number
        # variables for saving
        self.folder_path = None # folder path in which measurement files should be saved if none is chosen
        self.save_file_name = ""  # name of saved file if none is chosen
        self.save_file = None  # saved file variable is folder in which file is to be saved as well as name of file
        # variables for loading file
        self.power_filename = ''  # setting the filename of power settings for laser to None

        # Widget of Main Window
        self.centralWidget = QtWidgets.QWidget()  # defining central widget as a widget
        self.setCentralWidget(self.centralWidget)  # set central widget as the central widget on the photo current main window
        toolbar = QtWidgets.QToolBar("Tool Bar")  # define toolbar as toolbar with name
        self.addToolBar(toolbar)  # add toolbar to the toolbar

        self.menu = self.menuBar()  # define menu as a menu bar
        file_menu = self.menu.addMenu("&File")  # add the file menu to the menu bar

        # layout of central widget
        self.ps_window_layout = QtWidgets.QGridLayout()  # define the photo current window layout as a grid layout
        self.centralWidget.setLayout(self.ps_window_layout)  # set the photo current window layout to the central widget

        # photo current window design
        self.setWindowTitle("Photo Current Measurement")  # set the title for photo current window

        #   Keysight Control (Right side of the page)
        # Keysight Control Check (Should only be checked by people who know what they are doing)
        self.keysight_control_lbl = self.createQLabel("Keysight Control", 0, 15)
        self.keysight_control_check = self.createQCheckBox(0, 16) # checkbox for keysight controls
        # Calibration
        self.keysight_calibrate_btn = self.createQPushButton(1, 15, "Calibrate", False, "Calibrate the Keysight B2902A before use. Before perfoming self-calibration, disconnect test leads and cables from the channel terminal.")
        self.keysight_calibration_result_lbl = self.createQLabel("", 1, 16)
        # Source Mode Selection
        self.keysight_source_lbl = self.createQLabel("Source Mode:", 2, 15)
        self.keysight_source_box = self.createQComboBox(2, 16, ["Voltage", "Current"])
        # Source Range (Based on Source Mode)
        self.keysight_source_range_lbl = self.createQLabel("Source Range [V] or [A]:", 3, 15, "Enter a fixed source range in V or A or a lower limit if the auto source range is checked.")
        self.keysight_source_range_auto_check = self.createQCheckBox(4, 16, "Auto", True)
        self.keysight_source_range_txt = self.createQLineEdit("0.2", 3, 16) # line edit for source range
        # Pulsed Source Check
        self.keysight_source_pulsed_lbl = self.createQLabel("Pulsed Source", 5, 15)
        self.keysight_source_pulsed_check = self.createQCheckBox(5, 16)
        # Source Trigger Input
        user_text = "What the different trigger and wait time options mean." #?
        image_path = "C:/Users/WET-Czerny/PycharmProjects/pythonProject/images/Trigger_image.png" #?
        self.keysight_source_trigger_lbl = self.createQLabel("Source Trigger [s]:", 6, 15)
        self.keysight_source_trigger_txt = self.createQLineEdit("0", 6, 16, self.validator2)
        # Source Wait Time
        self.keysight_source_wait_time_offset_lbl = self.createQLabel("Source Wait Time Offset [s]:", 7, 15)
        self.keysight_source_wait_time_offset_txt = self.createQLineEdit("0", 7, 16, self.validator2, "0 to 1 second")
        # Wait Time On/Off
        self.keysight_source_wait_check = self.createQCheckBox(8, 15, "Wait Time On/Off", True)
        self.keysight_source_wait_check_auto = self.createQCheckBox(8, 16, "Source Wait Time Auto", True)
        # Source Wait Gain
        self.keysight_source_wait_gain_lbl = self.createQLabel("Source Wait Gain [s]:", 9, 15, "The wait time calculates as follows: wait time offset + gain * initial wait time (intrinsic)")
        self.keysight_source_wait_time_gain_txt = self.createQLineEdit("1", 9, 16, self.validator2)
        # Measurement Mode Current/Voltage/Resistance
        self.keysight_sense_mode_lbl = self.createQLabel("Measurement Mode:", 10, 15)
        self.keysight_sense_mode_box = self.createQComboBox(10, 16, [])
        list1 = [("Current", ["100 nA", "1 µA", "10 µA", "100 µA", "1 mA", "10 mA", "100 mA", "1 A", "1.5 A", "3 A"]),
                 ("Voltage", ["0.2 V", "2 V", "20 V", "200 V"]),
                 ("Resistance", ["2 Ohm", "20 Ohm", "200 Ohm", "2 kOhm", "20 kOhm", "200 kOhm", "2 MOhm", "20 MOhm", "200 MOhm"])]
        for a, b in list1: # For adding items as tuples to the combo box
            self.keysight_sense_mode_box.addItem(a, b)
        # Measurement Speed
        self.keysight_sense_speed_lbl = self.createQLabel("Measurement Speed/NPLC [nplc]:", 11, 15, "Measurement speed given in nplc (number per power line cycle). It should be between 0.0001 and 100 for 50 Hz.")
        self.keysight_sense_speed_txt = self.createQLineEdit("1", 11, 16)
        self.keysight_sense_speed_auto_check = self.createQCheckBox(12, 16, "Auto")
        # Measurement Range
        self.keysight_sense_range_lbl = self.createQLabel("Measurement Range [s]", 13, 15)
        self.keysight_sense_range_box = self.createQComboBox(13, 16, [])
        self.keysight_sense_range_auto_check = self.createQCheckBox(14, 16, "Auto", True)
        self.set_sense_range(self.keysight_sense_mode_box.currentIndex())
        # Measurement Range Auto Mode
        self.keysight_sense_range_auto_lbl = self.createQLabel("Measurement Range Auto Mode:", 15, 15)
        self.keysight_sense_range_auto_box = self.createQComboBox(15 ,16, ["Normal", "Resolution", "Speed"])
        # Compliance
        self.keysight_sense_compliance_lbl = self.createQLabel("Compliance [mA]:", 16, 15)
        self.keysight_sense_compliance_txt = self.createQLineEdit("0.1", 16, 16, self.validator2)
        self.ps_window_layout.addWidget(QtWidgets.QWidget(), 17, 16) # Add an empty widget to skip line
        # Sense Trigger
        self.keysight_sense_trigger_lbl = self.createQLabel("Sense Trigger [s]", 18, 15)
        self.keysight_sense_trigger_txt = self.createQLineEdit("0", 18, 16, self.validator2)
        # Measurement Wait Time
        self.keysight_sense_wait_time_offset_lbl = self.createQLabel("Measurement Wait Time Offset [s]:", 19, 15)
        self.keysight_sense_wait_time_offset_txt = self.createQLineEdit("0", 19, 16, self.validator2, "0 to 1 second.")
        self.keysight_sense_wait_check = self.createQCheckBox(20, 15, "Wait Time On/Off", True) # check box for Measurement wait time
        self.keysight_sense_wait_check_auto = self.createQCheckBox(20, 16, "Measurement Wait Time Auto", True) # check box for sense auto wait time
        # Measurement Wait Gain
        self.keysight_sense_wait_gain = self.createQLabel("Measurement Wait Gain [s]", 21, 15, "The wait time calculates as follows: wait time offset + gain * initial wait time (intrinsic)")
        self.keysight_sense_wait_time_gain_txt = self.createQLineEdit("1", 21, 16, self.validator2)

        #   Keithley and Laser Connection (Upper Menu)
        # Selection of System Measurement Unit
        smu_lbl = self.createQLabel("SMU: ", 0, 0)
        self.keithley_box = self.createQComboBox(0, 1, ["Keysight B2902A", "Keithley 2601A", "Keithley 2601"]) # ("Keithley 2601", 26) might need to be changed
        self.keithley_btn = self.createQPushButton(0, 2, "Connect", True)
        # Remote Display ON/OFF
        keysight_remote_display_lbl = self.createQLabel("Remote Display", 0, 3)
        self.keysight_remote_display_btn = self.createQPushButton(0, 4, "ON", True)
        # Selection of Laser
        laser_lbl = self.createQLabel("Laser: ", 0, 5)
        laser_box = self.createQComboBox(0, 6, ["NKT Photonics FIANIUM", ""])
        self.laser_btn = self.createQPushButton(0, 7, "Connect", True)
        # Emission Indicator
        self.emission_btn = self.createQPushButton(0, 8, "Emission", True)
        self.emission_led = LedIndicatorWidget.LedIndicator(self)  # emission led taken from Led Indicator Widget
        self.emission_led.setDisabled(True)  # Make the emission led non-clickable
        self.ps_window_layout.addWidget(self.emission_led, 0, 9)

        #   More Widgets (Middle of the Page)
        # Power Input
        power_lbl = self.createQLabel("Power in [%]:", 0, 13, "Set laser power between 0 and 100 %.")
        self.power_txt = self.createQLineEdit("", 0, 14, self.validator2) # text edit for laser power
        self.power_slider = QtWidgets.QSlider(Qt.Horizontal, self)  # horizontal slider widget for laser power
        self.power_slider.setMinimum(0)  # set minimum for laser power slider (0%)
        self.power_slider.setMaximum(100)  # set maximum for laser power slider (100%)
        self.power_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)  # set ticks below slider for laser power slider
        self.power_slider.setTickInterval(10)  # set tick interval on laser power slider (10%)
        self.ps_window_layout.addWidget(self.power_slider, 1, 13, 1, 2)
        # Wavelength Input
        wavelength_lbl = self.createQLabel("Wavelength in [nm]:", 2, 13, "Set emission wavelength between 390 and 850 nm.")
        self.wavelength_txt = self.createQLineEdit(str(self.wavelength), 2, 14, self.validator2)
        self.wavelength_slider = QtWidgets.QSlider(Qt.Horizontal, self)  # horizontal slider widget for laser wavelength (middle)
        self.wavelength_slider.setMinimum(390)  # set minimum for laser wavelength slider (390 nm)
        self.wavelength_slider.setMaximum(850)  # set maximum for laser wavelength slider (850 nm)
        self.wavelength_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)  # set ticks below slider for laser wavelength slider
        self.wavelength_slider.setTickInterval(50)  # set tick interval on laser wavelength slider (50 nm)
        self.ps_window_layout.addWidget(self.wavelength_slider, 3, 13, 1, 2)
        # Bandwith Input
        bandwidth_lbl = self.createQLabel("Bandwidth in [nm]:", 4, 13, "Set emission bandwidth between 10 and 100 nm.")
        self.bandwidth_txt = self.createQLineEdit(str(self.bandwidth), 4, 14, self.validator2)
        # Filter 1 and 2
        filter1_lbl = self.createQLabel("Filter 1 [nm]", 5, 13, "Set lower filter to desired wavelength.")
        self.filter1_txt = self.createQLineEdit("", 5, 14, self.validator2)
        filter2_lbl = self.createQLabel("Filter 2 [nm]", 6, 13, "Set upper filter to desired wavelength.")
        self.filter2_txt = self.createQLineEdit("", 6, 14, self.validator2)
        # Saving the calculations
        save_file_lbl = self.createQLabel("Save as:", 7, 13, "Enter the name of the file the data should be saved in.")
        self.save_file_txt = self.createQLineEdit("", 7, 14)
        save_dir_btn = self.createQPushButton(8, 13, "Saving Directory", False, "Press to choose folder in which the file should be saved.")
        # Loading laser power settings
        self.load_file_btn = self.createQPushButton(9, 13, "Upload File", False, "Press to upload a file with laser power settings for wavelength dependent measurement.")
        self.load_file_txt = self.createQLineEdit("", 9, 14) # text edit for loading a laser power file
        # Emission Time set
        emission_time_lbl = self.createQLabel("Emission time in [s]", 11, 13, "Set the time the emission should be on.")
        self.emission_time_txt = self.createQLineEdit("", 11, 14, self.validator2) # text edit for emission time in case of On/Off
        # Off time set
        off_time_lbl = self.createQLabel("Off time in [s]", 12, 13, "Set the time the emission should be off.")
        self.off_time_txt = self.createQLineEdit("", 12, 14, self.validator2)
        # Emission Cycles ON/OFF
        emission_cycles_lbl = self.createQLabel("On/Off cycles", 13, 13, "Set the amount of cycles the emission should go On/Off.")
        self.emission_cycles_txt = self.createQLineEdit("", 13, 14, self.validator3) # text edit for repetition cycles of emission on/off
        self.on_off_button = self.createQPushButton(14, 13, "On/Off Start", True, "Start On/Off of laser emission.")
        #  PicScope2000 Settings
        # Middle-Below Menu
        self.picoScope_set_frequency_lbl = self.createQLabel("Set Frequency:", 16, 13, "Value should be between 0 and 100000")
        self.picoScope_set_frequency_txt = self.createQLineEdit("", 16, 14, self.validator2)
        picoScope_lbl = self.createQLabel("Turn On/Off PicoScope:", 17, 13, "When oscilloscope is open, laser is turned off until programm is run.\n Make sure oscilloscope is closed, if you don't want to use it.")
        self.picoScope_on_off_button = self.createQPushButton(17, 14, "On/Off", True)
        # Back Button
        self.back_btn = self.createQPushButton(20, 14, "Back", False)

        # Tabs Widget
        measurements = QtWidgets.QTabWidget(self)  # widget on central widget with several tabs for different measurements
        # Tab names and labels for different measurements
        tab_data = [
            ("tab_1", "IV measurement"),
            ("tab_2", "Wavelength dependent measurement"),
            ("tab_3", "Time dependent measurement"),
            ("tab_4", "IdsVgs Measurement"),
            ("tab_5", "IdsVgs Sweep Measurement")
        ]
        # Create and add tabs dynamically
        for tab_name, label in tab_data:
            tab = QtWidgets.QWidget()
            setattr(self, tab_name, tab)  # Dynamically assign tab to self.tab_1, self.tab_2, etc.
            measurements.addTab(tab, label)
        measurements.setFont(self.normal_font)  # set fonts for tabs

        self.IV_measurement_tab = setup_iv_tab(self)
        self.wavelength_tab = setup_wavelenght_tab(self)
        self.time_measurement_tab2 = setup_time_tab(self)
        self.IdsVgs_measurement_tab = setup_ids_vgs_tab(self)
        self.IdsVgs_sweep_tab = setup_idsvgs_sweep_tab(self)

        self.ps_window_layout.addWidget(measurements, 1, 0, 16, 12)

        # disabling all laser control functions, so that they are only enabled when devices are connected?
        self.emission_btn.setDisabled(True)
        self.power_txt.setDisabled(True)
        self.power_slider.setDisabled(True)
        self.wavelength_txt.setDisabled(True)
        self.wavelength_slider.setDisabled(True)
        self.bandwidth_txt.setDisabled(True)
        self.filter1_txt.setDisabled(True)
        self.filter2_txt.setDisabled(True)
        self.emission_time_txt.setDisabled(True)
        self.off_time_txt.setDisabled(True)
        self.emission_cycles_txt.setDisabled(True)
        self.on_off_button.setDisabled(True)

        # button pressed/input entered connected with functions
        self.picoScope_on_off_button.clicked.connect(lambda: self.PS_on_off())
        self.picoScope_set_frequency_txt.editingFinished.connect(lambda : self.PS.set_Frequency(float(replace_separator(self.picoScope_set_frequency_txt.text()))))

        self.keithley_btn.clicked.connect(self.keithley_btn_clicked)
        self.laser_btn.clicked.connect(self.laser_btn_clicked)
        self.power_txt.editingFinished.connect(self.power_enter)
        self.power_slider.valueChanged.connect(self.power_display)
        self.wavelength_txt.editingFinished.connect(self.wavelength_enter)
        self.wavelength_slider.valueChanged.connect(self.wavelength_display)
        self.bandwidth_txt.editingFinished.connect(self.bandwidth_enter)
        self.emission_btn.clicked.connect(lambda: self.on_emission_btn())
        self.save_file_txt.editingFinished.connect(self.save_file_txt_editing)
        save_dir_btn.clicked.connect(self.choose_save_folder)
        self.load_file_btn.clicked.connect(self.choose_power_file)
        self.load_file_txt.editingFinished.connect(self.write_power_file)
        self.on_off_button.clicked.connect(self.on_off_emission)
        self.back_btn.clicked.connect(self.back_btn_pressed)
        self.keysight_calibrate_btn.clicked.connect(self.calibrate)
        self.keysight_control_check.stateChanged.connect(self.keysight_control_check_changed)
        self.keysight_remote_display_btn.clicked.connect(self.remote_display_btn_pressed)
        self.keysight_sense_mode_box.currentIndexChanged.connect(self.set_sense_range)
        self.keysight_sense_range_auto_box.currentIndexChanged.connect(self.sense_auto_range)

    # Called when app is closed
    def closeEvent(self, event):
        if self.PS: self.PS.Turn_Off()
        if self.keysight: self.keysight.close()
        print("app closed!")

    # Position of Main window
    def location_on_the_screen(self):
        self.move(100, 100)

    # Function to prepare keysight before a measurement
    def prepareKeysight(self, num_type, voltage=None, reset = True):
        if reset: self.keysight.reset()
        self.keysight.data_type_obtain(num_type)
        self.choose_source_mode()
        self.set_source_range()
        self.set_trigger()
        self.source_wait_time()
        self.choose_sense_mode()
        self.set_measurement_speed()
        self.choose_sense_range()
        self.set_compliance()
        self.sense_wait_time()
        if voltage: self.apply_output(voltage)

    # Connecting to Keithley
    def keithley_btn_clicked(self):
        keithley_btn_state = self.keithley_btn.isChecked()
        if keithley_btn_state is True:
            box_text = self.keithley_box.currentText()
            if box_text == "Keithley 2601":
                instrument_string = "GPIB0::26::INSTR"
                resource_manager = pyvisa.ResourceManager()  # Opens the resource manager
                resource_manager, self.my_instr = instrument_connect(resource_manager, instrument_string, 20000, 1, 1, 1)
                self.keithley_btn.setText("Connected")
                self.keithley = Keithley2600('GPIB0::26::INSTR', visa_library='')
                # self.keithley.smua.source.output = self.keithley.smua.OUTPUT_ON
                if keithley_btn_state is False:
                    instrument_write(self.my_instr, "*RST")
                    instrument_disconnect(self.my_instr)
                    self.keithley_btn.setText("Connect")
                return
            elif box_text == "Keysight B2902A":
                self.keysight = Agilent()
                self.keysight.__init__()
                self.keysight.write("*IDN?")
                print(self.keysight.read())
                self.keithley_btn.setText("Connected")
                if keithley_btn_state is False:
                    self.keysight.write("*RST")
                    self.keysight.close()
                    self.keithley_btn.setText("Connect")
            else:
                print('No device has been chosen.')
                self.keithley_btn.setChecked(False)
                return
        else:
            self.keithley_btn.setText("Connect")
            return

    # Connecting to Laser and enabling all laser control functions
    def laser_btn_clicked(self):
        if self.laser_btn.isChecked():
            result_power, power_read = NKTP_DLL.registerReadU16('COM3', 15, 0x37, -1)
            self.power_txt.setText(str('{0:.2f}'.format(power_read * 0.1)))
            result1, filter1_set, result2, filter2_set = self.read_filters()

            if result1 == 0 and result2 == 0:
                result_emission, emission_read = NKTP_DLL.registerReadU8('COM3', 15, 0x30, -1)
                if result_emission == 0 and emission_read == 3:
                    self.emission_btn.setChecked(True)
                else:
                    self.emission_btn.setChecked(False)

                self.laser_btn.setText("Connected")
                self.emission_btn.setDisabled(False)
                self.power_txt.setDisabled(False)
                self.power_slider.setDisabled(False)
                self.wavelength_txt.setDisabled(False)
                self.wavelength_slider.setDisabled(False)
                self.bandwidth_txt.setDisabled(False)
                self.filter1_txt.setDisabled(False)
                self.filter2_txt.setDisabled(False)
                self.emission_time_txt.setDisabled(False)
                self.off_time_txt.setDisabled(False)
                self.emission_cycles_txt.setDisabled(False)
                self.on_off_button.setDisabled(False)

                self.bandwidth = filter2_set * 0.1 - filter1_set * 0.1
                self.wavelength = filter1_set * 0.1 + self.bandwidth/2
                self.bandwidth_txt.setText(str(self.bandwidth))
                self.wavelength_txt.setText(str(self.wavelength))

            else:
                print('No device is connected.')
        else:
            self.laser_btn.setText("Connect")
            self.emission_btn.setDisabled(True)
            self.power_txt.setDisabled(True)
            self.power_slider.setDisabled(True)
            self.wavelength_txt.setDisabled(True)
            self.wavelength_slider.setDisabled(True)
            self.bandwidth_txt.setDisabled(True)
            self.filter1_txt.setDisabled(True)
            self.filter2_txt.setDisabled(True)
            self.emission_time_txt.setDisabled(True)
            self.off_time_txt.setDisabled(True)
            self.emission_cycles_txt.setDisabled(True)
            self.on_off_button.setDisabled(True)

    # Pressing the Emission button
    def on_emission_btn(self):
        if self.emission_btn.isChecked():
            NKTP_DLL.registerWriteU8('COM3', 15, 0x30, 0x03, -1)
            self.emission_led.setChecked(not self.emission_led.isChecked())
        else:
            NKTP_DLL.registerWriteU8('COM3', 15, 0x30, 0x00, -1)
            self.emission_led.setChecked(self.emission_led.isChecked())

    # setting laser power
    def power_enter(self):
        power = float(replace_separator(self.power_txt.text()))
        self.power_slider.setValue(int(power))
        if 0 <= power <= 100:
            NKTP_DLL.registerWriteU16('COM3', 15, 0x37, int(power * 10), -1)
            result_power, power_read = NKTP_DLL.registerReadU16('COM3', 15, 0x37, -1)
            self.power_txt.setText(str('{0:.1f}'.format(power_read * 0.1)))
        else:
            print("A number outside of the range between 0 % and 100 % has been chosen.")

    # setting laser power with the slider
    def power_display(self, event):
        power = event
        NKTP_DLL.registerWriteU16('COM3', 15, 0x37, int(power * 10), -1)
        result_power, power_read = NKTP_DLL.registerReadU16('COM3', 15, 0x37, -1)
        self.power_txt.setText(str('{0:.1f}'.format(power_read * 0.1)))

    # Reading the registers from laser filter and displaying values
    def read_filters(self):
        read_result1, filter1 = NKTP_DLL.registerReadU16('COM3', 16, 0x34, -1)
        read_result2, filter2 = NKTP_DLL.registerReadU16('COM3', 16, 0x33, -1)
        self.filter1_txt.setText(str('{0:.1f}'.format(filter1 * 0.1)))
        self.filter2_txt.setText(str('{0:.1f}'.format(filter2 * 0.1)))
        return read_result1, filter1, read_result2, filter2

    # calculating the filter values from wavelength and bandwidth and writing to the laser filter
    def set_filters(self, wavelength, bandwidth):
        filter1 = wavelength - (bandwidth/2)
        filter2 = wavelength + (bandwidth/2)
        if filter1 >= 390 and filter2 <= 850 and 10 <= bandwidth <= 100:
            NKTP_DLL.registerWriteU16('COM3', 16, 0x34, int(filter1 * 10), -1)
            NKTP_DLL.registerWriteU16('COM3', 16, 0x33, int(filter2 * 10), -1)
        elif filter1 < 390 or filter2 > 850:
            print("A number outside of the filter range between 390 nm and 850 nm has been chosen.")
        elif bandwidth < 10 or bandwidth > 100:
            print("The bandwidth should be between 10 nm and 100 nm.")
        return

    # setting filters from changing the wavelength with text input
    def wavelength_enter(self):
        self.wavelength = float(replace_separator(self.wavelength_txt.text()))
        self.wavelength_slider.setValue(int(self.wavelength))
        self.set_filters(self.wavelength, self.bandwidth)
        result1, filter1_set, result2, filter2_set = self.read_filters()

    # setting filters from changing the wavelength with the slider
    def wavelength_display(self, event):
        self.wavelength = event
        self.wavelength_txt.setText(str(self.wavelength))
        self.set_filters(self.wavelength, self.bandwidth)
        result1, filter1_set, result2, filter2_set = self.read_filters()

    # setting filters from changing the bandwidth
    def bandwidth_enter(self):
        self.bandwidth = float(replace_separator(self.bandwidth_txt.text()))
        self.set_filters(self.wavelength, self.bandwidth)
        result1, filter1_set, result2, filter2_set = self.read_filters()

    # editing the name of save file
    def save_file_txt_editing(self):
        if self.save_file_txt.text() == "":
            self.save_file_name = "unknown"
        else:
            self.save_file_name = self.save_file_txt.text()
        self.save_file = self.folder_path + "/" + self.save_file_name
        return self.save_file

    # choosing folder in which files should be saved
    def choose_save_folder(self):
        self.folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Saving directory')
        self.save_file = self.save_file_txt_editing()

    # choosing power file to upload for wavelength dependent measurement
    def choose_power_file(self):
        self.power_filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Folder directory")
        self.load_file_txt.setText(self.power_filename)
        self.wavelength_tab.power_filename = self.power_filename
        return self.power_filename

    # writing path for power file to upload for wavelength dependent measurement
    def write_power_file(self):
        self.power_filename = self.load_file_txt.text()
        return self.power_filename

    # starting on/off emission
    def on_off_emission(self):
        self.on_off_button.setChecked(True)
        self.on_off_button.setText("On/Off Stop")
        on_time = float(replace_separator(self.emission_time_txt.text()))
        off_time = float(replace_separator(self.off_time_txt.text()))
        cycles = int(replace_separator(self.emission_cycles_txt.tet()))
        if on_time is not None and off_time is not None and cycles is not None:
            for i in range(cycles):
                NKTP_DLL.registerWriteU8('COM3', 15, 0x30, 0x03, -1)
                time.sleep(on_time)
                NKTP_DLL.registerWriteU8('COM3', 15, 0x30, 0x00, -1)
                time.sleep(off_time)
                if not self.on_off_button.isChecked(True):
                    continue
                break
            return
        elif on_time is None or off_time is None or cycles is None:
            print("Fill out all the required boxes.")
            return

    # pressing back button
    def back_btn_pressed(self):
        if self.w is None:
            self.w = StartWindow()
            self.w.show()
            self.hide()

        else:
            self.w.close()
            self.w = None

    # pressing remote display on/off button
    def remote_display_btn_pressed(self):
        if self.keysight_remote_display_btn.isChecked():
            self.keysight_remote_display_btn.setText("OFF")
            self.keysight.remote_display_mode('off')
        else:
            self.keysight_remote_display_btn.setText("ON")
            self.keysight.remote_display_mode('on')
            return

    # checking state of Keysight control checkbox
    def keysight_control_check_changed(self):
        """Enable and assign white color to all keysight controls if the Keysight control checkbox is checked"""
        if self.keysight_control_check.isChecked():
            self.keysight_calibrate_btn.setDisabled(False)
            self.keysight_source_box.setDisabled(False)
            self.keysight_source_range_txt.setDisabled(False)
            self.keysight_source_range_auto_check.setDisabled(False)
            self.keysight_source_pulsed_check.setDisabled(False)
            self.keysight_source_trigger_txt.setDisabled(False)
            self.keysight_source_wait_time_offset_txt.setDisabled(False)
            self.keysight_source_wait_check.setDisabled(False)
            self.keysight_source_wait_check_auto.setDisabled(False)
            self.keysight_source_wait_time_gain_txt.setDisabled(False)
            self.keysight_sense_mode_box.setDisabled(False)
            self.keysight_sense_speed_txt.setDisabled(False)
            self.keysight_sense_speed_auto_check.setDisabled(False)
            self.keysight_sense_range_box.setDisabled(False)
            self.keysight_sense_range_auto_check.setDisabled(False)
            self.keysight_sense_range_auto_box.setDisabled(False)
            self.keysight_sense_compliance_txt.setDisabled(False)
            self.keysight_sense_trigger_txt.setDisabled(False)
            self.keysight_sense_wait_check.setDisabled(False)
            self.keysight_sense_wait_check_auto.setDisabled(False)
            self.keysight_sense_wait_time_gain_txt.setDisabled(False)

            self.keysight_calibrate_btn.setStyleSheet("QPushButton{color:white;}")
            self.keysight_calibration_result_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_source_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_source_box.setStyleSheet("QComboBox{color:white;}")
            self.keysight_source_range_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_source_range_txt.setStyleSheet("QLineEdit{color:white;}")
            self.keysight_source_range_auto_check.setStyleSheet("QCheckBox{color:white;}")
            self.keysight_source_pulsed_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_source_pulsed_check.setStyleSheet("QCheckBox{color:white;}")
            self.keysight_source_trigger_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_source_trigger_txt.setStyleSheet("QLineEdit{color:white;}")
            self.keysight_source_wait_time_offset_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_source_wait_time_offset_txt.setStyleSheet("QLineEdit{color:white;}")
            self.keysight_source_wait_check.setStyleSheet("QCheckBox{color:white;}")
            self.keysight_source_wait_check_auto.setStyleSheet("QCheckBox{color:white;}")
            self.keysight_source_wait_gain_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_source_wait_time_gain_txt.setStyleSheet("QLineEdit{color:white;}")
            self.keysight_sense_mode_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_sense_mode_box.setStyleSheet("QComboBox{color:white;}")
            self.keysight_sense_speed_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_sense_speed_txt.setStyleSheet("QLineEdit{color:white;}")
            self.keysight_sense_speed_auto_check.setStyleSheet("QCheckBox{color:white;}")
            self.keysight_sense_range_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_sense_range_box.setStyleSheet("QComboBox{color:white;}")
            self.keysight_sense_range_auto_check.setStyleSheet("QCheckBox{color:white;}")
            self.keysight_sense_range_auto_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_sense_range_auto_box.setStyleSheet("QComboBox{color:white;}")
            self.keysight_sense_compliance_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_sense_compliance_txt.setStyleSheet("QLineEdit{color:white;}")
            self.keysight_sense_trigger_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_sense_trigger_txt.setStyleSheet("QLineEdit{color:white;}")
            self.keysight_sense_wait_time_offset_lbl.setStyleSheet("QLabel{color:white;}")
            self.keysight_sense_wait_time_offset_txt.setStyleSheet("QLineEdit{color:white;}")
            self.keysight_sense_wait_check.setStyleSheet("QCheckBox{color:white;}")
            self.keysight_sense_wait_check_auto.setStyleSheet("QCheckBox{color:white;}")
            self.keysight_sense_wait_gain.setStyleSheet("QLabel{color:white;}")
            self.keysight_sense_wait_time_gain_txt.setStyleSheet("QLineEdit{color:white;}")
            return
        else:
            """Disable and assign grey color to all keysight controls if the Keysight control checkbox is not checked"""
            self.keysight_calibrate_btn.setDisabled(True)
            self.keysight_source_box.setDisabled(True)
            self.keysight_source_range_txt.setDisabled(True)
            self.keysight_source_range_auto_check.setDisabled(True)
            self.keysight_source_pulsed_check.setDisabled(True)
            self.keysight_source_trigger_txt.setDisabled(True)
            self.keysight_source_wait_time_offset_txt.setDisabled(True)
            self.keysight_source_wait_check.setDisabled(True)
            self.keysight_source_wait_check_auto.setDisabled(True)
            self.keysight_source_wait_time_gain_txt.setDisabled(True)
            self.keysight_sense_mode_box.setDisabled(True)
            self.keysight_sense_speed_txt.setDisabled(True)
            self.keysight_sense_speed_auto_check.setDisabled(True)
            self.keysight_sense_range_box.setDisabled(True)
            self.keysight_sense_range_auto_check.setDisabled(True)
            self.keysight_sense_range_auto_box.setDisabled(True)
            self.keysight_sense_compliance_txt.setDisabled(True)
            self.keysight_sense_trigger_txt.setDisabled(True)
            self.keysight_sense_wait_time_offset_txt.setDisabled(True)
            self.keysight_sense_wait_check.setDisabled(True)
            self.keysight_sense_wait_check_auto.setDisabled(True)
            self.keysight_sense_wait_time_gain_txt.setDisabled(True)

            self.keysight_calibrate_btn.setStyleSheet("QPushButton{color:grey;}")
            self.keysight_calibration_result_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_source_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_source_box.setStyleSheet("QComboBox{color:grey;}")
            self.keysight_source_range_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_source_range_txt.setStyleSheet("QLineEdit{color:grey;}")
            self.keysight_source_range_auto_check.setStyleSheet("QCheckBox{color:grey;}")
            self.keysight_source_pulsed_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_source_pulsed_check.setStyleSheet("QCheckBox{color:grey;}")
            self.keysight_source_trigger_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_source_trigger_txt.setStyleSheet("QLineEdit{color:grey;}")
            self.keysight_source_wait_time_offset_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_source_wait_time_offset_txt.setStyleSheet("QLineEdit{color:grey;}")
            self.keysight_source_wait_check.setStyleSheet("QCheckBox{color:grey;}")
            self.keysight_source_wait_check_auto.setStyleSheet("QCheckBox{color:grey;}")
            self.keysight_source_wait_gain_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_source_wait_time_gain_txt.setStyleSheet("QLineEdit{color:grey;}")
            self.keysight_sense_mode_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_sense_mode_box.setStyleSheet("QComboBox{color:grey;}")
            self.keysight_sense_speed_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_sense_speed_txt.setStyleSheet("QLineEdit{color:grey;}")
            self.keysight_sense_speed_auto_check.setStyleSheet("QCheckBox{color:grey;}")
            self.keysight_sense_range_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_sense_range_box.setStyleSheet("QComboBox{color:grey;}")
            self.keysight_sense_range_auto_check.setStyleSheet("QCheckBox{color:grey;}")
            self.keysight_sense_range_auto_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_sense_range_auto_box.setStyleSheet("QComboBox{color:grey;}")
            self.keysight_sense_compliance_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_sense_compliance_txt.setStyleSheet("QLineEdit{color:grey;}")
            self.keysight_sense_trigger_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_sense_trigger_txt.setStyleSheet("QLineEdit{color:grey;}")
            self.keysight_sense_wait_time_offset_lbl.setStyleSheet("QLabel{color:grey;}")
            self.keysight_sense_wait_time_offset_txt.setStyleSheet("QLineEdit{color:grey;}")
            self.keysight_sense_wait_check.setStyleSheet("QCheckBox{color:grey;}")
            self.keysight_sense_wait_check_auto.setStyleSheet("QCheckBox{color:grey;}")
            self.keysight_sense_wait_gain.setStyleSheet("QLabel{color:grey;}")
            self.keysight_sense_wait_time_gain_txt.setStyleSheet("QLineEdit{color:grey;}")
            return

    # Keysight Calibration
    def calibrate(self):
        self.keysight.write("*CAL?")
        self.keysight.read()
        self.keysight_calibration_result_lbl.setText("Calibrated")
        return

    # choosing source mode
    def choose_source_mode(self):
        i = self.keysight_source_box.currentIndex()
        if i == 0:
            self.keysight.source_output_mode('voltage')
            return
        elif i == 1:
            self.keysight.source_output_mode('current')
            return
        else:
            return

    # choose output (voltage or current, value)
    def apply_output(self, value):
        m = self.keysight_source_box.currentText()
        v = value
        self.keysight.apply_output(m, v)
        return

    # setting the source range
    def set_source_range(self):
        mode = self.keysight_source_box.currentIndex()
        i = self.keysight_source_range_auto_check.isChecked()
        r = self.keysight_source_range_txt.text()
        if i is True and mode == 0:
            self.keysight.output_range('voltage', 'on', r)
            return
        elif i is True and mode == 1:
            self.keysight.output_range('current', 'on', r)
            return
        elif i is False and mode == 0:
            self.keysight.output_range('voltage', 'on', r)
            return
        elif i is False and mode == 1:
            self.keysight.output_range('current', 'on', r)
        else:
            return

    # setting trigger time
    def set_trigger(self):
        t = self.keysight_source_trigger_txt.text()
        q = self.keysight_sense_trigger_txt.text()
        self.keysight.output_trigger(t, q)
        return

    # setting source wait time
    def source_wait_time(self):
        a = self.keysight_source_wait_check_auto.isChecked()
        i = self.keysight_source_wait_check.isChecked()
        o = self.keysight_source_wait_time_offset_txt.text()
        g = self.keysight_source_wait_time_gain_txt.text()
        if i is False:
            self.keysight.source_wait_time('off', 'off', '0', '0')
            return
        elif i is True and a is False:
            self.keysight.source_wait_time('off', 'on', o, g)
        elif i is True and a is True:
            self.keysight.source_wait_time('on', 'on', '0', '1')
            return
        else:
            return

    # choosing sense mode
    def choose_sense_mode(self):
        i = self.keysight_sense_mode_box.currentIndex()
        if i == 0:
            self.keysight_sense_compliance_lbl.setText("Compliance [mA]:")
            self.keysight.measurement_mode('current', 'on')
            return 'current'
        elif i == 1:
            self.keysight_sense_compliance_lbl.setText("Compliance [V]:")
            self.keysight.measurement_mode('voltage', 'on')
            return 'voltage'
        elif i == 2:
            self.keysight.measurement_mode('resistance', 'on')
            return 'resistance'
        else:
            return

    # set measurement speed
    def set_measurement_speed(self):
        i = self.keysight_sense_mode_box.currentIndex()
        a = self.keysight_sense_speed_auto_check.isChecked()
        s = self.keysight_sense_speed_txt.text()
        if i == 0 and a is True:
            self.keysight.measurement_speed("current", "on", 0.1)
            return
        elif i == 0 and a is False:
            self.keysight.measurement_speed("current", "off", s)
            return
        elif i == 1 and a is True:
            self.keysight.measurement_speed("voltage", "on", 0.1)
            return
        elif i == 1 and a is False:
            self.keysight.measurement_speed("voltage", "off", s)
            return
        elif i == 2 and a is True:
            self.keysight.measurement_speed("resistance", "on", 0.1)
            return
        elif i == 2 and a is False:
            self.keysight.measurement_speed("resistance", "off", s)
            return
        else:
            return

    # set sense range for sense mode
    def set_sense_range(self, index):
        self.keysight_sense_range_box.clear()
        range_options = self.keysight_sense_mode_box.itemData(index)
        if range_options is not None:
            self.keysight_sense_range_box.addItems(range_options)

    # choose sense range
    def choose_sense_range(self):
        m = self.keysight_sense_mode_box.currentText()
        i = self.keysight_sense_range_auto_check.isChecked()
        r = parser.parse(self.keysight_sense_range_box.currentText())
        v = r[0].value
        u = str(r[0].unit)
        if u == "milliampere":
            v = v/1000
        elif u == "microampere":
            v = v/1000000
        elif u == "nanoampere":
            v = v/1000000000
        if i is False:
            self.keysight.measurement_range(m, 'off', v)
            return
        else:
            return

    # setting auto range on or off
    def sense_auto_range(self):
        i = self.keysight_sense_range_auto_check.isChecked()
        m = self.keysight_sense_mode_box.currentText()
        print(m)
        o = self.keysight_sense_range_auto_box.currentText()
        if i is True:
            self.keysight.measurement_auto_range(m, o)
            return
        else:
            self.keysight.measurement_auto_range_off(m, 'off')
            return

    # set compliance
    def set_compliance(self):
        m = self.keysight_sense_mode_box.currentText()
        c = self.keysight_sense_compliance_txt.text()
        self.keysight.compliance(m, c)
        return

    # setting sense wait time
    def sense_wait_time(self):
        a = self.keysight_sense_wait_check_auto.isChecked()
        i = self.keysight_sense_wait_check.isChecked()
        o = self.keysight_sense_wait_time_offset_txt.text()
        g = self.keysight_sense_wait_time_gain_txt.text()
        if i is False:
            self.keysight.measurement_wait_time('off', 'off', '0', '0')
            return
        elif i is True and a is False:
            self.keysight.measurement_wait_time('off', 'on', g, o)
            return
        elif i is True and a is True:
            self.keysight.measurement_wait_time('on', 'on', '1', '0')
            return
        else:
            return

    # Save measurement data to given location with given name
    def save_data(self, data, file_header):
        # Base file name
        base_file_name = self.save_file + ".dat"
        file_name = base_file_name
        counter = 1

        # Check if the file already exists and modify the name if necessary
        while os.path.exists(file_name):
            file_name = f"{self.save_file}_{counter}.dat"
            counter += 1

        # Write data to the uniquely named file
        with open(file_name, 'wb') as file:
            np.savetxt(file, [], header=file_header)
            np.savetxt(file, data)
            file.flush()

    # Function to turn on/off Picoscope
    def PS_on_off(self):
        if self.picoScope_on_off_button.isChecked():
            self.PS = PicoScope()
            self.PS.Turn_On()
        else:
            self.PS.Turn_Off()
            self.PS = None

    # Create and add a QLabel widget to the layout
    def createQLabel(self, label, row, column, tooltip=None):
        button = QtWidgets.QLabel(label)
        button.setFont(self.normal_font)
        if tooltip: button.setToolTip(tooltip)
        self.ps_window_layout.addWidget(button, row, column)
        return button

    # Create and add QLineEdit widget to the layout
    def createQLineEdit(self, default, row, column, validator=None, tooltip=None):
        button = QtWidgets.QLineEdit(default)
        button.setFont(self.normal_font)
        if validator: button.setValidator(validator)
        if tooltip: button.setToolTip(tooltip)
        self.ps_window_layout.addWidget(button, row, column)
        return button

    # Create and add QCheckBox widget to the layout
    def createQCheckBox(self, row, column, text="", state=False):
        button = QtWidgets.QCheckBox(text)
        button.setFont(self.normal_font)
        if state: button.setChecked(state)
        self.ps_window_layout.addWidget(button, row, column)
        return button

    # Create and add QComboBox widget to the layout
    def createQComboBox(self, row, column, items):
        button = QtWidgets.QComboBox()
        button.setFont(self.normal_font)
        button.addItems(items)
        self.ps_window_layout.addWidget(button, row, column)
        return button

    # Create and add QPushButton widget to the layout
    def createQPushButton(self, row, column, text, checkable, tooltip=None):
        button = QtWidgets.QPushButton(text)
        button.setFont(self.normal_font)
        button.setCheckable(checkable)
        if tooltip: button.setToolTip(tooltip)
        self.ps_window_layout.addWidget(button, row, column)
        return button

def instrument_connect(resource_mgr, instrument_resource_string, timeout, do_id_query, do_reset, do_clear):
    instrument_object = resource_mgr.open_resource(instrument_resource_string)
    if do_id_query == 1:
        print(instrument_query(instrument_object, "*IDN?"))
    if do_reset == 1:
        instrument_write(instrument_object, "*RST")
    if do_clear == 1:
        instrument_object.clear()
    instrument_object.timeout = timeout
    return resource_mgr, instrument_object

def instrument_write(instrument_object, my_command):
    if echo_commands == 1:
        print(my_command)
    instrument_object.write(my_command)
    return

def instrument_query(instrument_object, my_command):
    if echo_commands == 1:
        print(my_command)
    return instrument_object.query(my_command)

def instrument_disconnect(instrument_object):
    instrument_object.close()
    return

def replace_separator(string1):
    string1 = string1.replace(',', '.')
    return string1
