from collections import deque
from dataclasses import asdict, dataclass
import math
from statistics import median

@dataclass(frozen=True)
class MotionConfig:
    window_s: float = 3.0
    minimum_span_s: float = 2.5
    minimum_samples: int = 12
    gap_s: float = 1.5
    stable_displacement_mm: float = 100.0
    stable_span_mm: float = 200.0
    moving_displacement_mm: float = 250.0
    moving_span_mm: float = 300.0
    moving_coherence: float = 0.35
    confirmation_s: float = 1.0
    jump_floor_mm: float = 250.0
    maximum_speed_mm_s: float = 4000.0

    def to_dict(self):
        return asdict(self)

def quantile(values, q):
    values = sorted(values)
    index = (len(values) - 1) * q
    low = int(index)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (index - low)

def center(points):
    return tuple(median([point[index] for point in points]) for index in range(3))

class MotionTracker:
    def __init__(self, config=None):
        self.config = config or MotionConfig()
        self.tracks = {}

    def retain(self, keys, now):
        keys = set(keys)
        for key, track in list(self.tracks.items()):
            if key not in keys or now - track['time'] > self.config.gap_s:
                del self.tracks[key]

    def update(self, key, now, xyz, valid=True):
        cfg = self.config
        if not math.isfinite(now) or not all(math.isfinite(value) for value in xyz):
            self.tracks.pop(key, None)
            return {'state': 'uncertain', 'reason': 'invalid_coordinates'}
        track = self.tracks.get(key)
        reason = 'collecting_window'
        if track:
            dt = now - track['time']
            if dt <= 0:
                self.tracks.pop(key, None)
                return {'state': 'uncertain', 'reason': 'non_monotonic_time'}
            if dt > cfg.gap_s:
                track = None
            elif math.dist(xyz, track['xyz']) > max(cfg.jump_floor_mm, cfg.maximum_speed_mm_s * dt):
                track = None
                reason = 'position_jump'
        if track is None:
            track = {'points': deque(maxlen=512), 'candidate': None, 'since': now}
            self.tracks[key] = track
        track.update(time=now, xyz=tuple(xyz))
        track['points'].append((now, tuple(xyz)))
        while track['points'] and now - track['points'][0][0] > cfg.window_s:
            track['points'].popleft()
        points = list(track['points'])
        elapsed = now - points[0][0]
        result = {'state': 'warmup', 'reason': reason, 'samples': len(points),
                  'window_s': round(elapsed, 3)}
        if not valid or len(points) < cfg.minimum_samples or elapsed < cfg.minimum_span_s:
            track['candidate'] = None
            if reason == 'position_jump':
                result['state'] = 'uncertain'
            return result
        xyzs = [point for _, point in points]
        first = [point for timestamp, point in points
                 if timestamp <= points[0][0] + elapsed / 3]
        last = [point for timestamp, point in points if timestamp >= now - elapsed / 3]
        displacement = math.dist(center(first), center(last))
        span = math.sqrt(sum((quantile([point[i] for point in xyzs], .9) -
                              quantile([point[i] for point in xyzs], .1)) ** 2
                             for i in range(3)))
        bins = []
        for index in range(6):
            group = [point for timestamp, point in points
                     if min(5, int((timestamp - points[0][0]) / elapsed * 6)) == index]
            if group:
                bins.append(center(group))
        path = sum(math.dist(a, b) for a, b in zip(bins, bins[1:]))
        coherence = min(1.0, math.dist(bins[0], bins[-1]) / path) if path else 0.0
        result.update(displacement_mm=round(displacement, 1),
                      span_mm=round(span, 1), coherence=round(coherence, 3))
        if displacement <= cfg.stable_displacement_mm and span <= cfg.stable_span_mm:
            candidate = 'stable'
        elif (displacement >= cfg.moving_displacement_mm and
              span >= cfg.moving_span_mm and coherence >= cfg.moving_coherence):
            candidate = 'moving'
        else:
            candidate = 'uncertain'
        if candidate != track['candidate']:
            track.update(candidate=candidate, since=now)
        confirmed = now - track['since'] >= cfg.confirmation_s
        result.update(state=candidate if confirmed or candidate == 'uncertain' else 'uncertain',
                      reason='window_evidence' if confirmed else 'awaiting_confirmation')
        return result
