import module
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from port_numbers import *
import time

class ModuleSignalRouter(module.ModuleBase):
    # Only full connection mode is supported.
    port_count = 64

    def __init__(self, bus, full_connection = True):
        super().__init__(bus, "ROUT")
        self.full_connection = True
        self.synced_during_init = False
        self.unsynced_warned = False
        try:
            self.sync()
            self.synced_during_init = True
        except Exception as e:
            print("Failed to sync routing configuration from device, initializing with default settings.")
            self.port_config = [0] * (64 + 64)
            self.port_enable = [1] * (64 + 64)
            self.encode()
            self.last_bits = self.bits

    def reset(self):
        super().reset()
        self.port_config = [0] * (64 + 64)
        self.port_enable = [1] * (64 + 64)
        self.encode()
        self.last_bits = self.bits

    def set_routing(self, port, source):
        if port // 64 != source // 64:
            raise ValueError("Port and source must either be both signals or control signals.")
        self.port_config[port] = source % 64

    def enable(self, port):
        self.port_enable[port] = 1

    def disable(self, port):
        self.port_enable[port] = 0

    def encode(self, hold_output = False):
        """
        将路由配置编码为位序列
        
        只支持全连接模式：
        - 每个端口使用8位：1位保留位(0) + 1位使能位 + 6位端口配置
        - 总长度补齐至1024位
        """
        bits = ""
        for i in range(64 + 64):
            bits = bin(self.port_config[i])[2:].zfill(6) + bits
            bits = str(self.port_enable[i]) + bits
            if hold_output and 56 <= i < 64: # Hardware output ports
                bits = "1" + bits
            else:
                bits = "0" + bits
        bits = bits.zfill(1024)
        self.bits = bits
        return
    

    def get_bytes(self):
        self.encode()
        return "".join([hex(int(self.bits[i * 8: (i + 1) * 8], 2))[2:] for i in range(64)])
    

    def _upload(self):
        for i in range(31, 0, -1):
            # if True:
            if self.bits[i * 32: (i + 1) * 32] != self.last_bits[i * 32: (i + 1) * 32]:
                print(f"diff {i}, old: {self.last_bits[i * 32: (i + 1) * 32]}, new: {self.bits[i * 32: (i + 1) * 32]}")
                self.write((31 - i), int(self.bits[i * 32: (i + 1) * 32], 2), hold = True)
        self.write(31, int(self.bits[0:32], 2), hold = False) # Flush at the end
        self.last_bits = self.bits

    def upload(self):
        if not self.synced_during_init and not self.unsynced_warned:
            print("Warning: Routing configuration was not synced during initialization. Uploading may overwrite existing configuration on the device.")
            self.unsynced_warned = True
        # Safe upload, hold output during reconfiguration
        self.encode(hold_output = True)
        self._upload()
        time.sleep(0.05) # Avoid unstable circuit responses
        self.encode(hold_output = False)
        self._upload()

    def sync(self):
        # Sync routing from the device
        bits = ""
        for i in range(32):
            data = self.read(i)
            bits = bin(int.from_bytes(data, "big", signed = False))[2:].zfill(32) + bits
        self.bits = bits
        self.last_bits = bits
        self.port_config = [0] * (64 + 64)
        self.port_enable = [1] * (64 + 64)
        for i in range(64 + 64):
            self.port_config[i] = int(bits[(64 + 64 - 1 - i) * 8 + 2: (64 + 64 - 1 - i) * 8 + 8], 2)
            self.port_enable[i] = int(bits[(64 + 64 - 1 - i) * 8 + 1], 2)

    def plot(self):
        raise NotImplementedError("Full connection mode does not require routing visualization.")

if __name__ == "__main__":
    r = ModuleSignalRouter(None)
    r.set_routing(2, 10)
    r.set_routing(1, 48)
    r.set_routing(19, 11)
    r.set_routing(36, 13)