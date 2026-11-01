from collections import Counter, deque
import math

WINDOW = 14

class TargetWindows:
    def __init__(self, gap_s=1.5, jump_floor_mm=600.0, maximum_speed_mm_s=2000.0):
        self.gap_s = gap_s
        self.jump_floor_mm = jump_floor_mm
        self.maximum_speed_mm_s = maximum_speed_mm_s
        self.windows = {}
        self.times = {}
        self.last_points = {}

    def update(self, frame_type, targets, now):
        counts = Counter(target['cluster_id'] for target in targets)
        ready = []
        rejected = []
        for target in targets:
            key = (frame_type, target['cluster_id'])
            if counts[target['cluster_id']] != 1:
                rejected.append((target['cluster_id'], 'duplicate_cluster'))
                continue
            if not all(math.isfinite(target[name]) and abs(target[name]) <= 1000
                       for name in ('x', 'y', 'z', 'distance_m')):
                rejected.append((target['cluster_id'], 'invalid_coordinates'))
                continue
            previous = self.times.get(key)
            if previous is None or now - previous > self.gap_s:
                self.windows[key] = deque(maxlen=WINDOW)
                previous = None
            point = tuple(round(target[name] * 1000)
                          for name in ('x', 'y', 'z', 'distance_m'))
            last = self.last_points.get(key)
            if previous is not None and last is not None:
                elapsed = now - previous
                if math.dist(point[:3], last[:3]) > max(self.jump_floor_mm,
                                                            self.maximum_speed_mm_s * elapsed):
                    self.windows[key] = deque(maxlen=WINDOW)
                    previous = None
            dt = 100 if previous is None else max(1, min(1000, round((now - previous) * 1000)))
            self.windows[key].append(point + (dt,))
            self.times[key] = now
            self.last_points[key] = point
            ready.append((target, list(self.windows[key])))
        for key in list(self.windows):
            if now - self.times[key] > self.gap_s:
                self.windows.pop(key, None)
                self.times.pop(key, None)
                self.last_points.pop(key, None)
        return ready, rejected
