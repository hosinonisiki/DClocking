import sys
import time
from PySide6.QtCore import QCoreApplication, QIODevice
from PySide6.QtSerialPort import QSerialPort

# QSerialPort requires a QCoreApplication instance to function correctly,
# even if we don't run the event loop with exec_().
if not QCoreApplication.instance():
    app = QCoreApplication(sys.argv)

class QtSerial:
    def __init__(self, port, baudrate=115200, parity="N", stopbits=1, bytesize=8, timeout=1):
        self.serial = QSerialPort()
        self.serial.setPortName(port)
        self.serial.setBaudRate(baudrate)

        # Parity Mapping
        parity_map = {
            "N": QSerialPort.NoParity,
            "E": QSerialPort.EvenParity,
            "O": QSerialPort.OddParity,
            "M": QSerialPort.MarkParity,
            "S": QSerialPort.SpaceParity
        }
        self.serial.setParity(parity_map.get(parity, QSerialPort.NoParity))

        # Stopbits Mapping
        if stopbits == 1:
            self.serial.setStopBits(QSerialPort.OneStop)
        elif stopbits == 2:
            self.serial.setStopBits(QSerialPort.TwoStop)
        
        # Data Bits Mapping
        if bytesize == 8:
            self.serial.setDataBits(QSerialPort.Data8)
        elif bytesize == 7:
            self.serial.setDataBits(QSerialPort.Data7)

        self.timeout = timeout
        self._buffer = bytearray()

        if not self.serial.open(QIODevice.ReadWrite):
            raise Exception(f"Failed to open port {port}: {self.serial.error()}")

    def close(self):
        self.serial.close()

    def write(self, data):
        if isinstance(data, str):
            data = data.encode()
        self.serial.write(data)
        # Blocking wait for write to complete
        if not self.serial.waitForBytesWritten(int(self.timeout * 1000)):
            print("Warning: Write timeout")

    def read_until(self, terminator=b'\n'):
        """
        Reads data from the serial port until the terminator is found.
        Returns the data up to and including the terminator.
        """
        start_time = time.time()
        
        while True:
            # Check if terminator is already in the buffer
            if terminator in self._buffer:
                split_index = self._buffer.find(terminator) + len(terminator)
                result = self._buffer[:split_index]
                self._buffer = self._buffer[split_index:]
                return bytes(result)

            # Check for timeout
            if (time.time() - start_time) > self.timeout:
                # Return whatever we have collected so far
                result = self._buffer
                self._buffer = bytearray()
                return bytes(result)

            # Wait for new data (blocking with small chunks)
            if self.serial.waitForReadyRead(50):
                data = self.serial.readAll().data()
                self._buffer.extend(data)

    def post(self, message, repeated=True, verbose=False):
        self.write(message)
        if repeated:
            response = self.read_until(b"!")
            while True:
                # Ensure response is long enough to check indices
                if len(response) >= 11:
                    if response[-6] == 46 and response[-11] == 46: # 46 is '.'
                        break
                
                new_data = self.read_until(b"!")
                if not new_data: # Timeout break
                    break
                response += new_data
            
            if verbose:
                print(response)
            if response != message:
                try:
                    msg_str = message.decode()
                    resp_str = response.decode()
                except:
                    msg_str = str(message)
                    resp_str = str(response)
                raise Exception(f"Error in transmission. Sent: {msg_str}, Received: {resp_str}")
        
        response = self.read_until(b"!")
        while True:
            if len(response) >= 6:
                if response[-6] == 46 or response[-6] == 58: # 46='.', 58=':'
                    break
            
            new_data = self.read_until(b"!")
            if not new_data: # Timeout break
                break
            response += new_data

        if verbose:
            print(response)
        
        if not response.startswith(b":ACKN"):
            try:
                resp_str = response.decode()
            except:
                resp_str = str(response)
            raise Exception(f"Error in transmission. Received: {resp_str}")
        return response

