from typing import List
from openrgb import orgb, OpenRGBClient
from openrgb.utils import RGBColor
from datetime import datetime
import time, random


class Palette():
    main_hsv: int = random.randrange(0,360,10)
    alt_hsv_distance: int = 40
    third_hsv_distance: int = 20
    saturation: int = 100
    value: int = 100


    def set_main_hue(self, value):
        self.main_hsv = value

    @property
    def alt_hsv(self):
        return (self.main_hsv + self.alt_hsv_distance)

    @property
    def third_hsv(self):
        return (self.main_hsv - self.third_hsv_distance)

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


def BlendHue(start_hue: int, end_hue: int, pct):
    return (start_hue + (end_hue - start_hue) * abs(pct)) % 360


def BlendedHueRange(start_hue: int, end_hue: int, length: int):
    return [
        BlendHue(start_hue, end_hue, n / (length - 1))
        for n in range(length)
    ]


def BlendedColorRange(start_hue: int, end_hue: int, length: int, saturation: int = 100, value: int = 100):
    return [
        RGBColor.fromHSV(hue, saturation, value)
        for hue in BlendedHueRange(start_hue, end_hue, length)
    ]


def Spin(array, pct):
    spin_size = int(pct / 100.0 * len(array))
    return array[spin_size:] + array[:spin_size]


def RepeatLength(array, length):
    return [
        array[n % len(array)]
        for n in range(length)
    ]


class PlaidManager(object):
    start: datetime
    now: datetime
    frame_times: List[int]
    gradient_wheel_colors: List[RGBColor]

    def __init__(self):
        self.client = OpenRGBClient()
        self.client.connect()
        self.frame = 0
        self.fps = 30
        self.palette = Palette()
        self.frame_times = []

    @property
    def devices(self) -> List[orgb.Device]:
        return self.client.devices

    @property
    def gradient_wheel(self):
        if not getattr(self, 'gradient_wheel_colors', None):
            self.gradient_wheel_colors = (
                    BlendedColorRange(self.palette.main_hsv, self.palette.alt_hsv, 64) +
                    BlendedColorRange(self.palette.alt_hsv, self.palette.main_hsv, 64) +
                    BlendedColorRange(self.palette.main_hsv, self.palette.main_hsv, 32) +
                    BlendedColorRange(self.palette.main_hsv, self.palette.third_hsv, 32) +
                    BlendedColorRange(self.palette.third_hsv, self.palette.main_hsv, 32) +
                    BlendedColorRange(self.palette.main_hsv, self.palette.main_hsv, 64)

            )
        return self.gradient_wheel_colors

    def RenderAnimationFrame(self):
        if self.now.hour >= 23 or self.now.hour <= 8:
            self.Off()
        else:
            self.Gradient()

    def Off(self):
        for d in self.devices:
            d.set_color(RGBColor.fromHSV(0, 0, 0))

    def Rainbow(self):
        for d in self.devices:
            colors = []
            for n, led in enumerate(d.leds):
                colors.append(RGBColor.fromHSV((self.frame + n) * 3 % 360, 100, 100))
            d.set_colors(colors)

    def Solid(self, color=None):
        for d in self.devices:
            d.set_color(color or self.palette.main)

    def Gradient(self):
        for n,d in enumerate(self.devices):
            colors = RepeatLength(Spin(self.gradient_wheel, (self.frame+n+n+n) % 100), len(d.leds))
            d.set_colors(colors)

    def OncePerSecond(self):
        self.now = datetime.now()
        self.palette.main_hsv = int(time.time()) % 360
        self.gradient_wheel_colors = None

        if self.now.second % 10 == 0 and self.frame_times:
            frame_time_avg = sum(self.frame_times) / len(self.frame_times)
            print(f"Avg frame: {int(frame_time_avg * 1000)}ms, FPS: {int(1 / frame_time_avg)}, Color: {self.palette.main_hsv}/{self.palette.alt_hsv}/{self.palette.third_hsv}")

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
            self.frame_times = [elapsed, ] + self.frame_times[:99]
            if self.frame % self.fps == 0:
                self.OncePerSecond()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    manager = PlaidManager()
    manager.Start()
