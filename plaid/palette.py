import random

from openrgb.utils import RGBColor


class Palette:
    main_hsv: int = random.randrange(0, 360, 10)
    alt_hsv_distance: int = 40
    third_hsv_distance: int = 60
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
