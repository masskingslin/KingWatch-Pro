"""
KingWatch Pro v17 - themes.py
8 modern themes with distinct colour identities.
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
    # ── 1. Dark Pro — default dark with vivid green ──────────────────────
    "Dark Pro": {
        "BG":     "#0A0A0A",
        "CARD":   "#141414",
        "TEXT":   "#FFFFFF",
        "DIM":    "#444444",
        "ACCENT": "#00E676",
        "WARN":   "#FF9100",
        "DANGER": "#FF1744",
    },
    # ── 2. Amoled — true black OLED, electric cyan ───────────────────────
    "Amoled": {
        "BG":     "#000000",
        "CARD":   "#0A0A0A",
        "TEXT":   "#FFFFFF",
        "DIM":    "#333333",
        "ACCENT": "#00E5FF",
        "WARN":   "#FFAB00",
        "DANGER": "#FF1744",
    },
    # ── 3. Cyber Neon — dark purple base, hot magenta + yellow ───────────
    "Cyber Neon": {
        "BG":     "#0D001A",
        "CARD":   "#1A0030",
        "TEXT":   "#F0E6FF",
        "DIM":    "#6600AA",
        "ACCENT": "#FF00FF",
        "WARN":   "#FFE600",
        "DANGER": "#FF1744",
    },
    # ── 4. Ocean Deep — deep navy, aqua accent ───────────────────────────
    "Ocean Deep": {
        "BG":     "#020C18",
        "CARD":   "#071828",
        "TEXT":   "#E0F4FF",
        "DIM":    "#1E4D6B",
        "ACCENT": "#00BCD4",
        "WARN":   "#FF9800",
        "DANGER": "#F44336",
    },
    # ── 5. Sunset Lava — near-black warm, vivid orange-red ───────────────
    "Sunset Lava": {
        "BG":     "#120500",
        "CARD":   "#1E0A00",
        "TEXT":   "#FFE5CC",
        "DIM":    "#7A3000",
        "ACCENT": "#FF6D00",
        "WARN":   "#FFCA28",
        "DANGER": "#DD2C00",
    },
    # ── 6. Forest Night — deep green-black, lime accent ──────────────────
    "Forest Night": {
        "BG":     "#030F03",
        "CARD":   "#091509",
        "TEXT":   "#D4EDDA",
        "DIM":    "#2E5E2E",
        "ACCENT": "#76FF03",
        "WARN":   "#FFD600",
        "DANGER": "#FF3D00",
    },
    # ── 7. Arctic Ice — cool dark slate, sky blue accent ─────────────────
    "Arctic Ice": {
        "BG":     "#040D14",
        "CARD":   "#0A1A26",
        "TEXT":   "#E8F4FD",
        "DIM":    "#1E4060",
        "ACCENT": "#40C4FF",
        "WARN":   "#FFD740",
        "DANGER": "#FF5252",
    },
    # ── 8. Royal Purple — deep indigo, violet + gold ─────────────────────
    "Royal Purple": {
        "BG":     "#080010",
        "CARD":   "#120020",
        "TEXT":   "#EDE7F6",
        "DIM":    "#4A1080",
        "ACCENT": "#CE93D8",
        "WARN":   "#FFD54F",
        "DANGER": "#FF5252",
    },
}


def get_theme(name: str) -> dict:
    return _THEMES.get(name, _THEMES["Dark Pro"])
