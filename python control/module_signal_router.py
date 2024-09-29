import module
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

class ModuleSignalRouter(module.ModuleBase):
    # The router consists of 8 banks of 10x10 switches,
    # 8 of which connects to the interface while the other
    # 2 connects to a 16x16 switch. The router has a total
    # of 96 channels including the internal channels, but
    # only 64 channels are exposed to the interface.
    # routing_config stores the routing configuration of
    # each channel, while routing_enable stores the enable
    # status of each channel. port_config stores the routing
    # configuration of each external port, while port_enable
    # stores the enable status of each external port.
    # Internal routing must be inferred from the routing
    # configuration of the external ports.

    channel_count = 96
    port_count = 64

    def __init__(self, bus, full_connection = True):
        super().__init__(bus, "ROUT")
        self.full_connection = full_connection
        if full_connection:
            self.port_config = list(range(64))
            self.port_enable = [1] * 64
            self.encode()
            self.last_bits = self.bits
        else:
            self.routing_config = list(range(10)) * 8 + list(range(16))
            self.routing_enable = [1] * self.channel_count
            self.port_config = list(range(64))
            self.port_enable = [1] * 64
            self.encode()
            self.last_bits = self.bits

    def reset(self):
        super().reset()
        if self.full_connection:
            self.port_config = list(range(64))
            self.port_enable = [1] * 64
            self.encode()
            self.last_bits = self.bits
        else:
            self.routing_config = list(range(10)) * 8 + list(range(16))
            self.routing_enable = [1] * self.channel_count
            self.port_config = list(range(64))
            self.port_enable = [1] * 64
            self.encode()
            self.last_bits = self.bits

    # Do not expose internal routing methods
    def _set_routing(self, channel, source):
        assert not self.full_connection
        self.routing_config[channel] = source

    def _enable(self, channel):
        assert not self.full_connection
        self.routing_enable[channel] = 1

    def _disable(self, channel):
        assert not self.full_connection
        self.routing_enable[channel] = 0

    def implement_routing(self):
        assert not self.full_connection, "Full connection mode does not require routing implementation."
        # Check if the routing configuration can be realized
        need_forward = [0] * 8
        receive_forward = [0] * 8
        for i in range(8):
            for j in range(8):
                if self.port_config[i * 8 + j] < i * 8 or self.port_config[i * 8 + j] >= (i + 1) * 8:
                    need_forward[i] += 1
                    receive_forward[self.port_config[i * 8 + j] // 8] += 1
        for i in range(8):
            if need_forward[i] >= 3:
                raise ValueError(f"The {i}th bank requires {need_forward[i]} forward switches.")
            if receive_forward[i] >= 3:
                raise ValueError(f"The {i}th bank receives {receive_forward[i]} forward switches.")
        forward_destination = [None] * 16
        for i in range(8):
            nth_forward = 0
            for j in range(8):
                if self.port_config[i * 8 + j] < i * 8 or self.port_config[i * 8 + j] >= (i + 1) * 8:
                    if nth_forward == 0:
                        self._set_routing(i * 10 + j, 8)
                        forward_destination[i * 2] = self.port_config[i * 8 + j]
                        nth_forward += 1
                    else:
                        self._set_routing(i * 10 + j, 9)
                        forward_destination[i * 2 + 1] = self.port_config[i * 8 + j]
                else:
                    self._set_routing(i * 10 + j, self.port_config[i * 8 + j] % 8)
        nth_receive = [0] * 8
        for i in range(15):
            if forward_destination[i] is not None:
                target_bank = forward_destination[i] // 8
                self._set_routing(80 + i, target_bank * 2 + nth_receive[target_bank])
                self._set_routing(target_bank * 10 + 8 + nth_receive[target_bank], forward_destination[i] % 8)
                nth_receive[target_bank] += 1
        for i in range(8):
            for j in range(8):
                if self.port_enable[i * 8 + j]:
                    self._enable(i * 10 + j)
                else:
                    self._disable(i * 10 + j)

    def set_routing(self, port, source):
        self.port_config[port] = source

    def enable(self, port):
        self.port_enable[port] = 1

    def disable(self, port):
        self.port_enable[port] = 0

    def encode(self):
        if self.full_connection:
            bits = ""
            for i in range(self.port_count):
                bits = bin(self.port_config[i])[2:].zfill(6) + bits
                bits = str(self.port_enable[i]) + bits
                bits = "0" + bits
            bits = bits.zfill(512)
        else:
            bits = ""
            for i in range(self.channel_count):
                bits = bin(self.routing_config[i])[2:].zfill(4) + bits
                bits = str(self.routing_enable[i]) + bits
            bits = bits.zfill(512)
        self.bits = bits
        return
    
    def get_bytes(self):
        self.encode()
        return "".join([hex(int(self.bits[i * 8: (i + 1) * 8], 2))[2:] for i in range(64)])
    
    def upload(self):
        self.encode()
        for i in range(15, -1, -1):
            if self.bits[i * 32: (i + 1) * 32] != self.last_bits[i * 32: (i + 1) * 32]:
                self.write((15 - i), int(self.bits[i * 32: (i + 1) * 32], 2))
        self.last_bits = self.bits

    def plot(self):
        assert not self.full_connection, "Full connection mode does not require routing visualization."
        # Draw a schematic to show the connectivity
        fig, ax = plt.subplots(1, 1, figsize=(15, 7))

        # Define 16 colors for forward pins
        forawrd_pin_colors = ['red', 'green', 'blue', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta', 'yellow', 'lime', 'teal', 'indigo', 'maroon', 'navy']

        # Plot 8 banks of 10x10 switches
        for i in range(8):
            ax.add_patch(Rectangle((i % 4 * 27 + 7, i // 4 * 23 + 18), 23, 10, fill=False, linewidth = 0.8))
            for j in range(10):
                # Draw small segments to represent pins
                color = 'black' if j < 8 else forawrd_pin_colors[i * 2]
                ax.plot([i % 4 * 27 + 9.5 + j * 2, i % 4 * 27 + 9.5 + j * 2], [i // 4 * 23 + 17.5, i // 4 * 23 + 18.5], color=color, linewidth=1)
                color = 'black' if j < 8 else forawrd_pin_colors[i * 2 + 1]
                ax.plot([i % 4 * 27 + 9.5 + j * 2, i % 4 * 27 + 9.5 + j * 2], [i // 4 * 23 + 27.5, i // 4 * 23 + 28.5], color=color, linewidth=1)
                if self.routing_enable[i * 10 + j]:
                    ax.plot([i % 4 * 27 + 9.5 + j * 2, i % 4 * 27 + 9.5 + self.routing_config[i * 10 + j] * 2], [i // 4 * 23 + 28, i // 4 * 23 + 18], color='black', linewidth=0.2)
            #ax.text(i % 4 + 10, i // 4 + 21, f"Bank {i}", ha='center', va='center')
        
        # Plot 16x16 switch
        ax.add_patch(Rectangle((120, 27), 32, 15, fill=False, linewidth = 0.8))
        for i in range(16):
            # Draw small segments to represent pins
            color = forawrd_pin_colors[i // 2 * 2 + 1]
            ax.plot([121 + i * 2, 121 + i * 2], [26.5, 27.5], color=color, linewidth=1)
            color = forawrd_pin_colors[i // 2 * 2]
            ax.plot([121 + i * 2, 121 + i * 2], [41.5, 42.5], color=color, linewidth=1)
            if self.routing_enable[80 + i]:
                ax.plot([121 + i * 2, 121 + self.routing_config[80 + i] * 2], [42, 27], color='black', linewidth=0.2)



        ax.set_xlim(0, 160)
        ax.set_ylim(0, 70)
        ax.set_aspect('equal', adjustable='box')
        plt.show()
        
if __name__ == "__main__":
    r = ModuleSignalRouter(None)
    r.set_routing(2, 10)
    r.set_routing(1, 48)
    r.set_routing(19, 11)
    r.set_routing(36, 13)
    #r.implement_routing()
    #r.plot()