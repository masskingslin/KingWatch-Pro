#:import CpuWidget ui.widgets.CpuWidget
#:import RamWidget ui.widgets.RamWidget
#:import StorageWidget ui.widgets.StorageWidget
#:import BatteryWidget ui.widgets.BatteryWidget
#:import NetworkWidget ui.widgets.NetworkWidget
#:import ThermalWidget ui.widgets.ThermalWidget


<StatCard>:
    orientation: "vertical"
    padding: 15
    spacing: 6
    size_hint_y: None
    height: 140

    canvas.before:
        Color:
            rgba: .12,.12,.14,1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [12]

    Label:
        text: root.title
        size_hint_y: None
        height: 20
        color: .7,.7,.7,1

    Label:
        text: root.value
        font_size: 32
        bold: True
        color: 0,1,0.6,1

    ProgressBar:
        value: root.percent
        max: 100

    Label:
        text: root.subtitle
        font_size: 12
        color: .6,.6,.6,1


BoxLayout:
    orientation: "vertical"
    padding: 10
    spacing: 10

    Label:
        text: "KingWatch Pro"
        font_size: 28
        size_hint_y: None
        height: 50
        bold: True
        color: 0,1,0.6,1

    ScrollView:

        BoxLayout:
            orientation: "vertical"
            spacing: 10
            size_hint_y: None
            height: self.minimum_height

            CpuWidget:
                id: cpu_card
                title: "CPU USAGE"

            RamWidget:
                id: ram_card
                title: "RAM"

            StorageWidget:
                id: storage_card
                title: "STORAGE"

            BatteryWidget:
                id: battery_card
                title: "BATTERY"

            NetworkWidget:
                id: network_card
                title: "NETWORK"

            ThermalWidget:
                id: thermal_card
                title: "THERMAL"