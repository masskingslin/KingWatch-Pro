"""
KingWatch Pro - themes.py
8 colour themes.
"""

THEME_NAMES = [
    "Dark Pro",
    "Amoled",
    "Midnight",
    "Cyberpunk",
    "Solarized",
    "Forest",
    "Sunset",
    "Ice Blue",
]

_THEMES = {
    "Dark Pro": {
        "BG":     "#0A0A0A",
        "CARD":   "#161616",
        "CARD2":  "#1E1E1E",
        "TEXT":   "#FFFFFF",
        "DIM":    "#555555",
        "ACCENT": "#00E676",
        "WARN":   "#FF9100",
        "DANGER": "#FF1744",
    },
    "Amoled": {
        "BG":     "#000000",
        "CARD":   "#0D0D0D",
        "CARD2":  "#1A1A1A",
        "TEXT":   "#FFFFFF",
        "DIM":    "#444444",
        "ACCENT": "#00E5FF",
        "WARN":   "#FFAB00",
        "DANGER": "#FF1744",
    },
    "Midnight": {
        "BG":     "#0D0D2B",
        "CARD":   "#13133D",
        "CARD2":  "#1A1A4F",
        "TEXT":   "#E8E8FF",
        "DIM":    "#5050AA",
        "ACCENT": "#7C83FD",
        "WARN":   "#FFAB40",
        "DANGER": "#FF5252",
    },
    "Cyberpunk": {
        "BG":     "#0D001A",
        "CARD":   "#1A0030",
        "CARD2":  "#260040",
        "TEXT":   "#F0E6FF",
        "DIM":    "#7700AA",
        "ACCENT": "#FF00FF",
        "WARN":   "#FFFF00",
        "DANGER": "#FF1744",
    },
    "Solarized": {
        "BG":     "#002B36",
        "CARD":   "#073642",
        "CARD2":  "#073642",
        "TEXT":   "#FDF6E3",
        "DIM":    "#586E75",
        "ACCENT": "#2AA198",
        "WARN":   "#CB4B16",
        "DANGER": "#DC322F",
    },
    "Forest": {
        "BG":     "#0A1A0A",
        "CARD":   "#112211",
        "CARD2":  "#1A2E1A",
        "TEXT":   "#D4EDDA",
        "DIM":    "#3A5C3A",
        "ACCENT": "#4CAF50",
        "WARN":   "#FFC107",
        "DANGER": "#F44336",
    },
    "Sunset": {
        "BG":     "#1A0A00",
        "CARD":   "#2E1500",
        "CARD2":  "#3D1F00",
        "TEXT":   "#FFE5CC",
        "DIM":    "#8B4513",
        "ACCENT": "#FF6D00",
        "WARN":   "#FFCA28",
        "DANGER": "#F44336",
    },
    "Ice Blue": {
        "BG":     "#001A2E",
        "CARD":   "#002244",
        "CARD2":  "#003366",
        "TEXT":   "#E0F4FF",
        "DIM":    "#336699",
        "ACCENT": "#00BFFF",
        "WARN":   "#FFD700",
        "DANGER": "#FF4500",
    },
}


def get_theme(name: str) -> dict:
    return _THEMES.get(name, _THEMES["Dark Pro"])