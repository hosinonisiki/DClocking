import numpy as np
import scipy.signal as signal

# Defines methods for module manipulation

# Base class of all modules
class ModuleBase():
    # Format: parameter_list[(int)address] = {"name": (str)name, "width": (int)width]
    parameter_list = {}
    # Format: deduced_parameter_list[(str)name] = method
    deduced_parameter_list = {}
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
        address = self.process_designator(address)
        if self.parameter_list.get(address, {"name": "UNKNOWN", "width": 32})["width"] != 1:
            raise ValueError("Invalid address or parameter name, should be a boolean parameter")
        if data in [1, True, "1", "True", "true", "on", "ON"]:
            data = 1
        elif data in [0, False, "0", "False", "false", "off", "OFF"]: 
            data = 0
        else:
            raise ValueError("Invalid boolean value")
        return self.bus.write(self.name, address, data)

    def write(self, designator, data, hold = False):
        # Further type casting is left to the bus
        # Only handle negative integers and parameter alias here
        ret = self.process_designator(designator)
        if type(ret) == int:
            address = ret
            if type(data) == int and data < 0:
                width = self.parameter_list.get(address, {"name": "UNKNOWN", "width": 32})["width"]
                data = 2 ** width + data
            return self.bus.write(self.name, address, data, hold)
        elif callable(ret):
            address_data_pairs = ret(data)
            for addr, dat in address_data_pairs[:-1]:
                if type(dat) == int and dat < 0:
                    width = self.parameter_list.get(addr, {"name": "UNKNOWN", "width": 32})["width"]
                    dat = 2 ** width + dat
                self.bus.write(self.name, addr, dat, True)
            return self.bus.write(self.name, address_data_pairs[-1][0], address_data_pairs[-1][1], hold)
        

    def read(self, designator):
        ret = self.process_designator(designator)
        if type(ret) == int:
            address = ret
            return self.bus.read(self.name, address)
        elif callable(ret):
            func = ret
            address_list, formula = func()
            data_list = [self.bus.read(self.name, addr) for addr in address_list]
            return formula(data_list)

    def process_designator(self, designator):
        if type(designator) == str:
            address = self.alias_list.get(designator, None)
            if address is None:
                parameter_func = self.deduced_parameter_list.get(designator, None)
                if parameter_func is None:
                    raise ValueError("Invalid address or parameter name")
                return parameter_func(self)
            return address
        return designator
    
class ModulePID(ModuleBase):
    parameter_list = {
        0: {"name": "gain_p", "width": 24},
        1: {"name": "gain_i", "width": 32},
        2: {"name": "gain_d", "width": 24},
        3: {"name": "setpoint", "width": 16},
        4: {"name": "limit_integral", "width": 16},
        5: {"name": "limit_sum", "width": 16},
        6: {"name": "leak_digit", "width": 32},
        7: {"name": "enable_auto_reset", "width": 1}
    }
    alias_list = {
        "gain_p": 0, "p": 0, "kp" : 0, "k_p": 0,
        "gain_i": 1, "i": 1, "ki" : 1, "k_i": 1,
        "gain_d": 2, "d": 2, "kd" : 2, "k_d": 2,
        "setpoint": 3, "set": 3,
        "limit_integral": 4, "limit_i": 4,
        "limit_sum": 5, "limit": 5,
        "leak_digit": 6, "leak": 6, # Only accepts 2^n values, from 1 to 2^31
        "enable_auto_reset": 7, "auto_reset": 7, "auto": 7
    }
    # Overall gain(dB) = 20 * log10(gain_p / 2^16)
    # PI corner = fs / 2pi * (gain_i / gain_p) / 2^16
    # PD corner = fs / 2pi * (gain_p / gain_d)
    # leak constant alpha = 1 - 1 / leak_digit / 2^8
    # Saturation gain(dB) = 20 * log10(gain_i / (1 - alpha) / 2^32) = 20 * log10(gain_i * leak_digit * 256 / 2^32)
    # Saturation turning frequency = (1 - alpha) * fs / 2pi = fs / 2pi / leak_digit / 256
    deduced_parameter_list = {
        "overall_gain": lambda self: self.overall_gain_func,
        "pi_corner": lambda self: self.pi_corner_func,
        "pd_corner": lambda self: self.pd_corner_func,
        "saturation_gain": lambda self: self.saturation_gain_func,
        "saturation_turning_frequency": lambda self: self.saturation_turning_frequency_func
    }

    # Sampling frequency involving integral is set to 125MHz at half system clock due to pipelining
    def overall_gain_func(self, data = None):
        if data != None:
            # Write, return address-data pairs
            target_gain_p = int(round(2 ** 16 * 10 ** (data / 20)))
            current_gain_p = int.from_bytes(self.read("gain_p"), "big")
            current_gain_i = int.from_bytes(self.read("gain_i"), "big")
            current_gain_d = int.from_bytes(self.read("gain_d"), "big")
            if current_gain_p != 0:
                scale_factor = target_gain_p / current_gain_p
                target_gain_i = int(round(current_gain_i * scale_factor))
                target_gain_d = int(round(current_gain_d * scale_factor))
                if target_gain_i >= 2 ** 31 or target_gain_i < -2 ** 31 or target_gain_d >= 2 ** 23 or target_gain_d < -2 ** 23:
                    raise ValueError("Resulting gain_i or gain_d is out of range")
                return [(0, target_gain_p), (1, target_gain_i), (2, target_gain_d)]
            else:
                return [(0, target_gain_p)]
        else:
            # Read, return address list and formula
            address_list = [0]
            def formula(data_list):
                gain_p = int.from_bytes(data_list[0], "big")
                if gain_p == 0:
                    return -np.inf
                return 20 * np.log10(gain_p / 2 ** 16)
            return address_list, formula
        
    def pi_corner_func(self, data = None):
        if data != None:
            # Write, return address-data pairs
            current_gain_p = int.from_bytes(self.read("gain_p"), "big")
            target_gain_i = int(round(current_gain_p * data * 2 * np.pi / 125000000 * 2 ** 16))
            if target_gain_i >= 2 ** 31 or target_gain_i < -2 ** 31:
                raise ValueError("Resulting gain_i is out of range")
            return [(1, target_gain_i)]
        else:
            # Read, return address list and formula
            address_list = [0, 1]
            def formula(data_list):
                gain_p = int.from_bytes(data_list[0], "big")
                gain_i = int.from_bytes(data_list[1], "big")
                if gain_p == 0:
                    return np.inf
                return (gain_i / gain_p) * 125000000 / (2 * np.pi * 2 ** 16)
            return address_list, formula

    def pd_corner_func(self, data = None):
        if data != None:
            # Write, return address-data pairs
            if data != 0:
                current_gain_p = int.from_bytes(self.read("gain_p"), "big")
                target_gain_d = int(round(current_gain_p * 250000000 / (data * 2 * np.pi)))
                if target_gain_d >= 2 ** 23 or target_gain_d < -2 ** 23:
                    raise ValueError("Resulting gain_d is out of range")
                return [(2, target_gain_d)]
            else:
                raise ValueError("PD corner frequency cannot be zero")
        else:
            # Read, return address list and formula
            address_list = [0, 1]
            def formula(data_list):
                gain_p = int.from_bytes(data_list[0], "big")
                gain_d = int.from_bytes(data_list[1], "big")
                if gain_d == 0:
                    return np.inf
                return (gain_p / gain_d) * 250000000 / (2 * np.pi)
            return address_list, formula

    def saturation_gain_func(self, data = None):
        if data != None:
            # Write, return address-data pairs
            current_gain_i = int.from_bytes(self.read("gain_i"), "big")
            if current_gain_i != 0:
                log_target_leak_digit = int(round(np.log2((10 ** (data / 20)) * (2 ** 32) / (current_gain_i * 256))))
                if log_target_leak_digit <= -1:
                    target_leak_digit = 1
                    print("Warning: saturation gain too low, setting to maximum leak")
                elif log_target_leak_digit >= 32:
                    target_leak_digit = 0
                    print("Warning: saturation gain too high, setting to no leak")
                else:
                    target_leak_digit = 2 ** log_target_leak_digit
                    print(f"Implemented saturation gain: {20 * np.log10(current_gain_i * target_leak_digit * 256 / (2 ** 32))} dB, requested: {data} dB")
                return [(6, target_leak_digit)]
            else:
                raise ValueError("gain_i is zero, cannot set saturation gain")
        else:
            # Read, return address list and formula
            address_list = [1, 6]
            def formula(data_list):
                gain_i = int.from_bytes(data_list[0], "big")
                if gain_i == 0:
                    raise ValueError("gain_i is zero, cannot read saturation gain")
                leak_digit = int.from_bytes(data_list[1], "big")
                if leak_digit == 0:
                    return np.inf
                return 20 * np.log10(gain_i * leak_digit * 256 / (2 ** 32))
            return address_list, formula

    def saturation_turning_frequency_func(self, data = None):
        if data != None:
            # Write, return address-data pairs
            if data != 0:
                log_target_leak_digit = int(round(np.log2(125000000 / (data * 2 * np.pi * 256))))
                if log_target_leak_digit <= -1:
                    target_leak_digit = 1
                    print("Warning: saturation turning frequency too high, setting to maximum leak")
                elif log_target_leak_digit >= 32:
                    target_leak_digit = 0
                    print("Warning: saturation turning frequency too low, setting to no leak")
                else:
                    target_leak_digit = 2 ** log_target_leak_digit
                    print(f"Implemented saturation turning frequency: {125000000 / (target_leak_digit * 256 * 2 * np.pi)} Hz, requested: {data} Hz")
                return [(6, target_leak_digit)]
            else:
                return [(6, 0)] # No leak
        else:
            # Read, return address list and formula
            address_list = [6]
            def formula(data_list):
                leak_digit = int.from_bytes(data_list[0], "big")
                if leak_digit == 0:
                    return 0
                return 125000000 / (leak_digit * 256 * 2 * np.pi)
            return address_list, formula

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

class ModuleAccumulator(ModuleBase):
    parameter_list = {
        0: {"name": "low", "width": 32},
        1: {"name": "high", "width": 32},
        3: {"name": "enable_auto_reset", "width": 1}
    }
    alias_list = {
        "low": 0,
        "high": 1,
        "enable_auto_reset": 3, "auto_reset": 3, "auto": 3
    }
    def set_freq(self, freq, sample_rate = 250000000):
        if freq < 0 or freq > sample_rate / 2:
            raise ValueError("Frequency must be between 0 and Nyquist frequency")
        var = int(round(freq / sample_rate * 2 ** 64))
        self.write(0, var % (2 ** 32), hold = True)
        self.write(1, var // (2 ** 32))

class ModuleFIRFilter(ModuleBase):
    parameter_list = {
        0: {"name": "coef_0", "width": 24},
        1: {"name": "coef_1", "width": 24},
        2: {"name": "coef_2", "width": 24},
        3: {"name": "coef_3", "width": 24},
        4: {"name": "coef_4", "width": 24},
        5: {"name": "coef_5", "width": 24},
        6: {"name": "coef_6", "width": 24},
        7: {"name": "coef_7", "width": 24},
        8: {"name": "coef_8", "width": 24},
        9: {"name": "coef_9", "width": 24},
        10: {"name": "coef_10", "width": 24},
        11: {"name": "coef_11", "width": 24},
        12: {"name": "coef_12", "width": 24},
        13: {"name": "coef_13", "width": 24},
        14: {"name": "coef_14", "width": 24},
        15: {"name": "coef_15", "width": 24},
        16: {"name": "coef_16", "width": 24},
        17: {"name": "coef_17", "width": 24},
        18: {"name": "coef_18", "width": 24},
        19: {"name": "coef_19", "width": 24},
        20: {"name": "coef_20", "width": 24},
        21: {"name": "coef_21", "width": 24},
        22: {"name": "coef_22", "width": 24},
        23: {"name": "coef_23", "width": 24},
        24: {"name": "coef_24", "width": 24},
        25: {"name": "coef_25", "width": 24},
        26: {"name": "coef_26", "width": 24},
        27: {"name": "coef_27", "width": 24},
        28: {"name": "coef_28", "width": 24},
        29: {"name": "coef_29", "width": 24},
        30: {"name": "coef_30", "width": 24},
        31: {"name": "coef_31", "width": 24},
        32: {"name": "coef_32", "width": 24},
        33: {"name": "coef_33", "width": 24},
        34: {"name": "coef_34", "width": 24},
        35: {"name": "coef_35", "width": 24},
        36: {"name": "coef_36", "width": 24},
        37: {"name": "coef_37", "width": 24},
        38: {"name": "coef_38", "width": 24},
        39: {"name": "coef_39", "width": 24},
        40: {"name": "coef_40", "width": 24},
        41: {"name": "coef_41", "width": 24},
        42: {"name": "coef_42", "width": 24},
        43: {"name": "coef_43", "width": 24},
        44: {"name": "coef_44", "width": 24},
        45: {"name": "coef_45", "width": 24},
        46: {"name": "coef_46", "width": 24},
        47: {"name": "coef_47", "width": 24},
        48: {"name": "coef_48", "width": 24},
        49: {"name": "coef_49", "width": 24},
        50: {"name": "coef_50", "width": 24},
        51: {"name": "coef_51", "width": 24},
        52: {"name": "coef_52", "width": 24},
        53: {"name": "coef_53", "width": 24},
        54: {"name": "coef_54", "width": 24},
        55: {"name": "coef_55", "width": 24},
        56: {"name": "coef_56", "width": 24},
        57: {"name": "coef_57", "width": 24},
        58: {"name": "coef_58", "width": 24},
        59: {"name": "coef_59", "width": 24},
        60: {"name": "coef_60", "width": 24},
        61: {"name": "coef_61", "width": 24},
        62: {"name": "coef_62", "width": 24},
        63: {"name": "coef_63", "width": 24},
        64: {"name": "norm", "width": 18}
    }
    alias_list = {
        "coef_0": 0, "c0": 0, "coef0": 0,
        "coef_1": 1, "c1": 1, "coef1": 1,
        "coef_2": 2, "c2": 2, "coef2": 2,
        "coef_3": 3, "c3": 3, "coef3": 3,
        "coef_4": 4, "c4": 4, "coef4": 4,
        "coef_5": 5, "c5": 5, "coef5": 5,
        "coef_6": 6, "c6": 6, "coef6": 6,
        "coef_7": 7, "c7": 7, "coef7": 7,
        "coef_8": 8, "c8": 8, "coef8": 8,
        "coef_9": 9, "c9": 9, "coef9": 9,
        "coef_10": 10, "c10": 10, "coef10": 10,
        "coef_11": 11, "c11": 11, "coef11": 11,
        "coef_12": 12, "c12": 12, "coef12": 12,
        "coef_13": 13, "c13": 13, "coef13": 13,
        "coef_14": 14, "c14": 14, "coef14": 14,
        "coef_15": 15, "c15": 15, "coef15": 15,
        "coef_16": 16, "c16": 16, "coef16": 16,
        "coef_17": 17, "c17": 17, "coef17": 17,
        "coef_18": 18, "c18": 18, "coef18": 18,
        "coef_19": 19, "c19": 19, "coef19": 19,
        "coef_20": 20, "c20": 20, "coef20": 20,
        "coef_21": 21, "c21": 21, "coef21": 21,
        "coef_22": 22, "c22": 22, "coef22": 22,
        "coef_23": 23, "c23": 23, "coef23": 23,
        "coef_24": 24, "c24": 24, "coef24": 24,
        "coef_25": 25, "c25": 25, "coef25": 25,
        "coef_26": 26, "c26": 26, "coef26": 26,
        "coef_27": 27, "c27": 27, "coef27": 27,
        "coef_28": 28, "c28": 28, "coef28": 28,
        "coef_29": 29, "c29": 29, "coef29": 29,
        "coef_30": 30, "c30": 30, "coef30": 30,
        "coef_31": 31, "c31": 31, "coef31": 31,
        "coef_32": 32, "c32": 32, "coef32": 32,
        "coef_33": 33, "c33": 33, "coef33": 33,
        "coef_34": 34, "c34": 34, "coef34": 34,
        "coef_35": 35, "c35": 35, "coef35": 35,
        "coef_36": 36, "c36": 36, "coef36": 36,
        "coef_37": 37, "c37": 37, "coef37": 37,
        "coef_38": 38, "c38": 38, "coef38": 38,
        "coef_39": 39, "c39": 39, "coef39": 39,
        "coef_40": 40, "c40": 40, "coef40": 40,
        "coef_41": 41, "c41": 41, "coef41": 41,
        "coef_42": 42, "c42": 42, "coef42": 42,
        "coef_43": 43, "c43": 43, "coef43": 43,
        "coef_44": 44, "c44": 44, "coef44": 44,
        "coef_45": 45, "c45": 45, "coef45": 45,
        "coef_46": 46, "c46": 46, "coef46": 46,
        "coef_47": 47, "c47": 47, "coef47": 47,
        "coef_48": 48, "c48": 48, "coef48": 48,
        "coef_49": 49, "c49": 49, "coef49": 49,
        "coef_50": 50, "c50": 50, "coef50": 50,
        "coef_51": 51, "c51": 51, "coef51": 51,
        "coef_52": 52, "c52": 52, "coef52": 52,
        "coef_53": 53, "c53": 53, "coef53": 53,
        "coef_54": 54, "c54": 54, "coef54": 54,
        "coef_55": 55, "c55": 55, "coef55": 55,
        "coef_56": 56, "c56": 56, "coef56": 56,
        "coef_57": 57, "c57": 57, "coef57": 57,
        "coef_58": 58, "c58": 58, "coef58": 58,
        "coef_59": 59, "c59": 59, "coef59": 59,
        "coef_60": 60, "c60": 60, "coef60": 60,
        "coef_61": 61, "c61": 61, "coef61": 61,
        "coef_62": 62, "c62": 62, "coef62": 62,
        "coef_63": 63, "c63": 63, "coef63": 63,
        "norm": 64
    }
    def load_coef(self, coef_list, norm):
        if len(coef_list) != 64:
            raise ValueError("Coefficient list must have exactly 64 elements")
        coef_list = np.array(coef_list)
        if max(abs(coef_list)) > 1:
            raise ValueError("Coefficient values must be normalized between -1 and 1")
        coef_int = np.round(coef_list * (2 ** 23 - 1))
        for i in range(64):
            if coef_int[i] < 0:
                coef_int[i] = 2 ** 24 + coef_int[i]
            self.write(i, int(coef_int[i]), hold = True)
        if norm < 1 or norm > 16:
            raise ValueError("Normalization factor must be between 1 and 16")
        self.write(64, int(norm * (2 ** 13 - 1)))
        return
    
    def design_lowpass(self, freq_pass, freq_stop, freq_sample, weight = 1):
        coef = signal.remez(64, [0, freq_pass, freq_stop, freq_sample / 2], [1, 0], fs = freq_sample, weight = [1, weight])
        coef = np.array(coef)
        coef = coef / np.max(np.abs(coef)) * 0.98
        l1_norm = sum(np.abs(coef))
        norm = 32 / l1_norm * 0.98
        if norm < 1 or norm > 16:
            raise ValueError("Designed filter normalization factor is out of range (1 to 16). Try increasing the passband frequency.")
        self.load_coef(coef, norm)

class ModuleLinearTransformer(ModuleBase):
    parameter_list = {
        0: {"name": "coef_aa", "width": 16},
        1: {"name": "coef_ab", "width": 16},
        2: {"name": "coef_ba", "width": 16},
        3: {"name": "coef_bb", "width": 16}
    }
    alias_list = {
        "coef_aa": 0, "a_to_a": 0,
        "coef_ab": 1, "b_to_a": 1,
        "coef_ba": 2, "a_to_b": 2,
        "coef_bb": 3, "b_to_b": 3
    }
    deduced_parameter_list = {
        "a00": lambda self: self.a00_func,
        "a01": lambda self: self.a01_func,
        "a10": lambda self: self.a10_func,
        "a11": lambda self: self.a11_func,
        "matrix": lambda self: self.matrix_func
    }

    def a00_func(self, data = None):
        if data != None:
            # Write, return address-data pairs
            if data < -1 or data > 1:
                raise ValueError("Coefficient must be between -1 and 1")
            coef_int = int(round(data * (2 ** 15 - 1)))
            if coef_int < 0:
                coef_int = 2 ** 16 + coef_int
            return [(0, coef_int)]
        else:
            # Read, return address list and formula
            address_list = [0]
            def formula(data_list):
                coef_int = int.from_bytes(data_list[0], "big")
                if coef_int >= 2 ** 15:
                    coef_int = coef_int - 2 ** 16
                return coef_int / (2 ** 15 - 1)
            return address_list, formula
        
    def a01_func(self, data = None):
        if data != None:
            # Write, return address-data pairs
            if data < -1 or data > 1:
                raise ValueError("Coefficient must be between -1 and 1")
            coef_int = int(round(data * (2 ** 15 - 1)))
            if coef_int < 0:
                coef_int = 2 ** 16 + coef_int
            return [(1, coef_int)]
        else:
            # Read, return address list and formula
            address_list = [1]
            def formula(data_list):
                coef_int = int.from_bytes(data_list[0], "big")
                if coef_int >= 2 ** 15:
                    coef_int = coef_int - 2 ** 16
                return coef_int / (2 ** 15 - 1)
            return address_list, formula
        
    def a10_func(self, data = None):
        if data != None:
            # Write, return address-data pairs
            if data < -1 or data > 1:
                raise ValueError("Coefficient must be between -1 and 1")
            coef_int = int(round(data * (2 ** 15 - 1)))
            if coef_int < 0:
                coef_int = 2 ** 16 + coef_int
            return [(2, coef_int)]
        else:
            # Read, return address list and formula
            address_list = [2]
            def formula(data_list):
                coef_int = int.from_bytes(data_list[0], "big")
                if coef_int >= 2 ** 15:
                    coef_int = coef_int - 2 ** 16
                return coef_int / (2 ** 15 - 1)
            return address_list, formula
        
    def a11_func(self, data = None):
        if data != None:
            # Write, return address-data pairs
            if data < -1 or data > 1:
                raise ValueError("Coefficient must be between -1 and 1")
            coef_int = int(round(data * (2 ** 15 - 1)))
            if coef_int < 0:
                coef_int = 2 ** 16 + coef_int
            return [(3, coef_int)]
        else:
            # Read, return address list and formula
            address_list = [3]
            def formula(data_list):
                coef_int = int.from_bytes(data_list[0], "big")
                if coef_int >= 2 ** 15:
                    coef_int = coef_int - 2 ** 16
                return coef_int / (2 ** 15 - 1)
            return address_list, formula

    def matrix_func(self, data = None):
        if not data is None:
            # Write, return address-data pairs
            if type(data) != np.ndarray or data.shape != (2, 2):
                raise ValueError("Input data must be a 2x2 numpy array")
            # Normalize to 1 in terms of l1 norm
            if np.abs(data[0,0]) + np.abs(data[0,1]) != 0:
                data[0] = data[0] / (np.abs(data[0,0]) + np.abs(data[0,1]))
            if np.abs(data[1,0]) + np.abs(data[1,1]) != 0:
                data[1] = data[1] / (np.abs(data[1,0]) + np.abs(data[1,1]))
            address_data_pairs = []
            address_data_pairs.append((0, int(round(data[0,0] * (2 ** 15 - 1))) % (2 ** 16)))
            address_data_pairs.append((1, int(round(data[0,1] * (2 ** 15 - 1))) % (2 ** 16)))
            address_data_pairs.append((2, int(round(data[1,0] * (2 ** 15 - 1))) % (2 ** 16)))
            address_data_pairs.append((3, int(round(data[1,1] * (2 ** 15 - 1))) % (2 ** 16)))
            return address_data_pairs
        else:
            # Read, return address list and formula
            address_list = [0, 1, 2, 3]
            def formula(data_list):
                matrix = np.zeros((2, 2))
                for i in range(2):
                    for j in range(2):
                        coef_int = int.from_bytes(data_list[i * 2 + j], "big")
                        if coef_int >= 2 ** 15:
                            coef_int = coef_int - 2 ** 16
                        matrix[i, j] = coef_int / 2 ** 15
                return matrix
            return address_list, formula
        
class ModulePDHFSM(ModuleBase):
    parameter_list = {
        0: {"name": "pc_cmd", "width": 2},
        1: {"name": "thre_sig_lock", "width": 16},
        2: {"name": "thre_sig_scan", "width": 16},
        3: {"name": "time_scan", "width": 32},
        4: {"name": "time_lock", "width": 32}
    }
    alias_list = {
        "pc_cmd": 0,
        "thre_sig_lock": 1, "threshold_signal_lock": 1,
        "thre_sig_scan": 2, "threshold_signal_scan": 2,
        "time_scan": 3,
        "time_lock": 4
    }