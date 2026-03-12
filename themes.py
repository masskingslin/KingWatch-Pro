# themes.py — store as hex strings, convert only when needed (Android safe)

THEMES = {
    "Dark Pro": {
        "BG":    "#000000",
        "CARD":  "#1E1E1E",
        "TEXT":  "#FFFFFF",
        "ACCENT": "#00C853",
        "BTN_TEXT": "#000000",
    },
    "Amoled Black": {
        "BG":    "#000000",
        "CARD":  "#121212",
        "TEXT":  "#FFFFFF",
        "ACCENT": "#03DAC6",
        "BTN_TEXT": "#000000",
    },
    "Midnight Blue": {
        "BG":    "#0D1B2A",
        "CARD":  "#1B263B",
        "TEXT":  "#E0E1DD",
        "ACCENT": "#778DA9",
        "BTN_TEXT": "#FFFFFF",
    },
    "Cyberpunk": {
        "BG":    "#0F0F0F",
        "CARD":  "#1F1F1F",
        "TEXT":  "#F5F5F5",
        "ACCENT": "#FF00FF",
        "BTN_TEXT": "#000000",
    },
    "Solarized": {
        "BG":    "#002B36",
        "CARD":  "#073642",
        "TEXT":  "#EEE8D5",
        "ACCENT": "#B58900",
        "BTN_TEXT": "#000000",
    },
    "Forest": {
        "BG":    "#0B3D2E",
        "CARD":  "#145A32",
        "TEXT":  "#E8F5E9",
        "ACCENT": "#66BB6A",
        "BTN_TEXT": "#000000",
    },
    "Sunset": {
        "BG":    "#2C1A1D",
        "CARD":  "#4E342E",
        "TEXT":  "#FFFFFF",
        "ACCENT": "#FF7043",
        "BTN_TEXT": "#FFFFFF",
    },
    "Light Mode": {
        "BG":    "#F5F5F5",
        "CARD":  "#FFFFFF",
        "TEXT":  "#000000",
        "ACCENT": "#1976D2",
        "BTN_TEXT": "#FFFFFF",
    },
}

THEME_NAMES = list(THEMES.keys())
DEFAULT_THEME = "Dark Pro"


def get_theme(name=DEFAULT_THEME):
    return THEMES.get(name, THEMES[DEFAULT_THEME])