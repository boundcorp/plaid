from typing import List

from openrgb.utils import RGBColor

from plaid.colors import scale_value


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
    return ColorWheel(
        [
            RGBColor.fromHSV(hue, saturation, brightness)
            for hue in BlendedHueRange(start_hue, end_hue, length)
        ]
    )


def FadeHueBrightess(hue, start, end, length) -> ColorWheel:
    return ColorWheel(
        [
            RGBColor.fromHSV(hue, 100, int(scale_value(start, end, n / length)))
            for n in range(length)
        ]
    )
