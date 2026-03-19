import pyvisa as visa
import time
import struct
from numpy import floor, log10


class Agilent(object):
    """
    Agilent Instrument
    """

    def __init__(self, dev="USB0::0x0957::0x8C18::MY51141352::INSTR", baud_rate=57600,
                 write_termination='\n', read_termination='\n', timeout=10000):
        self.rm = visa.ResourceManager()
        self.rm.list_resources()
        self.ag = self.rm.open_resource(dev)
        self.ag.write('*RST')
        self.ag.VI_ATTR_TERMCHAR_EN = True
        self.ag.VI_ATTR_ASRL_FLOW_CNTRL= 'VI_ASRL_FLOW_DTR_DSR'
        self.ag.timeout = 1000000   # war 50000 aber Error bei langen Messungen

        # self.ag.write('*IDN?')
        # print(self.ag.read())

    def close(self):
        self.ag.close()

    def write(self, txt):
        """write commands in text code"""
        self.ag.write(txt)

    def read(self):
        """Read the returned data"""
        return self.ag.read()

    def read_error_message(self):
        """Read Error messages"""
        self.write(':SYST:ERR?')
        err = self.ag.read()
        return print(err)

    def reset(self):
        """Reset SMU"""
        self.write("*RST")

    def remote_display_mode(self, display_mode):
        if display_mode == 'on':
            self.write(':DISP:ENAB ON')
        elif display_mode == 'off':
            self.write(':DISP:ENAB OFF')
        else:
            return print('Invalid operation')

    def output(self, source_output):
        if source_output == 'on':
            self.write(':OUTP ON')
        elif source_output == 'off':
            self.write(':OUTP OFF')
        else:
            return print('Invalid operation_outputc1')

    def output_c2(self, source_output):
        if source_output == 'on':
            self.write(':OUTP2 ON')
        elif source_output == 'off':
            self.write(':OUTP2 OFF')
        else:
            return print('Invalid operation_output')

    def source_output_mode(self, output_mode):
        if output_mode == 'voltage':
            self.write(':SOUR:FUNC:MODE VOLT')
        elif output_mode == 'current':
            self.write(':SOUR:FUNC:MODE CURR')
        else:
            return print('Invalid operation_source_c1')

    def source_output_mode_c2(self, output_mode):
        if output_mode == 'voltage':
            self.write(':SOUR2:FUNC:MODE VOLT')
        elif output_mode == 'current':
            self.write(':SOUR2:FUNC:MODE CURR')
        else:
            return print('Invalid operation_source')

    def apply_output(self, mode, value):
        if mode == 'Voltage':
            self.write(':SOUR:VOLT:TRIG '+str(value))
        elif mode == 'Current':
            self.write(':SOUR:CURR:TRIG '+str(value))
        else:
            return print('Invalid operation')

    def apply_output_c2(self, mode, value):
        if mode == 'Voltage':
            self.write(':SOUR2:VOLT '+str(value)) # Alternatively :TRIG
        elif mode == 'Current':
            self.write(':SOUR2:CURR '+str(value)) # Alternatively :TRIG
        else:
            return print('Invalid operation_apply')

    def compliance(self, mode, value):
        if mode == 'Current':
            value = float(value)/1000
            self.write(':SENS1:CURR:PROT '+str(value))
        elif mode == 'Voltage':
            self.write(':SENS1:VOLT:PROT '+str(value))
        else:
            return print('Invalid operation_compliance')

    def compliance_c2(self, mode, value):
        if mode == 'Current':
            value = float(value)/1000
            self.write(':SENS2:CURR:PROT '+str(value))
        elif mode == 'Voltage':
            self.write(':SENS2:VOLT:PROT '+str(value))
        else:
            return print('Invalid operation_compliance')

    def output_range(self, mode, auto, value):
        if mode == 'current':
            if auto == 'on':
                self.write(':SOUR:CURR:RANG:AUTO ON')
                self.write(':SOUR:CURR:RANG:AUTO:LLIM '+str(value))
            elif auto == 'off':
                self.write(':SOUR:CURR:RANG:AUTO OFF')
                self.write(':SOUR:CURR:RANG '+str(value))
            else:
                return print('Invalid operation')
        elif mode == 'voltage':
            if auto == 'on':
                self.write(':SOUR:VOLT:RANG:AUTO ON')
                self.write(':SOUR:VOLT:RANG:AUTO:LLIM '+str(value))
            elif auto == 'off':
                self.write(':SOUR:VOLT:RANG:AUTO OFF')
                self.write(':SOUR:VOLT:RANG '+value)
            else:
                return print('Invalid operation')

    def pulse_output(self, mode, delay_time, pulse_width, base_value, peak_value):
        self.write(':SOUR:FUNC:SHAP PULS:')
        self.write(':SOUR:PULS:DEL '+str(delay_time))
        self.write(':SOUR:PULS:WIDT '+str(pulse_width))
        if mode == 'current':
            self.write(':SOUR:CURR '+str(base_value))
            self.write(':SOUR:CURR:TRIG '+str(peak_value))
            self.output('on')
            self.write(':INIT (@1)')
        elif mode == 'voltage':
            self.write(':SOUR:VOLT '+str(base_value))
            self.write(':SOUR:VOLT:TRIG '+str(peak_value))
            self.output('on')
            self.write(':INIT (@1)')
        else:
            return print('Invalid operation')

    def sweep_output(self, mode, direction, step, start, stop):
        if direction == 'up':
            self.write(':SOUR:SWE:DIR UP')
        elif direction == 'down':
            self.write(':SOUR:SWE:DIR DOWN')
        else:
            return print('Invalid operation')

        if mode == 'Current':
            self.write(':SOUR:CURR:MODE SWE')
            self.write(':SOUR:CURR:STAR '+str(start))
            self.write(':SOUR:CURR:STOP '+str(stop))
            self.write('SOUR:CURR:STEP '+str(step))
        elif mode == 'Voltage':
            self.write(':SOUR:VOLT:MODE SWE')
            self.write(':SOUR:VOLT:STAR '+str(start))
            self.write(':SOUR:VOLT:STOP '+str(stop))
            self.write('SOUR:VOLT:STEP '+str(step))
        else:
            return print('Invalid operation')

    def sweep_output_c2(self, mode, direction, step, start, stop):
        if direction == 'up':
            self.write(':SOUR2:SWE:DIR UP')
        elif direction == 'down':
            self.write(':SOUR2:SWE:DIR DOWN')
        else:
            return print('Invalid operation')

        if mode == 'Current':
            self.write(':SOUR2:CURR:MODE SWE')
            self.write(':SOUR2:CURR:STAR ' + str(start))
            self.write(':SOUR2:CURR:STOP ' + str(stop))
            self.write('SOUR2:CURR:STEP ' + str(step))
        elif mode == 'Voltage':
            self.write(':SOUR2:VOLT:MODE SWE')
            self.write(':SOUR2:VOLT:STAR ' + str(start))
            self.write(':SOUR2:VOLT:STOP ' + str(stop))
            self.write('SOUR2:VOLT:STEP ' + str(step))
        else:
            return print('Invalid operation')

    def output_trigger(self, source_delay, acquisition_delay):
        self.write(':TRIG:TRAN:DEL '+str(source_delay))
        self.write(':TRIG:ACQ:DEL '+str(acquisition_delay))

    def source_wait_time(self, auto, source_wait, offset, gain):
        if auto == 'off' and source_wait == 'on':
            self.write(':SOUR:WAIT ON')
            self.write(':SOUR:WAIT:AUTO OFF')
            self.write(':SOUR:WAIT:GAIN '+str(gain))
            self.write(':SOUR:WAIT:OFFS ' + str(offset))
        elif auto == 'on' and source_wait == 'on':
            self.write(':SOUR:WAIT ON')
            self.write(':SOUR:WAIT:AUTO ON')
        elif source_wait == 'off':
            self.write(':SOUR:WAIT OFF')
            self.write(':SOUR:WAIT:AUTO OFF')
        else:
            return print('Invalid operation')

    def measurement_mode(self, mode, switch):
        if switch == 'on':
            if mode == 'all':
                self.write(':SENS:FUNC:ALL')
            elif mode == 'voltage':
                self.write('SENS:FUNC ""VOLT""')
            elif mode == 'current':
                self.write(':SENS:FUNC ""CURR""')
            elif mode == 'resistance':
                self.write(':SENS:FUNC ""RES""')
            else:
                return print('Invalid operation')
        if switch == 'off':
            if mode == 'all':
                self.write(':SENS:FUNC:OFF:ALL')
            elif mode == 'voltage':
                self.write('SENS:FUNC:OFF ""VOLT""')
            elif mode == 'current':
                self.write(':SENS:FUNC:OFF ""CURR""')
            elif mode == 'resistance':
                self.write(':SENS:FUNC:OFF ""RES""')
            else:
                return print('Invalid operation_measurement')

    def measurement_speed(self, mode, auto, speed):
        if mode == 'voltage':
            if auto == 'on':
                self.write(':SENS:VOLT:NPLC:AUTO ON')
            elif auto == 'off':
                self.write(':SENS:VOLT:NPLC OFF')
                self.write(':SENS:VOLT:NPLC '+str(speed))
            else:
                return print('Invalid operation')
        elif mode == 'current':
            if auto == 'on':
                self.write(':SENS:CURR:NPLC:AUTO ON')
            elif auto == 'off':
                self.write(':SENS:CURR:NPLC OFF')
                self.write(':SENS:CURR:NPLC '+str(speed))
            else:
                return print('Invalid operation')
        elif mode == 'resistance':
            if auto == 'on':
                self.write(':SENS:RES:NPCL:AUTO ON')
            elif auto == 'off':
                self.write(':SENS:RES:NPLC OFF')
                self.write(':SENS:RES:NPLC '+str(speed))
            else:
                return print('Invalid operation')
        else:
            return print('Invalid operation')

    def measurement_range(self, mode, auto, measurement_range):
        if auto == 'off':
            if mode == 'Voltage':
                self.write(':SENS:VOLT:RANG:AUTO OFF')
                self.write(':SENS:VOLT:RANG:UPP '+str(measurement_range))
            elif mode == 'Current':
                self.write(':SENS:CURR:RANG:AUTO OFF')
                self.write(':SENS:CURR:RANG:UPP '+str(measurement_range))
            elif mode == 'Resistance':
                self.write(':SENS:RES:RANG:AUTO OFF')
                self.write(':SENS:RES:RANG:UPP '+str(measurement_range))
            else:
                return print('Invalid operation')
        else:
            return

    def measurement_auto_range_off(self, mode, status):
        if mode == 'Voltage':
            if status == 'on':
                self.write(':SENS:VOLT:RANG:AUTO ON')
            elif status == 'off':
                self.write(':SENS:VOLT:RANG:AUTO OFF')
            else:
                return print('Invalid operation.')

        elif mode == 'Current':
            if status == 'on':
                self.write(':SENS:CURR:RANG:AUTO ON')
            elif status == 'off':
                self.write(':SENS:CURR:RANG:AUTO OFF')
            else:
                return print('Invalid operation.')

        elif mode == 'Resistance':
            if status == 'on':
                self.write(':SENS:RES:RANG:AUTO ON')
            elif status == 'off':
                self.write(':SENS:RES:RANG:AUTO OFF')
            else:
                return print('Invalid operation.')
        else:
            return print('Invalid operation.')

    def measurement_auto_range(self, mode, operation_mode):
        if mode == 'Voltage':
            if operation_mode == 'Normal':
                self.write(':SENS:VOLT:RANG:AUTO:MODE NORM')
            elif operation_mode == 'Resolution':
                self.write(':SENS:VOLT:RANG:AUTO:MODE RES')
            elif operation_mode == 'Speed':
                self.write(':SENS:VOLT:RANG:AUTO:MODE SPE')
            else:
                return print('Invalid operation')

        elif mode == 'Current':
            if operation_mode == 'Normal':
                self.write(':SENS:CURR:RANG:AUTO:MODE NORM')
            elif operation_mode == 'Resolution':
                self.write(':SENS:CURR:RANG:AUTO:MODE RES')
            elif operation_mode == 'Speed':
                self.write(':SENS:CURR:RANG:AUTO:MODE SPE')
            else:
                return print('Invalid operation')

        elif mode == 'Resistance':
            if operation_mode == 'Normal':
                self.write(':SENS:RES:RANG:AUTO:MODE NORM')
            elif operation_mode == 'Resolution':
                self.write(':SENS:RES:RANG:AUTO:MODE RES')
            elif operation_mode == 'Speed':
                self.write(':SENS:RES:RANG:AUTO:MODE SPE')
            else:
                return print('Invalid operation')
        else:
            return print('Invalid operation')

    def measurement_wait_time(self, auto, measurement_wait, gain, offset):
        if auto == 'off' and measurement_wait == 'on':
            self.write(':SENS:WAIT ON')
            self.write(':SENS:WAIT:AUTO OFF')
            self.write(':SENS:WAIT:GAIN '+str(gain))
            self.write(':SENS:WAIT:OFFS ' + str(offset))
        elif auto == 'on' and measurement_wait == 'on':
            self.write(':SENS:WAIT ON')
            self.write(':SENS:WAIT:AUTO ON')
        elif measurement_wait == 'off':
            self.write(':SENS:WAIT OFF')
            self.write(':SENS:WAIT:AUTO OFF')
        else:
            return print('Invalid operation')

        if offset != 0:
            self.write(':SENS:WAIT:OFFS ' + str(offset))

    def measurement_trigger_count(self, trigger_time, count):
        self.write(':TRIG:SOUR TIM')
        self.write(':TRIG:TIM '+str(trigger_time))
        self.write(':TRIG:COUN '+str(count))

    def measurement_trigger_count_auto(self, count):
        self.write(':TRIG:SOUR AINT')
        self.write(':TRIG:COUN '+str(count))

    def measurement_trigger_count_auto_c2(self, count):
        self.write(':TRIG2:SOUR AINT')
        self.write(':TRIG2:COUN '+str(count))

    def measure(self):
        self.write(":INIT (@1)")

    def measure_c2(self):
        self.write(":INIT (@2)")

    def retrieve_data(self, data_type):
        if data_type == "current":
            self.write("FETC:ARR:CURR? (@1)")
            currents = self.read()
            return currents
        elif data_type == "time":
            self.write("FETC:ARR:TIME? (@1)")
            times = self.read()
            return times
        elif data_type == "voltage":
            self.write("FETC:ARR:VOLT? (@1)")
            voltages = self.read()
            return voltages
        else:
            return print('Invalid operation')

    def data_type_obtain(self, amount):
        if amount == 2:
            self.write("FORM:ELEM:SENS VOLT, CURR")
        elif amount == 3:
            self.write("FORM:ELEM:SENS VOLT, CURR, TIME")
        else:
            return print('Invalid operation')

if __name__ == "__main__":
    Agilent().output_trigger('0.5', '2')
    Agilent().pulse_output('voltage', '0.5', '1.5', '0', '1')
