from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

class RootWidget(BoxLayout):
    pass

class KingWatchApp(App):

    def build(self):
        Builder.load_file("kingwatch.kv")
        return RootWidget()

if __name__ == "__main__":
    KingWatchApp().run()