from kivy.utils import get_color_from_hex


class ThemeBase:
    BG = None
    CARD = None
    TEXT = None
    ACCENT = None


class DarkPro(ThemeBase):
    BG = get_color_from_hex("#000000")
    CARD = get_color_from_hex("#1E1E1E")
    TEXT = get_color_from_hex("#FFFFFF")
    ACCENT = get_color_from_hex("#00C853")


class MidnightBlue(ThemeBase):
    BG = get_color_from_hex("#0D1B2A")
    CARD = get_color_from_hex("#1B263B")
    TEXT = get_color_from_hex("#E0E1DD")
    ACCENT = get_color_from_hex("#778DA9")


class AmoledBlack(ThemeBase):
    BG = get_color_from_hex("#000000")
    CARD = get_color_from_hex("#121212")
    TEXT = get_color_from_hex("#FFFFFF")
    ACCENT = get_color_from_hex("#03DAC6")


class Cyberpunk(ThemeBase):
    BG = get_color_from_hex("#0F0F0F")
    CARD = get_color_from_hex("#1F1F1F")
    TEXT = get_color_from_hex("#F5F5F5")
    ACCENT = get_color_from_hex("#FF00FF")


class SolarizedDark(ThemeBase):
    BG = get_color_from_hex("#002B36")
    CARD = get_color_from_hex("#073642")
    TEXT = get_color_from_hex("#EEE8D5")
    ACCENT = get_color_from_hex("#B58900")


class ForestGreen(ThemeBase):
    BG = get_color_from_hex("#0B3D2E")
    CARD = get_color_from_hex("#145A32")
    TEXT = get_color_from_hex("#E8F5E9")
    ACCENT = get_color_from_hex("#66BB6A")


class SunsetOrange(ThemeBase):
    BG = get_color_from_hex("#2C1A1D")
    CARD = get_color_from_hex("#4E342E")
    TEXT = get_color_from_hex("#FFFFFF")
    ACCENT = get_color_from_hex("#FF7043")


class LightMode(ThemeBase):
    BG = get_color_from_hex("#F5F5F5")
    CARD = get_color_from_hex("#FFFFFF")
    TEXT = get_color_from_hex("#000000")
    ACCENT = get_color_from_hex("#1976D2")


THEMES = {
    "dark": DarkPro,
    "midnight": MidnightBlue,
    "amoled": AmoledBlack,
    "cyberpunk": Cyberpunk,
    "solarized": SolarizedDark,
    "forest": ForestGreen,
    "sunset": SunsetOrange,
    "light": LightMode
}