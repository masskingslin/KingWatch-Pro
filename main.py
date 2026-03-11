from kivy.app import App
from kivy.lang import Builder
from ui.themes import ThemeManager

Builder.load_file("kingwatch.kv")


class KingWatchApp(App):

    def build(self):
        self.theme_manager = ThemeManager()
        self.theme_names = list(self.theme_manager.THEMES.keys())
        self.theme_index = 0
        self.theme_name = self.theme_names[0]
        self.theme = self.theme_manager.get(self.theme_name)
        return Builder.load_file("kingwatch.kv")

    def next_theme(self):
        self.theme_index = (self.theme_index + 1) % len(self.theme_names)
        self.theme_name = self.theme_names[self.theme_index]
        self.theme = self.theme_manager.get(self.theme_name)
        self.root.canvas.ask_update()


KingWatchApp().run()