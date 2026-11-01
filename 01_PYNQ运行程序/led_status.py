GPIO_BASE = 0x41200000
GPIO_RANGE = 0x1000
GPIO_DATA = 0x00
GPIO_TRI = 0x04

def compose_status_word(present, moving):
    return ((int(bool(present)) << 3) | (int(bool(moving)) << 2)) & 0xC

class LedStatus:
    def __init__(self, mmio=None):
        if mmio is None:
            from pynq import MMIO
            mmio = MMIO(GPIO_BASE, GPIO_RANGE)
        self.mmio = mmio
        self.mmio.write(GPIO_TRI, 0)
        self.clear()

    def update(self, present, moving):
        value = compose_status_word(present, moving)
        self.mmio.write(GPIO_DATA, value)
        return value

    def clear(self):
        self.mmio.write(GPIO_DATA, 0)
