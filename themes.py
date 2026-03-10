"""
Theme Manager — KingWatch Pro v15
8 color themes. Each theme defines:
  bg   : window/background color  (RGBA)
  arc  : gauge arc primary color  (RGBA)
  text : primary text color       (RGBA)
  card : card/row background      (RGBA)
"""


class ThemeManager:

    THEMES = {
        "DARK": {
            "bg":   (0.05, 0.05, 0.08, 1),
            "arc":  (0.24, 0.86, 0.51, 1),
            "text": (0.95, 0.95, 0.95, 1),
            "card": (0.10, 0.10, 0.16, 1),
        },
        "CYBER": {
            "bg":   (0.02, 0.05, 0.10, 1),
            "arc":  (0.00, 0.90, 1.00, 1),
            "text": (0.00, 0.90, 1.00, 1),
            "card": (0.05, 0.10, 0.20, 1),
        },
        "OCEAN": {
            "bg":   (0.02, 0.08, 0.18, 1),
            "arc":  (0.30, 0.75, 1.00, 1),
            "text": (0.85, 0.95, 1.00, 1),
            "card": (0.05, 0.12, 0.25, 1),
        },
        "LAVA": {
            "bg":   (0.10, 0.02, 0.02, 1),
            "arc":  (1.00, 0.30, 0.10, 1),
            "text": (1.00, 0.85, 0.80, 1),
            "card": (0.18, 0.05, 0.05, 1),
        },
        "AMOLED": {
            "bg":   (0.00, 0.00, 0.00, 1),
            "arc":  (0.90, 0.90, 0.90, 1),
            "text": (0.95, 0.95, 0.95, 1),
            "card": (0.06, 0.06, 0.06, 1),
        },
        "PURPLE": {
            "bg":   (0.06, 0.02, 0.12, 1),
            "arc":  (0.67, 0.33, 1.00, 1),
            "text": (0.90, 0.80, 1.00, 1),
            "card": (0.12, 0.05, 0.20, 1),
        },
        "GOLD": {
            "bg":   (0.08, 0.06, 0.00, 1),
            "arc":  (1.00, 0.80, 0.10, 1),
            "text": (1.00, 0.92, 0.70, 1),
            "card": (0.15, 0.12, 0.02, 1),
        },
        "MINT": {
            "bg":   (0.02, 0.10, 0.08, 1),
            "arc":  (0.40, 1.00, 0.80, 1),
            "text": (0.85, 1.00, 0.95, 1),
            "card": (0.05, 0.16, 0.13, 1),
        },
    }

    def get(self, name: str) -> dict:
        return self.THEMES.get(name, self.THEMES["DARK"])

    def names(self):
        return list(self.THEMES.keys())
