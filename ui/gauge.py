import io, math
from PIL import Image, ImageDraw, ImageFont

def draw_gauge(pct, size=110, fg=(0,230,118,255), bg=(40,40,40,255), thick=11):
    """
    Draw a 270-degree arc gauge using Pillow.
    Returns PNG bytes safe for Kivy CoreImage.
    """
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = thick + 6
    box = [pad, pad, size - pad, size - pad]

    # Background ring
    draw.arc(box, start=135, end=45, fill=bg, width=thick)

    # Foreground arc
    span = max(0.0, min(100.0, pct)) / 100.0 * 270.0
    if span > 1:
        draw.arc(box, start=135, end=135 + span, fill=fg, width=thick)

    # Tip dot
    if span > 1:
        ang = math.radians(135 + span)
        cx  = (box[0] + box[2]) / 2.0
        cy  = (box[1] + box[3]) / 2.0
        r   = (box[2] - box[0]) / 2.0
        tx  = cx + r * math.cos(ang)
        ty  = cy + r * math.sin(ang)
        d   = thick // 2 + 2
        draw.ellipse([tx-d, ty-d, tx+d, ty+d], fill=fg)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def pct_to_color(pct, lo=75, hi=90):
    """Return RGBA tuple: green < lo, orange lo-hi, red > hi."""
    if pct >= hi:  return (255, 23,  68,  255)
    if pct >= lo:  return (255, 145, 0,   255)
    return              (0,   230, 118, 255)
