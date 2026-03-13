THEMES = {
    'Hacker': {
        'BG':       '#0A0A0A',
        'CARD':     '#161616',
        'CARD2':    '#242424',
        'ACCENT':   '#00E676',
        'DIM':      '#555555',
        'DIV':      '#222222',
        'BTN_TEXT': '#000000',
        'WARN':     '#FFC107',
        'DANGER':   '#FF1744',
    },
    'Ocean': {
        'BG':       '#050F1A',
        'CARD':     '#0A1628',
        'CARD2':    '#112240',
        'ACCENT':   '#00B4D8',
        'DIM':      '#4A7FA5',
        'DIV':      '#1A3050',
        'BTN_TEXT': '#000000',
        'WARN':     '#FFC107',
        'DANGER':   '#FF1744',
    },
    'Ember': {
        'BG':       '#110800',
        'CARD':     '#1E0F00',
        'CARD2':    '#2E1800',
        'ACCENT':   '#FF6B00',
        'DIM':      '#7A4520',
        'DIV':      '#3D2000',
        'BTN_TEXT': '#000000',
        'WARN':     '#FFD700',
        'DANGER':   '#FF1744',
    },
    'Violet': {
        'BG':       '#0A0010',
        'CARD':     '#120020',
        'CARD2':    '#200038',
        'ACCENT':   '#9B59B6',
        'DIM':      '#5D3A7A',
        'DIV':      '#280050',
        'BTN_TEXT': '#FFFFFF',
        'WARN':     '#FFC107',
        'DANGER':   '#FF1744',
    },
    'Ice': {
        'BG':       '#0D1117',
        'CARD':     '#161B22',
        'CARD2':    '#21262D',
        'ACCENT':   '#58A6FF',
        'DIM':      '#484F58',
        'DIV':      '#30363D',
        'BTN_TEXT': '#000000',
        'WARN':     '#FFC107',
        'DANGER':   '#FF1744',
    },
}

THEME_NAMES   = list(THEMES.keys())
DEFAULT_THEME = 'Hacker'


def get_theme(name):
    return THEMES.get(name, THEMES[DEFAULT_THEME])
