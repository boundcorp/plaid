from openrgb.utils import RGBColor
BLACK = RGBColor.fromHSV(0, 0, 0)
WHITE = RGBColor.fromHSV(0, 0, 100)

def scale_value(start: float, end: float, pct: float) -> float:
    """
    :param start: beginning float value
    :param end:  end float value
    :param pct: float 0-1 distance from start to end
    :return: a scaled float that is pct distance between start and end
    """
    return int(start + (end - start) * abs(pct))
