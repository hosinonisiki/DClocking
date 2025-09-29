# Defines methods to map uart transmissions to spi commands

import uart
import time

class Spi():
    def __init__(self, serial):
        self.serial = serial

    def post_string(self, message):
        self.serial.post(message.encode())

    def post_bytes(self, message):
        self.serial.post(message)

    # Read and write are performed simmultaneously in spi communication
    def write(self, module, length, write_length, data):
        # lengths are represented in bytes
        module = module.upper().ljust(4, '_')
        if type(data) == int:
            raise Exception("Data for spi communication must not be an integer")
        elif type(data) == str:
            data = bytes.fromhex(data)
        # Check if data length is consistent with write length
        if len(data) != write_length:
            raise Exception("Data length is not consistent with write length")
        # Pad empty bytes
        data = data.ljust(4, b'\x00')
        message = b":SPI_." + module.encode() + b".\x00\x00" + (write_length * 8 - 1).to_bytes(1, "big") + (length * 8 - 1).to_bytes(1, "big") + b"." + data + b"!"
        response = self.serial.post(message)

        read_length = length - write_length
        time.sleep(0.1)
        return response[-1 - read_length:-1]

class SpiChip():
    def __init__(self, name, spi):
        self.name = name.upper().ljust(4, '_')
        self.spi = spi

    def write(self, data):
        return self.spi.write(self.name, 3, 3, data).hex()
    
    def read(self, data):
        return self.spi.write(self.name, 3, 2, data).hex()
