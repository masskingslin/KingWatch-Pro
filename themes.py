# themes.py — 8 themes, hex strings only (Android safe, no Kivy at import time)

THEMES = {
    "Dark Pro": {
        "BG": "#0A0A0A", "CARD": "#161616", "CARD2": "#1E1E1E",
        "TEXT": "#FFFFFF", "DIM": "#666666",
        "ACCENT": "#00E676", "ACCENT2": "#69F0AE",
        "BTN_TEXT": "#000000", "DANGER": "#FF1744", "WARN": "#FF9100",
    },
    "Amoled": {
        "BG": "#000000", "CARD": "#0D0D0D", "CARD2": "#141414",
        "TEXT": "#FFFFFF", "DIM": "#555555",
        "ACCENT": "#03DAC6", "ACCENT2": "#80CBC4",
        "BTN_TEXT": "#000000", "DANGER": "#CF6679", "WARN": "#FFB74D",
    },
    "Midnight": {
        "BG": "#0D1B2A", "CARD": "#1B263B", "CARD2": "#243B55",
        "TEXT": "#E0E1DD", "DIM": "#778DA9",
        "ACCENT": "#4FC3F7", "ACCENT2": "#81D4FA",
        "BTN_TEXT": "#0D1B2A", "DANGER": "#EF5350", "WARN": "#FFA726",
    },
    "Cyberpunk": {
        "BG": "#0A0010", "CARD": "#150025", "CARD2": "#1F003A",
        "TEXT": "#F0E6FF", "DIM": "#9E77CC",
        "ACCENT": "#FF00FF", "ACCENT2": "#CC00FF",
        "BTN_TEXT": "#FFFFFF", "DANGER": "#FF1744", "WARN": "#FF6D00",
    },
    "Solarized": {
        "BG": "#002B36", "CARD": "#073642", "CARD2": "#0A4252",
        "TEXT": "#FDF6E3", "DIM": "#657B83",
        "ACCENT": "#2AA198", "ACCENT2": "#859900",
        "BTN_TEXT": "#002B36", "DANGER": "#DC322F", "WARN": "#CB4B16",
    },
    "Forest": {
        "BG": "#071A0F", "CARD": "#0E2918", "CARD2": "#163D24",
        "TEXT": "#E8F5E9", "DIM": "#4CAF50",
        "ACCENT": "#69F0AE", "ACCENT2": "#B9F6CA",
        "BTN_TEXT": "#071A0F", "DANGER": "#EF5350", "WARN": "#FF7043",
    },
    "Sunset": {
        "BG": "#1A0A00", "CARD": "#2C1500", "CARD2": "#3E1F00",
        "TEXT": "#FFF3E0", "DIM": "#FF8A65",
        "ACCENT": "#FF6D00", "ACCENT2": "#FF9E40",
        "BTN_TEXT": "#FFFFFF", "DANGER": "#F44336", "WARN": "#FFCA28",
    },
    "Ice Blue": {
        "BG": "#E8F4FD", "CARD": "#FFFFFF", "CARD2": "#F0F8FF",
        "TEXT": "#0D2137", "DIM": "#607D8B",
        "ACCENT": "#0288D1", "ACCENT2": "#039BE5",
        "BTN_TEXT": "#FFFFFF", "DANGER": "#D32F2F", "WARN": "#F57C00",
    },
}

THEME_NAMES = list(THEMES.keys())
DEFAULT_THEME = "Dark Pro"


def get_theme(name=DEFAULT_THEME):
    return THEMES.get(name, THEMES[DEFAULT_THEME])
