# Defines methods to map uart transmissions to bus commands

import uart

class Bus():
    def __init__(self, serial):
        self.serial = serial

    def post_string(self, message):
        self.serial.post(message.encode())

    def post_bytes(self, message):
        self.serial.post(message)

    def write(self, module, address, data, hold = False):
        module = module.upper()
        if type(address) == int:
            address = address.to_bytes(4, "big")
        elif type(address) == str:
            address = bytes.fromhex(address)
        if type(data) == int:
            data = data.to_bytes(4, "big")
        elif type(data) == str:
            data = bytes.fromhex(data)
        message = b":BUS_." + module.encode() + b".WRTE.ADDR." + address + b".DATA." + data
        if hold:
            message += b".HOLD!"
        else:
            message += b"!"
        self.serial.post(message)

    def read(self, module, address):
        module = module.upper()
        if type(address) == int:
            address = address.to_bytes(4, "big")
        elif type(address) == str:
            address = int(address, 16).to_bytes(4, "big")
        message = b":BUS_." + module.encode() + b".READ.ADDR." + address + b"!"
        self.serial.post(message)