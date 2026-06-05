import sys
import glob
import time
from enum import Enum
from multiprocessing import Process, Array, Lock

import serial


class ServoCommands(Enum):
    INC = "\x01"
    DEC = "\x02"
    STOP = "\x03"
    LASER_OFF = "\x04"
    LASER_ON = "\x05"
    IGNORE = "\x06"


STOP_SIGNAL = b"\x03\x03"


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


class Servo:
    def __init__(self, port=None, baudrate=9600, timeout=0.1):
        if port is None:
            ports = serial_ports()
            if len(ports) == 0:
                raise RuntimeError("No available serial ports detected. Please connect the servo controller and try again.")
            print(f"Servo: available serial ports: {ports}")
            port = ports[0]
            print(f"Servo: selected serial port {port}")
        else:
            print(f"Servo: using explicit serial port {port}")

        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

        self.stop_signal = self.compose_signal(ServoCommands.STOP, ServoCommands.STOP)
        self._prev_signal = self.stop_signal

    def close(self):
        self._send(self.stop_signal)
        self.ser.close()

    def update(self, yaw=ServoCommands.STOP, pitch=ServoCommands.STOP):
        signal = self.compose_signal(yaw, pitch)

        self.update_raw(signal)

    def update_raw(self, signal):
        if signal == self._prev_signal:
            return

        self._send(signal)
        self._prev_signal = signal

    def _send(self, signal):
        print(signal)
        self.ser.write(signal)

    @staticmethod
    def compose_signal(yaw, pitch):
        return f"{yaw.value}{pitch.value}".encode()

    stop_signal = compose_signal.__func__(ServoCommands.STOP, ServoCommands.STOP)


class ServoWorker():
    def __init__(self, port=None):
        self.lck = Lock()
        self.signal = Array('c', Servo.stop_signal)

        self.process = Process(
            target=self._worker,
            args=(self.signal, self.lck, port)
        )
        self.process.daemon = True
        self.process.start()

    @staticmethod
    def _worker(signal, lck, port):
        servo = None
        try:
            servo = Servo(port=port)
            while True:
                with lck:
                    signal_val = signal.value
                if signal_val == b"":
                    break
                servo.update_raw(signal_val)
                time.sleep(1e-4)
        except Exception as e:
            print(f"Servo worker error: {e}")
            sys.stdout.flush()
            return
        finally:
            if servo is None:
                return
            servo.update(ServoCommands.LASER_OFF, ServoCommands.IGNORE)
            servo.update()
            servo.close()

    def update(self, yaw, pitch):
        with self.lck:
            self.signal.value = Servo.compose_signal(yaw, pitch)

    def join(self):
        self.signal.value = b"\x00\x00"
        self.process.join()
