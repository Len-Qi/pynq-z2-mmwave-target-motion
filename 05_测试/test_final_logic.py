import math
from pathlib import Path
import struct
import sys

RUNTIME = Path(__file__).resolve().parents[1] / '01_PYNQ运行程序'
sys.path.insert(0, str(RUNTIME))

from fpga_radar_core import parse_targets
from led_status import LedStatus, compose_status_word
from motion_core import MotionConfig, MotionTracker


class FakeMMIO:
    def __init__(self):
        self.values = {}

    def write(self, address, value):
        self.values[address] = value


def check_led_logic():
    assert compose_status_word(False, False) == 0x0
    assert compose_status_word(True, False) == 0x8
    assert compose_status_word(True, True) == 0xC
    assert compose_status_word(False, True) == 0x4
    for present in (False, True):
        for moving in (False, True):
            assert compose_status_word(present, moving) & 0x3 == 0
    fake = FakeMMIO()
    leds = LedStatus(fake)
    assert leds.update(True, False) == 0x8
    assert leds.update(True, True) == 0xC
    leds.clear()
    assert fake.values[0] == 0


def check_target_parser():
    payload = struct.pack('<i', 2)
    payload += struct.pack('<fffii', 1.0, 2.0, 0.5, 7, 11)
    payload += struct.pack('<fffii', -1.0, 0.0, 0.0, -2, 12)
    targets = parse_targets(payload)
    assert [row['cluster_id'] for row in targets] == [11, 12]
    assert math.isclose(targets[0]['distance_m'], math.sqrt(5.25), rel_tol=1e-6)


def final_state(points):
    tracker = MotionTracker(MotionConfig())
    result = None
    for index, xyz in enumerate(points):
        result = tracker.update(1, index * 0.1, xyz, True)
    return result


def check_motion_logic():
    stable = [(1000 + (i % 3) * 2, 500, 100) for i in range(50)]
    moving = [(1000 + i * 50, 500 + i * 10, 100) for i in range(50)]
    assert final_state(stable)['state'] == 'stable'
    assert final_state(moving)['state'] == 'moving'


if __name__ == '__main__':
    check_led_logic()
    check_target_parser()
    check_motion_logic()
    print('PASS: parser, motion classification and LED mapping are correct.')
