import ctypes
import time

import numpy as np
import os
import math
from time import sleep

from picosdk.discover import find_all_units
from picosdk.ps2000 import ps2000 as ps
from picosdk.functions import adc2mV, assert_pico2000_ok
from picosdk.PicoDeviceEnums import picoEnum

from PyQt5 import QtWidgets

class PicoScope():
    # initilaziton of class
    def __init__(self):
        self.status = {}
        self.chandle = ctypes.c_int16()
        self.frequency = 0
        self.pkToPk = 1500000
        self.on = 0

    # Turn ON function
    def Turn_On(self):
        # Check if already opened
        if self.on == 1:
            return

        # Open Unit
        self.status["openUnit"] = ps.ps2000_open_unit()
        assert_pico2000_ok(self.status["openUnit"])
        self.chandle = ctypes.c_int16(self.status["openUnit"])
        self.on = 1

        # Send successful or not message to user
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Oscilloscope Status")
        if self.status["openUnit"] == 1:
            msg.setText("     Turn On Successful     ")
        elif self.status["openUnit"] == 0:
            msg.setText("     Oscilloscope not found     ")
        else:
            msg.setText("     Failed to open Oscilloscope       ")
        msg.exec_()

        print(self.status)

    # Turn Off function
    def Turn_Off(self):
        # Check if already closed
        if self.on == 0:
            return

        # Close Unit
        self.status["close"] = ps.ps2000_close_unit(self.chandle)
        assert_pico2000_ok(self.status["close"])
        self.on = 0

        # Send successful or not message to user
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Oscilloscope Status")
        if self.status["openUnit"] == 0:
            msg.setText("     Handle Not Valid     ")
        else:
            msg.setText("     Turn Off Successful     ")
        msg.exec_()

        print(self.status)

    # Setting frequency
    def set_Frequency(self, frequency):
        self.frequency = frequency

    # Signal Generator Function
    def Signal_Generator(self, pkToPk): # get peak to peak voltage value from application
        # Check if picoscope is on
        if self.on == 0:
            return

        # Setting variable for the function
        offsetVoltage = ctypes.c_int32(0)
        pk_To_Pk = ctypes.c_uint32(pkToPk) # Used for opening and closing the signal generator

        # PS2000_WAVE_TYPE
        #  "PS2000_SINE" 0
        #  "PS2000_SQUARE" 1
        #  "PS2000_TRIANGLE" 2
        #  "PS2000_RAMPUP" 3
        #  "PS2000_RAMPDOWN" 4
        #  "PS2000_DC_VOLTAGE" 5
        #  "PS2000_GAUSSIAN" 6
        #  "PS2000_SINC" 7
        #  "PS2000_HALF_SINE" 8
        waveType = 1

        # Between 0 and 100000
        startFrequency = self.frequency
        stopFrequency = startFrequency

        # These value are to be changed if startFrequency != stopFrequency
        increment = 0
        dwellTime = 1

        # PS2000_SWEEP_TYPE
        # PS_2000_UP 0
        # PS_2000_DOWN 1
        # PS_2000_UPDOWN 2
        # PS_2000_DOWNUP 3
        sweepType = 0

        sweepFrequency = ctypes.c_uint32(0)

        # Generate Signal
        self.status["ps2000_set_sig_gen_built_in"] = ps.ps2000_set_sig_gen_built_in(self.chandle, offsetVoltage, pk_To_Pk, waveType,
                                                                               startFrequency, stopFrequency, increment,
                                                                               dwellTime, sweepType, sweepFrequency)
        assert_pico2000_ok(self.status["ps2000_set_sig_gen_built_in"])

        # display status report
        print(self.status)

    def Stop(self):
        if self.on == 0:
            return

        status = ps.ps2000_set_sig_gen_built_in(self.chandle, ctypes.c_int32(0), ctypes.c_uint32(0), 0,
                                                0.0, 0.0, 0, 1, 0, ctypes.c_uint32(0))
        self.status["stop"] = status
        print(self.status)

# if __name__ == '__main__':
#     Ps = PicoScope()
#     Ps.Turn_On()
#     Ps.set_Frequency(1)
#     Ps.Signal_Generator(2500000)
#     time.sleep(6)
#     Ps.Stop()
#     Ps.Turn_Off()

