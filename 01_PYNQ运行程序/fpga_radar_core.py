import math
from pathlib import Path
import struct
import time

AP_CTRL = 0x000
X_MM, Y_MM, Z_MM, DISTANCE_MM = 0x010, 0x018, 0x020, 0x028
DT_MS, RESET_STATE = 0x030, 0x038
FILTERED_X_MM, FILTERED_Y_MM = 0x040, 0x050
FILTERED_Z_MM, FILTERED_DISTANCE_MM = 0x060, 0x070
VELOCITY_X_MM_S, VELOCITY_Y_MM_S = 0x080, 0x090
VELOCITY_Z_MM_S, VELOCITY_DISTANCE_MM_S = 0x0A0, 0x0B0
RANGE_X_MM, RANGE_Y_MM = 0x0C0, 0x0D0
RANGE_Z_MM, RANGE_DISTANCE_MM = 0x0E0, 0x0F0
MOTION_SCORE, VALID = 0x100, 0x110
MAX_DATA_LENGTH = 1024

def checksum(data):
    value = 0
    for byte in data:
        value ^= byte
    return (~value) & 0xFF

class TinyFrameParser:
    def __init__(self):
        self.buffer = bytearray()
        self.good_frames = self.bad_headers = self.bad_data = 0

    def feed(self, chunk):
        self.buffer.extend(chunk)
        frames = []
        while True:
            start = self.buffer.find(b'\x01')
            if start < 0:
                self.buffer.clear()
                break
            if start:
                del self.buffer[:start]
            if len(self.buffer) < 8:
                break
            length = int.from_bytes(self.buffer[3:5], 'big')
            if length > MAX_DATA_LENGTH:
                del self.buffer[0]
                self.bad_headers += 1
                continue
            total = 9 + length
            if len(self.buffer) < total:
                break
            frame = bytes(self.buffer[:total])
            if checksum(frame[:7]) != frame[7]:
                del self.buffer[0]
                self.bad_headers += 1
                continue
            if checksum(frame[8:-1]) != frame[-1]:
                del self.buffer[:total]
                self.bad_data += 1
                continue
            frames.append((int.from_bytes(frame[1:3], 'big'),
                           int.from_bytes(frame[5:7], 'big'), frame[8:-1]))
            del self.buffer[:total]
            self.good_frames += 1
        return frames

def parse_targets(data):
    if len(data) < 4:
        raise ValueError('target frame is too short')
    count = struct.unpack_from('<i', data, 0)[0]
    if count < 0 or count > 50 or len(data) < 4 + count * 20:
        raise ValueError('invalid target frame')
    targets = []
    offset = 4
    for _ in range(count):
        x, y, z, doppler, cluster = struct.unpack_from('<fffii', data, offset)
        offset += 20
        targets.append({'x': x, 'y': y, 'z': z, 'doppler_index': doppler,
                        'cluster_id': cluster,
                        'distance_m': math.sqrt(x*x + y*y + z*z)})
    return targets

def signed32(value):
    return value - (1 << 32) if value & 0x80000000 else value

def invoke(mmio, x_mm=0, y_mm=0, z_mm=0, distance_mm=0, dt_ms=50, reset_state=0):
    for address, value in ((X_MM, x_mm), (Y_MM, y_mm), (Z_MM, z_mm),
                           (DISTANCE_MM, distance_mm), (DT_MS, dt_ms),
                           (RESET_STATE, reset_state)):
        mmio.write(address, value & 0xFFFFFFFF)
    mmio.write(AP_CTRL, 1)
    deadline = time.monotonic() + 1.0
    while not mmio.read(AP_CTRL) & 2:
        if time.monotonic() >= deadline:
            raise TimeoutError('FPGA filter did not finish')
    return {'fx': signed32(mmio.read(FILTERED_X_MM)),
            'fy': signed32(mmio.read(FILTERED_Y_MM)),
            'fz': signed32(mmio.read(FILTERED_Z_MM)),
            'fd': signed32(mmio.read(FILTERED_DISTANCE_MM)),
            'vx': signed32(mmio.read(VELOCITY_X_MM_S)),
            'vy': signed32(mmio.read(VELOCITY_Y_MM_S)),
            'vz': signed32(mmio.read(VELOCITY_Z_MM_S)),
            'vd': signed32(mmio.read(VELOCITY_DISTANCE_MM_S)),
            'rx': mmio.read(RANGE_X_MM), 'ry': mmio.read(RANGE_Y_MM),
            'rz': mmio.read(RANGE_Z_MM), 'rd': mmio.read(RANGE_DISTANCE_MM),
            'score': mmio.read(MOTION_SCORE), 'valid': mmio.read(VALID)}

def open_filter_overlay():
    from pynq import MMIO, Overlay
    bitfile = Path(__file__).resolve().parent / 'radar_filter_v3.bit'
    overlay = Overlay(str(bitfile), download=True)
    candidates = [(name, info) for name, info in overlay.ip_dict.items()
                  if 'radar_filter' in name.lower()]
    if not candidates:
        raise RuntimeError('radar_filter IP was not found')
    name, info = candidates[0]
    to_int = lambda value: int(value, 0) if isinstance(value, str) else int(value)
    mmio = MMIO(to_int(info['phys_addr']), to_int(info['addr_range']))
    invoke(mmio, reset_state=1)
    return name, mmio

def replay_window(mmio, history):
    invoke(mmio, reset_state=1)
    result = None
    for x, y, z, distance, dt in history:
        result = invoke(mmio, x, y, z, distance, dt)
    return result
