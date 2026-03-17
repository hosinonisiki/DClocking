import sys
import time
from PySide6.QtCore import QCoreApplication, QIODevice
from PySide6.QtSerialPort import QSerialPort

class QtSerial: 
    def __init__(self, port=None, baudrate=115200, parity="E", stopbits=1, bytesize=8, timeout=1, serial_instance=None):
        """
        初始化串口
        
        Args: 
            port: 串口名称（如果 serial_instance 为 None）
            baudrate: 波特率
            parity:  校验位
            stopbits: 停止位
            bytesize: 数据位
            timeout: 超时时间
            serial_instance: 已打开的 QSerialPort 实例（优先使用）
        """
        self.timeout = timeout
        self._buffer = bytearray()
        self._own_serial = False  # 标记是否需要自己管理串口
        
        if serial_instance is not None:
            # 使用外部传入的已打开串口
            if not isinstance(serial_instance, QSerialPort):
                raise TypeError("serial_instance must be a QSerialPort object")
            if not serial_instance.isOpen():
                raise Exception("Provided serial_instance is not open")
            self.serial = serial_instance
            self._own_serial = False
        else:
            # 自己创建并打开串口
            if port is None:
                raise ValueError("Either 'port' or 'serial_instance' must be provided")
            
            self.serial = QSerialPort()
            self.serial.setPortName(port)
            self.serial.setBaudRate(baudrate)

            # Parity Mapping
            parity_map = {
                "N": QSerialPort.NoParity,
                "E":  QSerialPort.EvenParity,
                "O": QSerialPort.OddParity,
                "M": QSerialPort.MarkParity,
                "S": QSerialPort.SpaceParity
            }
            self.serial.setParity(parity_map.get(parity, QSerialPort.NoParity))

            # Stopbits Mapping
            if stopbits == 1:
                self.serial.setStopBits(QSerialPort. OneStop)
            elif stopbits == 2:
                self.serial.setStopBits(QSerialPort.TwoStop)
            
            # Data Bits Mapping
            if bytesize == 8:
                self.serial.setDataBits(QSerialPort.Data8)
            elif bytesize == 7:
                self.serial.setDataBits(QSerialPort.Data7)

            if not self.serial.open(QIODevice.ReadWrite):
                raise Exception(f"Failed to open port {port}: {self.serial.error()}")
            
            self._own_serial = True

    def close(self):
        """只在自己打开的情况下才关闭串口"""
        if self._own_serial and self.serial.isOpen():
            self.serial.close()

    def write(self, data):
        if isinstance(data, str):
            data = data.encode()
        self.serial.write(data)
        self.serial.flush()
        # time.sleep(0.1)
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
                result = self._buffer[: split_index]
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
                raise Exception(f"Error in transmission.  Sent: {msg_str}, Received: {resp_str}")
        
        response = self. read_until(b"!")
        while True:
            if len(response) >= 6:
                if response[-6] == 46 or response[-6] == 58: # 46='. ', 58=':'
                    break
            
            new_data = self.read_until(b"!")
            if not new_data: # Timeout break
                break
            response += new_data

        if verbose:
            print(response)
        
        if not response.startswith(b":ACKN"):
            try:
                resp_str = response. decode()
            except:
                resp_str = str(response)
            raise Exception(f"Error in transmission. Received: {resp_str}")
        return response