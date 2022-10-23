import subprocess
import time
from datetime import datetime
from typing import List, Dict

from openrgb import OpenRGBClient, orgb
from openrgb.utils import RGBColor

from plaid.layout import Region, Segment
from plaid.palette import Palette
from plaid.utils import ColorWheel, BlendedWheel


class PlaidManager(object):
    start: datetime
    now: datetime
    frame_times: List[float]
    regions: Dict[str, Region]
    cached_wheel: ColorWheel
    client: OpenRGBClient

    def __init__(self):
        self.frame = 0
        self.gradient_frame = 0
        self.fps = 15
        self.palette = Palette()
        self.frame_times = []
        self.safe_connect()
        self.map_segments()

    def safe_connect(self, wait=5, tries=5, restart_service=3):
        for i in range(tries):
            try:
                client = OpenRGBClient()
                client.connect()
                if not client.devices:
                    raise
                self.client = client
                print("Connected!")
                return client
            except:
                print(f"Connection error, waiting {wait} seconds for openrgb...")
                time.sleep(wait)
        if restart_service:
            print("Error connecting, killing openrgb...")
            try:
                subprocess.check_output(["pkill", "openrgb"])
            except:
                pass
            print("restarting service...")
            subprocess.check_output(["sudo", "service", "openrgb", "restart"])
            print("waiting for service init...")
            time.sleep(10)
            return self.safe_connect(
                wait=wait, tries=tries, restart_service=restart_service - 1
            )

        raise Exception("plaid unable to connect")

    @property
    def devices(self) -> List[orgb.Device]:
        return self.client.devices

    def map_segments(self):
        regions = {}
        for d in self.devices:
            typename = d.type.name
            if typename not in regions:
                regions[typename] = Region(typename)

            if d.type == orgb.utils.DeviceType.DRAM:
                regions["DRAM"].add_segment(
                    Segment("ram-%s" % (len(regions["DRAM"].segments) + 1), d)
                )
            elif d.type == orgb.utils.DeviceType.MOTHERBOARD:
                regions["MOTHERBOARD"].add_segment(Segment("mobo", d))
            elif d.type == orgb.utils.DeviceType.KEYBOARD:
                regions["KEYBOARD"].add_segment(Segment("kb", d))
            elif d.type == orgb.utils.DeviceType.MOUSE:
                regions["MOUSE"].add_segment(Segment("mouse", d))
            elif d.type == orgb.utils.DeviceType.MOUSEMAT:
                regions["MOUSEMAT"].add_segment(Segment("mousemat", d))
            elif d.type == orgb.utils.DeviceType.HEADSET:
                regions["HEADSET"].add_segment(Segment("headset", d))
            elif d.type == orgb.utils.DeviceType.COOLER:
                fan_size = len(d.leds) // 3
                for i in range(0, len(d.leds) // fan_size):
                    seg = regions["COOLER"].add_segment(
                        Segment(
                            "cooler-%s" % (i + 1),
                            d,
                            i * fan_size,
                            (i + 1) * fan_size,
                        )
                    )
                    seg.fast_update = False
            else:
                print("UNKNOWN DEVICE", d, typename)

        print("Mapped regions:\n======\n")
        for k, v in regions.items():
            print(v.dump())

        self.regions = regions

    @property
    def wheel(self):
        if not getattr(self, "cached_wheel", None):
            self.cached_wheel = self.build_wheel()
            self.after_build_wheel()
        return self.cached_wheel

    def build_wheel(self):
        return (
                BlendedWheel(self.palette.main_hsv, self.palette.main_hsv, 64)
                + BlendedWheel(self.palette.main_hsv, self.palette.third_hsv, 32)
                + BlendedWheel(self.palette.third_hsv, self.palette.main_hsv, 32)
                + BlendedWheel(self.palette.main_hsv, self.palette.alt_hsv, 32)
                + BlendedWheel(self.palette.alt_hsv, self.palette.main_hsv, 32)
                + BlendedWheel(self.palette.main_hsv, self.palette.main_hsv, 64)
                + BlendedWheel(self.palette.main_hsv, self.palette.third_hsv, 32)
                + BlendedWheel(self.palette.third_hsv, self.palette.main_hsv, 32)
        )

    def after_build_wheel(self):
        for number, seg in enumerate(self.regions["COOLER"].segments):
            seg.position_offset = seg.odd and len(self.cached_wheel) // 2 or 0
            seg.reverse_direction = seg.odd
            seg.reverse_wheel = seg.odd

        for number, seg in enumerate(self.regions["DRAM"].segments):
            seg.position_offset = seg.odd and len(self.cached_wheel) // 2 or 0
            seg.reverse_direction = seg.odd
            seg.reverse_wheel = seg.odd

    def RenderAnimationFrame(self):
        # if self.now.hour >= 23 or self.now.hour <= 8:
        # self.Off()
        # else:
        self.Gradient()

    def Off(self):
        for d in self.devices:
            d.set_color(RGBColor.fromHSV(0, 0, 0))

    def Rainbow(self):
        self.gradient_frame += 1
        for d in self.devices:
            colors = []
            for n, led in enumerate(d.leds):
                colors.append(
                    RGBColor.fromHSV((self.gradient_frame + n) * 3 % 360, 100, 100)
                )
            d.set_colors(colors)

    def Solid(self, color=None):
        for d in self.devices:
            d.set_color(color or self.palette.main)

    def Gradient(self):
        self.gradient_frame = self.gradient_frame + 1
        for n, name in enumerate(self.regions.keys()):
            region = self.regions[name]
            region.apply_wheel(self.wheel, self.gradient_frame)

        self.DrawToDevices()

    def DrawToDevices(self):
        for d in self.devices:
            start = time.time()
            d.show(fast=True)
            end = time.time()
            elapsed_ms = (end - start) * 1000
            if elapsed_ms > 10:
                print("SLOW DEVICE PAINT:", d.name, "show took", elapsed_ms, "ms")

    def OncePerSecond(self):
        self.now = datetime.now()
        self.palette.main_hsv = int(time.time()) % 360
        self.cached_wheel = None

        if self.now.second % 10 == 0 and self.frame_times:
            frame_time_avg = sum(self.frame_times) / len(self.frame_times)
            print(
                f"Avg frame: {int(frame_time_avg * 1000)}ms, FPS: {int(1 / frame_time_avg)}, Color: {self.palette.main_hsv}/{self.palette.alt_hsv}/{self.palette.third_hsv}"
            )

    def RemindDevicesDirectMode(self):
        for d in self.devices:
            d.set_mode(0)

    def Start(self):
        self.start = datetime.now()
        sec_per_frame = 1 / self.fps

        self.RemindDevicesDirectMode()

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
            if self.now.second != datetime.now().second:
                self.OncePerSecond()


