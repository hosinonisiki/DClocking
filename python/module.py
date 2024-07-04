# Defines methods for module manipulation

# Base class of all modules
class ModuleBase():
    def __init__(self, bus, name):
        self.bus = bus
        self.name = name

    def reset(self):
        self.bus.post_string(":BUS_.%s.CTRL.RSTR!" % self.name)
        self.bus.post_string(":BUS_.%s.CTRL.SETR!" % self.name)
        self.bus.post_string(":BUS_.%s.CTRL.RSTC!" % self.name)
        self.bus.post_string(":BUS_.%s.CTRL.SETC!" % self.name)

    def write(self, address, data, hold = False):
        return self.bus.write(self.name, address, data, hold)

    def read(self, address):
        return self.bus.read(self.name, address)