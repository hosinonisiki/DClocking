# Defines methods for module manipulation

# Base class of all modules
class ModuleBase():
    # Format: parameter_list[(int)address] = {"name": (str)name, "width": (int)width]
    parameter_list = {}
    # Format: alias_list[(str)alias] = (int)address
    alias_list = {}

    def __init__(self, bus, name):
        self.bus = bus
        self.name = name

    def reset(self):
        self.bus.post_string(":BUS_.%s.CTRL.RSTR!" % self.name)
        self.bus.post_string(":BUS_.%s.CTRL.SETR!" % self.name)
        self.bus.post_string(":BUS_.%s.CTRL.RSTC!" % self.name)
        self.bus.post_string(":BUS_.%s.CTRL.SETC!" % self.name)

    def set(self, address, data):
        address = self.process_address(address)
        if self.parameter_list.get(address, {"name": "UNKNOWN", "width": 32})["width"] != 1:
            raise ValueError("Invalid address or parameter name, should be a boolean parameter")
        if data in [1, True, "1", "True", "true", "on", "ON"]:
            data = 1
        elif data in [0, False, "0", "False", "false", "off", "OFF"]: 
            data = 0
        else:
            raise ValueError("Invalid boolean value")
        return self.bus.write(self.name, address, data)

    def write(self, address, data, hold = False):
        # Further type casting is left to the bus
        # Only handle negative integers and parameter alias here
        address = self.process_address(address)
        if type(data) == int and data < 0:
            width = self.parameter_list.get(address, {"name": "UNKNOWN", "width": 32})["width"]
            data = 2 ** width + data
        return self.bus.write(self.name, address, data, hold)

    def read(self, address):
        address = self.process_address(address)
        return self.bus.read(self.name, address)
    
    def process_address(self, address):
        if type(address) == str:
            address = self.alias_list.get(address, None)
        if address is None:
            raise ValueError("Invalid address or parameter name")
        return address
    
class ModulePID(ModuleBase):
    parameter_list = {
        0: {"name": "gain_p", "width": 24},
        1: {"name": "gain_i", "width": 32},
        2: {"name": "gain_d", "width": 24},
        3: {"name": "setpoint", "width": 16},
        4: {"name": "limit_integral", "width": 16},
        5: {"name": "limit_sum", "width": 16}
    }
    alias_list = {
        "gain_p": 0, "p": 0, "kp" : 0, "k_p": 0,
        "gain_i": 1, "i": 1, "ki" : 1, "k_i": 1,
        "gain_d": 2, "d": 2, "kd" : 2, "k_d": 2,
        "setpoint": 3, "set": 3,
        "limit_integral": 4, "limit_i": 4,
        "limit_sum": 5, "limit": 5
    }

class ModuleScaler(ModuleBase):
    parameter_list = {
        0: {"name": "scale", "width": 24},
        1: {"name": "bias", "width": 16},
        2: {"name": "upper_limit", "width": 16},
        3: {"name": "lower_limit", "width": 16},
        4: {"name": "enable_wrapping", "width": 1}
    }
    alias_list = {
        "scale": 0, "gain": 0,
        "bias": 1, "offset": 1,
        "upper": 2, "upper_limit": 2,
        "lower": 3, "lower_limit": 3,
        "enable_wrapping": 4, "wrap": 4, "wrapping": 4
    }