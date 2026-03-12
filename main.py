from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

class RootWidget(BoxLayout):
    pass

class KingWatchApp(App):
    def build(self):
        return RootWidget()

if __name__ == "__main__":
    KingWatchApp().run()