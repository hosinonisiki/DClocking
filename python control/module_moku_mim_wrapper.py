import module

class ModuleMokuMIMWrapper(module.ModuleBase):
    def __init__ (self, bus, config_id):
        super().__init__(bus, "MMWR")
        self.data = b"\x00\x00\x00\x00"
        self.set_config(config_id)

    def reset(self):
        super().reset()
        self.disable()
        self.upload()

    def enable(self):
        self.data = b"\x10\x00\x00" + self.config_id.to_bytes(1, "big")

    def disable(self):
        self.data = b"\x00\x00\x00" + self.config_id.to_bytes(1, "big")

    def set_config(self, config_id):
        self.config_id = int(config_id)
        if self.config_id != -1:
            self.data = self.data[:3] + self.config_id.to_bytes(1, "big")

    def upload(self):
        self.bus.post_bytes(b":BUS_.MMWR.MISC.DATA." + self.data + b"!")