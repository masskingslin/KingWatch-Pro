"""
KingWatch Pro v17 - themes.py
8 modern themes. All text colours are bright/white for readability.
No unicode, no emoji.
"""

THEME_NAMES = [
    "Dark Pro",
    "Amoled",
    "Cyber Neon",
    "Ocean Deep",
    "Sunset Lava",
    "Forest Night",
    "Arctic Ice",
    "Royal Purple",
]

_THEMES = {
    # 1. Dark Pro - classic dark, bright green accent
    "Dark Pro": {
        "BG":     "#0A0A0A",
        "CARD":   "#1A1A1A",
        "TEXT":   "#FFFFFF",
        "DIM":    "#888888",
        "ACCENT": "#00E676",
        "WARN":   "#FF9100",
        "DANGER": "#FF1744",
    },
    # 2. Amoled - true black, white text, cyan accent
    "Amoled": {
        "BG":     "#000000",
        "CARD":   "#111111",
        "TEXT":   "#FFFFFF",
        "DIM":    "#777777",
        "ACCENT": "#18FFFF",
        "WARN":   "#FFD740",
        "DANGER": "#FF1744",
    },
    # 3. Cyber Neon - dark purple, white text, magenta accent
    "Cyber Neon": {
        "BG":     "#110022",
        "CARD":   "#1E0038",
        "TEXT":   "#FFFFFF",
        "DIM":    "#9966CC",
        "ACCENT": "#FF40FF",
        "WARN":   "#FFFF00",
        "DANGER": "#FF3040",
    },
    # 4. Ocean Deep - dark navy, white text, aqua accent
    "Ocean Deep": {
        "BG":     "#03111F",
        "CARD":   "#071E30",
        "TEXT":   "#FFFFFF",
        "DIM":    "#5599BB",
        "ACCENT": "#00E5FF",
        "WARN":   "#FF9800",
        "DANGER": "#FF3D00",
    },
    # 5. Sunset Lava - dark warm, white text, orange accent
    "Sunset Lava": {
        "BG":     "#150800",
        "CARD":   "#221200",
        "TEXT":   "#FFFFFF",
        "DIM":    "#AA6622",
        "ACCENT": "#FF6D00",
        "WARN":   "#FFD600",
        "DANGER": "#DD2C00",
    },
    # 6. Forest Night - dark green, white text, lime accent
    "Forest Night": {
        "BG":     "#041204",
        "CARD":   "#0A1E0A",
        "TEXT":   "#FFFFFF",
        "DIM":    "#449944",
        "ACCENT": "#69FF47",
        "WARN":   "#FFD600",
        "DANGER": "#FF3D00",
    },
    # 7. Arctic Ice - dark slate, white text, sky blue accent
    "Arctic Ice": {
        "BG":     "#06101A",
        "CARD":   "#0D1E2E",
        "TEXT":   "#FFFFFF",
        "DIM":    "#5588AA",
        "ACCENT": "#40C4FF",
        "WARN":   "#FFD740",
        "DANGER": "#FF5252",
    },
    # 8. Royal Purple - dark indigo, white text, violet accent
    "Royal Purple": {
        "BG":     "#0C0018",
        "CARD":   "#180030",
        "TEXT":   "#FFFFFF",
        "DIM":    "#9966BB",
        "ACCENT": "#EA80FC",
        "WARN":   "#FFD54F",
        "DANGER": "#FF5252",
    },
}


def get_theme(name):
    return _THEMES.get(name, _THEMES["Dark Pro"])
