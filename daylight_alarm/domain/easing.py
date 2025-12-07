def ease_linear(t: float) -> float:
    return t


def ease_in_quad(t: float) -> float:
    return t * t


def ease_in_cubic(t: float) -> float:
    return t * t * t


def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)
