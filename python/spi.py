# Defines methods to map uart transmissions to spi commands

import uart

class Spi():
    def __init__(self, serial):
        self.serial = serial