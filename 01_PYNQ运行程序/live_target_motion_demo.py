#!/usr/bin/env python3
import argparse
import fcntl
import signal
import time

import serial
from fpga_radar_core import TinyFrameParser, open_filter_overlay, parse_targets, replay_window
from led_status import LedStatus
from motion_core import MotionConfig, MotionTracker
from target_windows import TargetWindows

LABELS = {'warmup': 'WARMUP', 'stable': 'STABLE',
          'moving': 'MOVING', 'uncertain': 'UNCERTAIN'}

def main():
    signal.signal(signal.SIGINT, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt()))
    signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt()))
    parser = argparse.ArgumentParser(description='LD6004 + PYNQ target and motion demo')
    parser.add_argument('--device', default='/dev/ttyUSB0')
    parser.add_argument('--baud', type=int, default=115200)
    parser.add_argument('--duration', type=float, default=0)
    args = parser.parse_args()
    if args.duration < 0:
        parser.error('duration must be >= 0')

    lock = open('/tmp/pynq_target_motion_demo.lock', 'a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Another demo process is already running. Stop it with Ctrl+C.')

    windows = TargetWindows()
    tracker = MotionTracker(MotionConfig())
    parser_state = TinyFrameParser()
    started = time.monotonic()
    last_target_frame = started
    next_display = started
    current = {}
    leds = None

    print('Loading FPGA overlay and opening radar serial port...', flush=True)
    try:
        with serial.Serial(args.device, args.baud, timeout=0.1, exclusive=True) as port:
            ip_name, mmio = open_filter_overlay()
            leds = LedStatus()
            port.reset_input_buffer()
            print('FPGA=%s | SERIAL=%s @ %d' % (ip_name, args.device, args.baud), flush=True)
            print('LED3=target present | LED2=at least one target moving | LED1/LED0=off', flush=True)
            print('Wait about 3 seconds for the motion window. Press Ctrl+C to stop.', flush=True)
            while not args.duration or time.monotonic() - started < args.duration:
                chunk = port.read(min(port.in_waiting or 1, 65536))
                for sequence, kind, payload in parser_state.feed(chunk):
                    if kind != 0x0A04:
                        continue
                    now = time.monotonic()
                    last_target_frame = now
                    try:
                        targets = parse_targets(payload)
                    except (ValueError, OverflowError):
                        continue
                    ready, rejected = windows.update(kind, targets, now)
                    active = [target['cluster_id'] for target, history in ready]
                    tracker.retain(active, now)
                    current = {}
                    for target, history in ready:
                        result = replay_window(mmio, history)
                        cluster = target['cluster_id']
                        motion = tracker.update(cluster, now,
                                                (result['fx'], result['fy'], result['fz']),
                                                bool(result['valid']))
                        current[cluster] = {'status': 'ok', 'motion': motion, 'fpga': result}
                    present = bool(current)
                    moving = any(row['motion']['state'] == 'moving' for row in current.values())
                    leds.update(present, moving)

                now = time.monotonic()
                if now - last_target_frame > 1.5:
                    current = {}
                    tracker.retain([], now)
                    if leds is not None:
                        leds.update(False, False)
                if now >= next_display:
                    next_display = now + 0.5
                    moving = any(row['motion']['state'] == 'moving' for row in current.values())
                    print('\rPRESENT=%-3s MOVING=%-3s TARGETS=%-2d ' %
                          ('YES' if current else 'NO', 'YES' if moving else 'NO', len(current)),
                          end='', flush=True)
                    for cluster, row in sorted(current.items()):
                        motion = row['motion']
                        print('| ID=%s %s d=%smm span=%smm ' %
                              (cluster, LABELS[motion['state']],
                               motion.get('displacement_mm', '--'),
                               motion.get('span_mm', '--')), end='', flush=True)
    except KeyboardInterrupt:
        print('\nStopped.', flush=True)
    finally:
        if leds is not None:
            leds.clear()

if __name__ == '__main__':
    try:
        main()
    except (serial.SerialException, OSError, TimeoutError) as exc:
        raise SystemExit('Run failed: %s' % exc)
