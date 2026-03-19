import numpy as np
import re
from numbers import Real
import code

def convert_to_bits(integer, length):
    if integer >= 0:
        return bin(integer)[2:].zfill(length)
    else:
        return bin(integer + 2 ** length)[2:].zfill(length)
    
def array_to_fixed(array, format):
    array = array.astype(object)
    for index in np.ndindex(array.shape):
        array[index] = fixed(format, array[index])
    return array

def resize(obj, new_format):
    if isinstance(obj, fixed):
        return obj.resize(new_format)
    elif isinstance(obj, np.ndarray):
        for index in np.ndindex(obj.shape):
            obj[index].resize(new_format)
        return obj

class fixed:
    allow_overflow = False
    def __init__(self, format, value):
        pattern = r"^Q([0-9]+)\.([0-9]+)$"
        match = re.match(pattern, format)
        if not match:
            raise ValueError("Invalid format. Use Qm.n format.")
        self.int_bits = int(match.group(1))
        self.frac_bits = int(match.group(2))
        if self.int_bits < 1:
            raise ValueError("Integer bits must be at least 1 for signed fixed-point numbers.")
        self.format = f"Q{self.int_bits}.{self.frac_bits}"
        self.total_bits = self.int_bits + self.frac_bits
        self.scale = 2 ** self.frac_bits
        self.value = int(round(value * self.scale))
        self.max_val = 2 ** (self.total_bits - 1) - 1
        self.min_val = - (2 ** (self.total_bits - 1))
        if self.value > self.max_val:
            raise OverflowError(f"Value {value} exceeds maximum representable value {self.max_val / self.scale} for {self.format}.")
        if self.value < self.min_val:
            raise OverflowError(f"Value {value} is less than minimum representable value {self.min_val / self.scale} for {self.format}.")

    def __str__(self):
        return f"{self.value / self.scale} // 0x{convert_to_bits(self.value, self.total_bits)} ({self.format})"
    
    def __format__(self, format_spec):
        return f"{self.value / self.scale:{format_spec}}"
    
    def __hash__(self):
        return hash(self.value / self.scale)

    def __eq__(self, other):
        if isinstance(other, fixed):
            return self.value / self.scale == other.value / other.scale
        elif isinstance(other, Real):
            other_value = other * self.scale
            return self.value == other_value
        elif isinstance(other, np.ndarray):
            result = np.zeros(other.shape, dtype=bool)
            for index in np.ndindex(other.shape):
                result[index] = self.__eq__(other[index])
            return result
        else:
            return False
        
    def __ne__(self, value):
        return not self.__eq__(value)
    
    def __lt__(self, other):
        if isinstance(other, fixed):
            if self.format != other.format:
                raise ValueError(f"Cannot compare fixed-point numbers with different formats ({self.format} and {other.format}).")
            return self.value < other.value
        elif isinstance(other, Real):
            other_value = other * self.scale
            return self.value < other_value
        elif isinstance(other, np.ndarray):
            result = np.zeros(other.shape, dtype=bool)
            for index in np.ndindex(other.shape):
                result[index] = self.__lt__(other[index])
            return result
        else:
            raise TypeError(f"Unsupported operand type for <: {type(other)}")
        
    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)
    
    def __gt__(self, other):
        return not self.__le__(other)
    
    def __ge__(self, other):
        return not self.__lt__(other)
    
    def __float__(self):
        return self.value / self.scale
    
    def __int__(self):
        return self.value // self.scale
    
    def __index__(self):
        return self.__int__()
    
    def __abs__(self):
        result = fixed(self.format, 0)
        result.value = abs(self.value)
        if result.value >= 2 ** (self.total_bits - 1):
            result.value -= 2 ** self.total_bits
        return result
    
    def __ceil__(self):
        result = fixed(self.format, 0)
        result.value = np.ceil(self.value / self.scale) * self.scale
        if result.value >= 2 ** (self.total_bits - 1):
            result.value -= 2 ** self.total_bits
        return result
    
    def __floor__(self):
        result = fixed(self.format, 0)
        result.value = np.floor(self.value / self.scale) * self.scale
        if result.value >= 2 ** (self.total_bits - 1):
            result.value -= 2 ** self.total_bits
        return result
    
    def __round__(self):
        result = fixed(self.format, 0)
        result.value = int(round(self.value / self.scale)) * self.scale
        if result.value >= 2 ** (self.total_bits - 1):
            result.value -= 2 ** self.total_bits
        return result
    
    def __trunc__(self):
        result = fixed(self.format, 0)
        result.value = int(self.value / self.scale) * self.scale
        if result.value >= 2 ** (self.total_bits - 1):
            result.value -= 2 ** self.total_bits
        return result
    
    def __add__(self, other):
        if isinstance(other, fixed):
            if self.format != other.format:
                raise ValueError(f"Cannot add fixed-point numbers with different formats ({self.format} and {other.format}).")
            result_value = self.value + other.value
        elif isinstance(other, Real):
            other_value = int(round(other * self.scale))
            result_value = self.value + other_value
        elif isinstance(other, np.ndarray):
            result = np.zeros(other.shape, dtype=object)
            for index in np.ndindex(other.shape):
                result[index] = self.__add__(other[index])
            return result
        else:
            raise TypeError(f"Unsupported operand type for +: {type(other)}")
        if not self.allow_overflow:
            if result_value > self.max_val or result_value < self.min_val:
                raise OverflowError(f"Addition result {result_value / self.scale} is less than minimum representable value {self.min_val / self.scale} or greater than maximum representable value {self.max_val / self.scale} for {self.format}.")
        result_value = result_value % (2 ** self.total_bits)
        if result_value >= 2 ** (self.total_bits - 1):
            result_value -= 2 ** self.total_bits
        result = fixed(self.format, 0)
        result.value = result_value
        return result
    
    def __mul__(self, other):
        if isinstance(other, fixed):
            result_value = self.value * other.value
            result = fixed(f"Q{self.int_bits + other.int_bits}.{self.frac_bits + other.frac_bits}", 0)
        elif isinstance(other, Real):
            result_value = int(round(self.value * other))
            result_value = result_value % (2 ** self.total_bits)
            if result_value >= 2 ** (self.total_bits - 1):
                result_value -= 2 ** self.total_bits
            result = fixed(self.format, 0)
        elif isinstance(other, np.ndarray):
            result = np.zeros(other.shape, dtype=object)
            for index in np.ndindex(other.shape):
                result[index] = self.__mul__(other[index])
            return result
        else:
            raise TypeError(f"Unsupported operand type for *: {type(other)}")
        result.value = result_value
        return result
    
    def __neg__(self):
        result = fixed(self.format, 0)
        if result.value != - 2 ** (self.total_bits - 1):
            result.value = -self.value
        return result
    
    def __sub__(self, other):
        return self.__add__(-other)
    
    def __pos__(self):
        return self
    
    def __truediv__(self, other):
        if isinstance(other, Real):
            result = fixed(self.format, 0)
            result.value = int(round(self.value / other))
            if result.value >= 2 ** (self.total_bits - 1):
                result.value -= 2 ** self.total_bits
            return result
        else:
            return NotImplemented
    
    def __floordiv__(self, other):
        return NotImplemented
    
    def __mod__(self, other):
        return NotImplemented
    
    def __pow__(self, other):
        return NotImplemented
    
    def __divmod__(self, other):
        return NotImplemented
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __rsub__(self, other):
        return (-self).__add__(other)
    
    def __rtruediv__(self, other):
        return NotImplemented
    
    def __rpow__(self, other):
        return NotImplemented
    
    def __rfloordiv__(self, other):
        return NotImplemented
    
    def __rmod__(self, other):
        return NotImplemented
    
    def __rdivmod__(self, other):
        return NotImplemented
    
    def __iadd__(self, other):
        self.value = self.__add__(other).value
        return self
    
    def __imul__(self, other):
        result = self.__mul__(other)
        self.int_bits = result.int_bits
        self.frac_bits = result.frac_bits
        self.format = result.format
        self.total_bits = result.total_bits
        self.scale = result.scale
        self.value = result.value
        self.max_val = result.max_val
        self.min_val = result.min_val
        return self
    
    def __isub__(self, other):
        self.value = self.__sub__(other).value
        return self
    
    def __array__(self, dtype=None):
        return np.array(float(self), dtype=dtype)
    
    def resize(self, format):
        pattern = r"^Q([0-9]+)\.([0-9]+)$"
        match = re.match(pattern, format)
        if not match:
            raise ValueError("Invalid format. Use Qm.n format.")
        new_int_bits = int(match.group(1))
        new_frac_bits = int(match.group(2))
        if new_int_bits < 1:
            raise ValueError("Integer bits must be at least 1 for signed fixed-point numbers.")
        new_total_bits = new_int_bits + new_frac_bits
        new_scale = 2 ** new_frac_bits
        new_value = int(round((self.value / self.scale) * new_scale)) % (2 ** new_total_bits)
        if new_value >= 2 ** (new_total_bits - 1):
            new_value -= 2 ** new_total_bits
        self.int_bits = new_int_bits
        self.frac_bits = new_frac_bits
        self.format = format
        self.total_bits = new_total_bits
        self.scale = new_scale
        self.value = new_value
        self.max_val = 2 ** (self.total_bits - 1) - 1
        self.min_val = - (2 ** (self.total_bits - 1))
        return self
    
    def copy(self):
        return fixed(self.format, self.value / self.scale)

    def resized(self, format):
        return self.copy().resize(format)
    
if __name__ == "__main__":
    # Example usage
    print("Example usage of fixed-point class:")
    a = fixed("Q4.0", 1)
    b = fixed("Q4.0", 2)
    print(a + b)
    print(a + b == 3)
    print("/////////////////")
    a = fixed("Q1.4", 0.125)
    b = fixed("Q1.6", -0.1875)
    print(a * b)
    print(a * b == -0.0234375)
    print(a * b >= -0.03)
    print(a * b > -0.02)
    a *= b
    print(a) # Format is modified after multiplication, Q1.4 -> Q2.10
    print(a == -0.0234375)
    print("/////////////////")
    a = fixed("Q7.1", 1.5)
    print(str(a))
    print(a + 1)
    print(a * (-2))
    print(a * 10.33) # Lost precision
    print("/////////////////")
    a = fixed("Q4.0", 7)
    print(a)
    print(a + 1) # Overflow
    print(a + 15) # 15 = 2^4 -1
    print(a + 16) # 16 = 2^4
    print("/////////////////")
    a = np.array([fixed("Q3.4", 1.5), fixed("Q3.4", -2.0)], dtype=object)
    print(str(np.sum(a)))
    print([str(x) for x in np.abs(a)]) # Supports simple operations
    print([str(fixed("Q8.8", np.sin(float(x)))) for x in a]) # Must convert to float then back to fixed with proper format
    print("/////////////////")
    a = fixed("Q4.0", 7)
    a.resize("Q5.1") # Extended range
    print(a) # 7.0 // 0x001110 (Q5.1)
    b = fixed("Q4.8", 7.15625)
    print(b) # 7.15625 // 0x011100101000 (Q4.8)
    b.resize("Q4.2") # Precision loss
    print(b) # 7.25 // 0x011101 (Q4.2)
    b.resize("Q2.2") # Range loss
    print(b) # -0.75 // 0x1101 (Q2.2)
    print("/////////////////")
    a = fixed("Q4.0", 7)
    b = a.copy()
    b.resize("Q2.0")
    print(b) # -1.0 // 0x11 (Q2.0)
    print(a.resized("Q2.0")) # -1.0 // 0x11 (Q2.0)
    print(a) # 7.0 // 0x0111 (Q4.0)
    print("/////////////////")
    try:
        c = fixed("Q8.0", 12345) # Out of range
    except Exception as error:
        print(error)
    c = fixed("Q8.0", 0)
    c += 12345 # Wraps around
    print(c)
    print("/////////////////")
    try:
        d = fixed("Q4.0", 1)
        e = fixed("Q5.0", 1)
        print(d + e) # Different format
    except Exception as error:
        print(error)
    f = fixed(d.format, float(e))
    print(d + f) # Now works after converting to same format
    print("/////////////////")
    code.interact(local=locals())