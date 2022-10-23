from openrgb import orgb

from plaid.utils import ColorWheel


class Segment(object):
    title: str
    device: orgb.Device
    start: int = 0
    end: int = 0
    region_index: int = 0

    odd: bool = False
    position_offset: float = 0
    reverse_direction: bool = False
    reverse_wheel: bool = False
    fast_update: bool = True

    def __init__(self, title, device: orgb.Device, start: int = 0, end: int = -1):
        self.title = title
        self.device = device
        self.start = start
        self.end = end
        if end < 0:
            self.end = len(device.leds) + end + 1

    def __len__(self):
        return self.end - self.start

    def set_colors(self, colors):
        self.device.colors[self.start:self.end] = colors

    def apply_wheel(
        self, wheel: ColorWheel, render_position: float, position_is_percent=False
    ):
        if self.reverse_wheel:
            wheel = ColorWheel(list(reversed(wheel.array)))
        shifted = position_is_percent and wheel.shifted_pct or wheel.shifted_amount
        colors = shifted(render_position + self.position_offset).get_array(len(self))
        if self.reverse_direction:
            colors = list(reversed(colors))
        return self.set_colors(colors)

    def dump(self):
        summary = self.device.name
        if self.start != 0 or self.end != -1:
            summary += "[%s:%s]" % (self.start or "", self.end != -1 and self.end or "")
        return "Segment[%s]: %s" % (self.title, summary)


class Region(object):
    def __init__(self, title, segments=None):
        self.title = title
        self.segments = segments or []

    def add_segment(self, seg):
        seg.region_index = len(self.segments)
        seg.odd = seg.region_index % 2 == 1
        self.segments.append(seg)
        return seg

    def apply_wheel(
        self, wheel: ColorWheel, render_position: float, position_is_percent=False
    ):
        for seg in self.segments:
            seg.apply_wheel(wheel, render_position, position_is_percent)

    def dump(self):
        return "Region[%s]:\n%s" % (
            self.title,
            "\n".join("  " + seg.dump() for seg in self.segments),
        )
