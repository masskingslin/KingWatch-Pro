THEMES = {
    "Dark Pro": {
        "BG":"#0A0A0A","CARD":"#161616","CARD2":"#242424",
        "TEXT":"#FFFFFF","DIM":"#555555",
        "ACCENT":"#00E676","WARN":"#FF9100","DANGER":"#FF1744",
        "BTN_TEXT":"#000000"
    },

    "Amoled": {
        "BG":"#000000","CARD":"#0D0D0D","CARD2":"#1A1A1A",
        "TEXT":"#FFFFFF","DIM":"#444444",
        "ACCENT":"#03DAC6","WARN":"#FFB74D","DANGER":"#CF6679",
        "BTN_TEXT":"#000000"
    },

    "Midnight": {
        "BG":"#0D1B2A","CARD":"#1B263B","CARD2":"#243B55",
        "TEXT":"#E0E1DD","DIM":"#778DA9",
        "ACCENT":"#4FC3F7","WARN":"#FFA726","DANGER":"#EF5350",
        "BTN_TEXT":"#0D1B2A"
    },

    "Cyberpunk": {
        "BG":"#0A0010","CARD":"#150025","CARD2":"#200038",
        "TEXT":"#F0E6FF","DIM":"#9E77CC",
        "ACCENT":"#FF00FF","WARN":"#FF6D00","DANGER":"#FF1744",
        "BTN_TEXT":"#000000"
    },

    "Solarized": {
        "BG":"#002B36","CARD":"#073642","CARD2":"#0A4252",
        "TEXT":"#FDF6E3","DIM":"#657B83",
        "ACCENT":"#2AA198","WARN":"#CB4B16","DANGER":"#DC322F",
        "BTN_TEXT":"#002B36"
    },

    "Forest": {
        "BG":"#071A0F","CARD":"#0E2918","CARD2":"#163D24",
        "TEXT":"#E8F5E9","DIM":"#4CAF50",
        "ACCENT":"#69F0AE","WARN":"#FF7043","DANGER":"#EF5350",
        "BTN_TEXT":"#071A0F"
    },

    "Sunset": {
        "BG":"#1A0A00","CARD":"#2C1500","CARD2":"#3E1F00",
        "TEXT":"#FFF3E0","DIM":"#FF8A65",
        "ACCENT":"#FF6D00","WARN":"#FFCA28","DANGER":"#F44336",
        "BTN_TEXT":"#000000"
    },

    "Ice Blue": {
        "BG":"#E8F4FD","CARD":"#FFFFFF","CARD2":"#D6ECFA",
        "TEXT":"#0D2137","DIM":"#607D8B",
        "ACCENT":"#0288D1","WARN":"#F57C00","DANGER":"#D32F2F",
        "BTN_TEXT":"#FFFFFF"
    }
}

THEME_NAMES = list(THEMES.keys())
DEFAULT_THEME = "Dark Pro"


def get_theme(name=DEFAULT_THEME):
    return THEMES.get(name, THEMES[DEFAULT_THEME])