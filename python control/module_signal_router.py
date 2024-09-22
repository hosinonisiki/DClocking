import module

class ModuleSignalRouter(module.ModuleBase):
    channel_count = 96

    def __init__(self, bus):
        super().__init__(bus, "ROUT")
        self.routing_config = list(range(10)) * 8 + list(range(16))
        self.routing_enable = [1] * self.channel_count
        self.bits = self.encode()
        self.last_bits = self.bits

    def reset(self):
        super().reset()
        self.routing_config = list(range(10)) * 8 + list(range(16))
        self.routing_enable = [1] * self.channel_count
        self.bits = self.encode()

    def set_routing(self, channel, source):
        self.routing_config[channel] = source
        self.bits = self.encode()
        self.upload()

    def enable(self, channel):
        self.routing_enable[channel] = 1
        self.bits = self.encode()
        self.upload()

    def disable(self, channel):
        self.routing_enable[channel] = 0
        self.bits = self.encode()
        self.upload()

    def encode(self):
        bits = ""
        for i in range(self.channel_count):
            bits = bin(self.routing_config[i])[2:].zfill(4) + bits
            bits = str(self.routing_enable[i]) + bits
        bits = bits.zfill(512)
        return bits
    
    def upload(self):
        for i in range(15, -1, -1):
            if self.bits[i * 32: (i + 1) * 32] != self.last_bits[i * 32: (i + 1) * 32]:
                self.write((15 - i), int(self.bits[i * 32: (i + 1) * 32], 2))
        self.last_bits = self.bits