"""
K-DroidSentinel v2.1.0 - themes.py
8 themes. Default is K-DroidSentinel matching the JSX design.
All TEXT = #FFFFFF. No unicode.
"""

THEME_NAMES = [
    "K-DroidSentinel",
    "Dark Pro",
    "Amoled",
    "Cyber Neon",
    "Ocean Deep",
    "Sunset Lava",
    "Forest Night",
    "Arctic Ice",
]

_THEMES = {
    # 1. K-DroidSentinel - gold/cyan military dark (matches JSX)
    "K-DroidSentinel": {
        "BG":     "#060A12",
        "CARD":   "#0C1220",
        "TEXT":   "#C8D8F0",
        "DIM":    "#4A6080",
        "ACCENT": "#F0C040",
        "WARN":   "#FFA502",
        "DANGER": "#FF4757",
    },
    # 2. Dark Pro
    "Dark Pro": {
        "BG":     "#0A0A0A",
        "CARD":   "#1A1A1A",
        "TEXT":   "#FFFFFF",
        "DIM":    "#888888",
        "ACCENT": "#00E676",
        "WARN":   "#FF9100",
        "DANGER": "#FF1744",
    },
    # 3. Amoled
    "Amoled": {
        "BG":     "#000000",
        "CARD":   "#111111",
        "TEXT":   "#FFFFFF",
        "DIM":    "#777777",
        "ACCENT": "#18FFFF",
        "WARN":   "#FFD740",
        "DANGER": "#FF1744",
    },
    # 4. Cyber Neon
    "Cyber Neon": {
        "BG":     "#110022",
        "CARD":   "#1E0038",
        "TEXT":   "#FFFFFF",
        "DIM":    "#9966CC",
        "ACCENT": "#FF40FF",
        "WARN":   "#FFFF00",
        "DANGER": "#FF3040",
    },
    # 5. Ocean Deep
    "Ocean Deep": {
        "BG":     "#03111F",
        "CARD":   "#071E30",
        "TEXT":   "#FFFFFF",
        "DIM":    "#5599BB",
        "ACCENT": "#00E5FF",
        "WARN":   "#FF9800",
        "DANGER": "#FF3D00",
    },
    # 6. Sunset Lava
    "Sunset Lava": {
        "BG":     "#150800",
        "CARD":   "#221200",
        "TEXT":   "#FFFFFF",
        "DIM":    "#AA6622",
        "ACCENT": "#FF6D00",
        "WARN":   "#FFD600",
        "DANGER": "#DD2C00",
    },
    # 7. Forest Night
    "Forest Night": {
        "BG":     "#041204",
        "CARD":   "#0A1E0A",
        "TEXT":   "#FFFFFF",
        "DIM":    "#449944",
        "ACCENT": "#69FF47",
        "WARN":   "#FFD600",
        "DANGER": "#FF3D00",
    },
    # 8. Arctic Ice
    "Arctic Ice": {
        "BG":     "#06101A",
        "CARD":   "#0D1E2E",
        "TEXT":   "#FFFFFF",
        "DIM":    "#5588AA",
        "ACCENT": "#40C4FF",
        "WARN":   "#FFD740",
        "DANGER": "#FF5252",
    },
}


def get_theme(name):
    return _THEMES.get(name, _THEMES["K-DroidSentinel"])
