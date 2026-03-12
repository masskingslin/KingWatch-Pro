from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.properties import StringProperty, NumericProperty
from kivy.graphics import Color, RoundedRectangle


class CircularGauge(BoxLayout):

    title = StringProperty("")
    value = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=10, padding=10, **kwargs)

        self.title_label = Label(
            text=self.title,
            font_size="18sp",
            size_hint=(1, None),
            height=40
        )

        self.bar = ProgressBar(
            max=100,
            value=self.value,
            size_hint=(1, None),
            height=20
        )

        self.value_label = Label(
            text=f"{self.value}%",
            font_size="16sp",
            size_hint=(1, None),
            height=30
        )

        self.add_widget(self.title_label)
        self.add_widget(self.bar)
        self.add_widget(self.value_label)

        self.bind(value=self.update_value)

    def update_value(self, instance, val):

        self.bar.value = val
        self.value_label.text = f"{val}%"


class InfoCard(BoxLayout):

    title = StringProperty("")
    value = StringProperty("--")

    def __init__(self, **kwargs):
        super().__init__(orientation="horizontal", padding=15, spacing=20, **kwargs)

        with self.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.bg = RoundedRectangle(radius=[12])

        self.bind(pos=self.update_bg, size=self.update_bg)

        self.title_label = Label(
            text=self.title,
            font_size="18sp"
        )

        self.value_label = Label(
            text=self.value,
            font_size="18sp"
        )

        self.add_widget(self.title_label)
        self.add_widget(self.value_label)

        self.bind(title=self.update_title)
        self.bind(value=self.update_value)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def update_title(self, instance, value):
        self.title_label.text = value

    def update_value(self, instance, value):
        self.value_label.text = value