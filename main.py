from typing import List, Dict
from openrgb import orgb, OpenRGBClient
from openrgb.utils import RGBColor
from datetime import datetime
from plaid.colors import scale_value, BLACK, WHITE
import time, random

RAM_NAMES = [
    "Corsair Vengeance Pro RGB",
]


def BlendedHueRange(start_hue: int, end_hue: int, length: int) -> List[int]:
    """
    :param start_hue: the starting hue value
    :param end_hue: the ending hue value
    :param length: the size of the output range
    :return: a list of hue values (length in size) scaling between start and end
    """
    return [
        int(scale_value(start_hue, end_hue, n / (length - 1))) % 360
        for n in range(length)
    ]


class ColorWheel(object):
    """
    ColorWheel is just an array of colors.py to display!
    I've tested patterns 40-200 colors.py in length.
    """

    def __init__(self, array):
        self.array = array

    def __add__(self, other):
        return ColorWheel(self.array + other.array)

    def __len__(self) -> int:
        return len(self.array)

    def shifted_pct(self, pct: float):
        """
        rotates the color wheel by a percentage of it's width
        :param pct: the amount to rotate the wheel, 0-100
        :return: a new wheel, shifted by pct%
        """
        amount = int(pct * len(self.array))
        return self.shifted_amount(amount)

    def shifted_amount(self, amount: float):
        """
        rotates the color wheel by an amount
        :param amount: the amount to rotate the wheel
        :return: a new wheel, shifted by amount
        """
        amount = amount % len(self)
        return ColorWheel(self.array[amount:] + self.array[:amount])

    def get_array(self, output_size) -> List[RGBColor]:
        """
        repeats the color wheel in an array of output_size
        :param output_size:
        :return: a list of length output_size, repeating the input wheel until complete
        """
        return [self.array[n % len(self)] for n in range(output_size)]


def BlendedWheel(
        start_hue: int,
        end_hue: int,
        length: int,
        saturation: int = 100,
        brightness: int = 100,
) -> ColorWheel:
    """
    :param start_hue: the starting hue value
    :param end_hue: the ending hue value
    :param length: the size of the output range
    :param saturation: the saturation of the gradient
    :param brightness: the brightness value
    :return: a HSV gradient between start_hue and end_hue
    """
    return ColorWheel([
        RGBColor.fromHSV(hue, saturation, brightness)
        for hue in BlendedHueRange(start_hue, end_hue, length)
    ])


def FadeHueBrightess(hue, start, end, length) -> ColorWheel:
    return ColorWheel([
        RGBColor.fromHSV(hue, 100, int(scale_value(start, end, n / length)))
        for n in range(length)
    ])


class Palette:
    main_hsv: int = random.randrange(0, 360, 10)
    alt_hsv_distance: int = 40
    third_hsv_distance: int = 20
    saturation: int = 100
    value: int = 100

    def set_main_hue(self, value):
        self.main_hsv = value

    @property
    def alt_hsv(self):
        return self.main_hsv + self.alt_hsv_distance

    @property
    def third_hsv(self):
        return self.main_hsv - self.third_hsv_distance

    @property
    def inverse_hsv(self):
        return self.main_hsv + 180

    @property
    def saturation(self):
        return self.saturation

    @property
    def value(self):
        return self.value

    @property
    def main(self):
        return RGBColor.fromHSV(self.main_hsv, self.saturation, self.value)

    @property
    def alternate(self):
        return RGBColor.fromHSV(self.alt_hsv, self.saturation, self.value)

    @property
    def third(self):
        return RGBColor.fromHSV(self.third_hsv, self.saturation, self.value)

    @property
    def inverse(self):
        return RGBColor.fromHSV(self.inverse_hsv, self.saturation, self.value)


class Segment(object):
    def __init__(self, title, device: orgb.Device, start=0, end=-1, offset=0):
        self.title = title
        self.device = device
        self.start = start
        self.end = end
        if end < 0:
            self.end = len(device.leds) + end + 1

        self.position_offset = offset

    def __len__(self):
        return self.end - self.start

    def set_colors(self, colors, fast=False):
        return self.device.set_colors(colors, self.start, self.end, fast=fast)

    def apply_wheel(self, wheel: ColorWheel, render_position: float, position_is_percent=False):
        shifted = position_is_percent and wheel.shifted_pct or wheel.shifted_amount
        return self.set_colors(shifted(render_position + self.position_offset).get_array(len(self)))

    def dump(self):
        summary = self.device.name
        if self.start != 0 or self.end != -1:
            summary += "[%s:%s]" % (self.start or "", self.end != -1 and self.end or "")
        return "Segment[%s]: %s" % (self.title, summary)


class Region(object):
    def __init__(self, title, segments=None):
        self.title = title
        self.segments = segments or []

    def apply_wheel(self, wheel: ColorWheel, render_position: float, position_is_percent=False):
        for number, seg in enumerate(self.segments):
            if number % 2 == 1:
                if position_is_percent:
                    seg.position_offset = 0.50
                else:
                    seg.position_offset = len(wheel) // 2
            seg.apply_wheel(wheel, render_position, position_is_percent)

    def dump(self):
        return ("Region[%s]:\n%s" % (
            self.title,
            "\n".join("  " + seg.dump() for seg in self.segments)
        ))


class PlaidManager(object):
    start: datetime
    now: datetime
    frame_times: List[float]
    regions: Dict[str, Region]
    cached_wheel: ColorWheel

    def __init__(self):
        self.client = OpenRGBClient()
        self.client.connect()
        self.map_segments()
        self.frame = 0
        self.gradient_frame = 0
        self.fps = 30
        self.palette = Palette()
        self.frame_times = []

    @property
    def devices(self) -> List[orgb.Device]:
        return self.client.devices

    def map_segments(self):
        regions = {
        }
        for d in self.devices:
            typename = d.type.name
            if typename not in regions:
                regions[typename] = Region(typename)

            if d.type == orgb.utils.DeviceType.DRAM:
                regions['DRAM'].segments.append(
                    Segment("ram-%s" % (len(regions['DRAM'].segments) + 1), d)
                )
            elif d.type == orgb.utils.DeviceType.MOTHERBOARD:
                regions['MOTHERBOARD'].segments.append(
                    Segment("mobo", d)
                )
            elif d.type == orgb.utils.DeviceType.KEYBOARD:
                regions['KEYBOARD'].segments.append(
                    Segment("kb", d)
                )
            elif d.type == orgb.utils.DeviceType.MOUSE:
                regions['MOUSE'].segments.append(
                    Segment("mouse", d)
                )
            elif d.type == orgb.utils.DeviceType.COOLER:
                fan_size = len(d.leds) // 3
                for i in range(0, len(d.leds)//fan_size):
                    regions['COOLER'].segments.append(
                        Segment("cooler-%s" % (i + 1), d, i*fan_size, (i +1)* fan_size)
                    )
            else:
                print("UNKNOWN DEVICE", d, typename)

        print("Mapped regions:\n======\n")
        for k, v in regions.items():
            print(v.dump())

        self.regions = regions

    @property
    def wheel(self):
        if not getattr(self, "cached_wheel", None):
            self.cached_wheel = (
                    BlendedWheel(self.palette.main_hsv, self.palette.main_hsv, 48)
                    + BlendedWheel(self.palette.main_hsv, self.palette.main_hsv, 16)
                    + BlendedWheel(self.palette.main_hsv, self.palette.third_hsv, 16)
                    + BlendedWheel(self.palette.third_hsv, self.palette.main_hsv, 16)
                    + BlendedWheel(self.palette.main_hsv, self.palette.alt_hsv, 16)
                    + BlendedWheel(self.palette.alt_hsv, self.palette.main_hsv, 16)
                    + BlendedWheel(self.palette.main_hsv, self.palette.main_hsv, 16)
                    + BlendedWheel(self.palette.main_hsv, self.palette.third_hsv, 16)
                    + BlendedWheel(self.palette.third_hsv, self.palette.main_hsv, 16)
                    + BlendedWheel(self.palette.main_hsv, self.palette.main_hsv, 48)
                    + BlendedWheel(self.palette.main_hsv, self.palette.alt_hsv, 16)
                    + BlendedWheel(self.palette.alt_hsv, self.palette.main_hsv, 48)
                    + BlendedWheel(self.palette.main_hsv, self.palette.main_hsv, 16)
                    + BlendedWheel(self.palette.main_hsv, self.palette.third_hsv, 16)
                    + BlendedWheel(self.palette.third_hsv, self.palette.main_hsv, 16)
            )
        return self.cached_wheel

    def RenderAnimationFrame(self):
        if self.now.hour >= 23 or self.now.hour <= 8:
            self.Off()
        else:
            self.Gradient()

    def Off(self):
        for d in self.devices:
            d.set_color(RGBColor.fromHSV(0, 0, 0))

    def Rainbow(self):
        self.gradient_frame += 1
        for d in self.devices:
            colors = []
            for n, led in enumerate(d.leds):
                colors.append(RGBColor.fromHSV((self.gradient_frame + n) * 3 % 360, 100, 100))
            d.set_colors(colors)

    def Solid(self, color=None):
        for d in self.devices:
            d.set_color(color or self.palette.main)

    def Gradient(self):
        self.gradient_frame = self.gradient_frame + 1
        for n, name in enumerate(self.regions.keys()):
            region = self.regions[name]
            region.apply_wheel(self.wheel, self.gradient_frame)

    def OncePerSecond(self):
        self.now = datetime.now()
        self.palette.main_hsv = int(time.time()) % 360
        self.cached_wheel = None

        if self.now.second % 10 == 0 and self.frame_times:
            frame_time_avg = sum(self.frame_times) / len(self.frame_times)
            print(
                f"Avg frame: {int(frame_time_avg * 1000)}ms, FPS: {int(1 / frame_time_avg)}, Color: {self.palette.main_hsv}/{self.palette.alt_hsv}/{self.palette.third_hsv}"
            )

    def Start(self):
        self.start = datetime.now()
        sec_per_frame = 1 / self.fps
        for d in self.devices:
            d.set_mode(0)

        self.OncePerSecond()
        while True:
            begin = time.time()
            self.frame += 1
            self.RenderAnimationFrame()
            elapsed = time.time() - begin
            sleep_needed = sec_per_frame - elapsed
            if sleep_needed > 0:
                time.sleep(sleep_needed)
            self.frame_times = [
                                   elapsed,
                               ] + self.frame_times[:99]
            if self.frame % self.fps == 0:
                self.OncePerSecond()


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    manager = PlaidManager()
    manager.Start()
