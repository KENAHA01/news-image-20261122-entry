#!/usr/bin/env python3
"""news-image-20261122 v4 - v3 layout with 3 fixes: redrawn lead scenes
(tanker reads as a ship, warship reads as a warship, COP31 clarified),
more breathing room (line spacing, DATE CHECK/footer air), fanned map pins.
Built fresh from the rank-1/2/3 reference layout.
Structure follows the top leaderboard entries (dark top bar, giant serif
masthead, number strip, region tabs, UTC strip, 3 illustrated leads,
10 illustrated medium cards, world map + 'also' list, red DATE CHECK box,
footer). Stories are OUR OWN verified 22 Nov 2026 research only.
Deterministic: no randomness, no network, no time dependence.
"""
from PIL import Image, ImageDraw, ImageFont
import hashlib

W, H = 1024, 1024
CREAM = (245, 241, 230)
PAPER = (250, 247, 238)
INK = (26, 26, 26)
NAVY = (27, 42, 74)
RED = (176, 30, 36)
DARKRED = (140, 20, 26)
GOLD = (212, 175, 105)
GREY = (110, 108, 100)
LIGHT = (235, 230, 216)

FB = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf"
SB = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SR = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
SI = "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf"
SS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SSB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def F(path, size):
    return ImageFont.truetype(path, size)

def tw(draw, text, font):
    return draw.textlength(text, font=font)

def wrap(draw, text, font, maxw):
    """Wrap text to lines fitting maxw pixels."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tw(draw, t, font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def fit_lines(draw, text, font, maxw, maxlines):
    """Wrap and clip to maxlines, adding ellipsis on the last line."""
    lines = wrap(draw, text, font, maxw)
    if len(lines) <= maxlines:
        return lines
    out = lines[:maxlines]
    while out and tw(draw, out[-1] + "...", font) > maxw:
        out[-1] = out[-1].rsplit(" ", 1)[0] if " " in out[-1] else out[-1][:-1]
    out[-1] = out[-1] + "..."
    return out

def draw_text_block(draw, x, y, lines, font, fill, lh):
    for i, ln in enumerate(lines):
        draw.text((x, y + i * lh), ln, font=font, fill=fill)
    return y + len(lines) * lh

# ---------------------------------------------------------------- region colors
REGION_COLORS = {
    "EUROPE": (46, 125, 123),
    "MIDDLE EAST": (176, 30, 36),
    "AMERICAS": (43, 95, 158),
    "ASIA-PACIFIC": (199, 126, 42),
    "AFRICA": (74, 122, 58),
    "OCEANIA": (106, 90, 158),
    "WORLD": (90, 90, 90),
}

def tag_chip(draw, x, y, text, fill, fg=(255, 255, 255), size=9):
    f = F(SSB, size)
    w = int(tw(draw, text, f)) + 10
    draw.rounded_rectangle([x, y, x + w, y + 13], radius=2, fill=fill)
    draw.text((x + 5, y + 1), text, font=f, fill=fg)
    return w

# ---------------------------------------------------------------- scene painters
def sky_band(d, box, top, bottom):
    """Simple vertical gradient sky between two RGB colors."""
    x0, y0, x1, y1 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
    for i in range(y1 - y0):
        t = i / max(1, (y1 - y0 - 1))
        c = tuple(int(top[j] + (bottom[j] - top[j]) * t) for j in range(3))
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c)

def flame(d, cx, base, s):
    """Big orange flame with flickering tongues."""
    d.polygon([(cx - 0.62 * s, base), (cx - 0.28 * s, base - 1.1 * s),
               (cx, base - 1.9 * s), (cx + 0.30 * s, base - 1.05 * s),
               (cx + 0.62 * s, base)], fill=(235, 90, 20))
    d.polygon([(cx - 0.40 * s, base), (cx - 0.15 * s, base - 0.9 * s),
               (cx, base - 1.35 * s), (cx + 0.18 * s, base - 0.85 * s),
               (cx + 0.40 * s, base)], fill=(255, 160, 40))
    d.polygon([(cx - 0.22 * s, base), (cx, base - 0.85 * s), (cx + 0.22 * s, base)],
              fill=(255, 220, 110))
    d.polygon([(cx - 0.95 * s, base), (cx - 0.70 * s, base - 0.7 * s),
               (cx - 0.45 * s, base)], fill=(255, 140, 40))
    d.polygon([(cx + 0.45 * s, base), (cx + 0.70 * s, base - 0.7 * s),
               (cx + 0.95 * s, base)], fill=(255, 140, 40))

def smoke(d, cx, cy, r, col=(70, 70, 75)):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    d.ellipse([cx - r * 0.7, cy - r * 1.5, cx + r * 0.7, cy - r * 0.1], fill=col)
    d.ellipse([cx - r * 0.5, cy - r * 2.0, cx + r * 0.5, cy - r * 0.6],
              fill=(95, 95, 100))

def smoke_big(d, cx, cy, r):
    """Tall smoke plume: stacked puffs rising and drifting left."""
    for i, (ox, oy, rr) in enumerate([(0, 0, 1.0), (-0.3, -1.2, 0.85),
                                      (-0.7, -2.2, 0.7), (-1.1, -3.1, 0.55)]):
        col = (60 + i * 12, 60 + i * 12, 66 + i * 12)
        d.ellipse([cx + ox * r - rr * r, cy + oy * r - rr * r,
                   cx + ox * r + rr * r, cy + oy * r + rr * r], fill=col)

def draw_cop31(d, x, y, w, h):
    sky_band(d, (x, y, x + w, y + h), (236, 220, 186), (214, 188, 140))
    # back wall + floor
    d.rectangle([x, y + h * 0.58, x + w, y + h * 0.66], fill=(150, 112, 70))
    d.rectangle([x, y + h * 0.66, x + w, y + h], fill=(118, 84, 50))
    # 6 big flags on poles (fewer, wider, clearly readable)
    flag_cols = [(0, 90, 160), (200, 30, 40), (0, 130, 80),
                 (240, 200, 40), (230, 120, 30), (140, 60, 160)]
    fw = (w - 24) / 6
    for i in range(6):
        fx = x + 12 + i * fw
        d.line([(fx + fw / 2, y + 18), (fx + fw / 2, y + h * 0.56)],
               fill=(70, 52, 32), width=2)
        d.rectangle([fx + 2, y + 18, fx + fw - 2, y + 38], fill=flag_cols[i],
                    outline=(120, 100, 70))
    # long table with green cloth runner
    d.rectangle([x + 8, y + h * 0.70, x + w - 8, y + h * 0.94], fill=(96, 64, 38))
    d.rectangle([x + 8, y + h * 0.70, x + w - 8, y + h * 0.75], fill=(160, 112, 64))
    d.rectangle([x + w * 0.32, y + h * 0.70, x + w * 0.68, y + h * 0.94],
                fill=(30, 110, 70))
    # 4 delegates, bigger heads, clear of the podium
    suits = [(35, 45, 70), (90, 40, 45), (40, 70, 55), (70, 60, 90)]
    skins = [(215, 175, 135), (190, 150, 115), (225, 190, 155), (200, 160, 125)]
    for i, dx in enumerate([0.10, 0.28, 0.72, 0.90]):
        cx = x + w * dx
        d.rounded_rectangle([cx - 17, y + h * 0.62, cx + 17, y + h * 0.72],
                            radius=6, fill=suits[i])
        d.ellipse([cx - 9, y + h * 0.48, cx + 9, y + h * 0.48 + 18], fill=skins[i])
        d.pieslice([cx - 9, y + h * 0.48, cx + 9, y + h * 0.48 + 11], 180, 360,
                   fill=(50, 40, 32))
        d.rectangle([cx - 12, y + h * 0.75, cx + 12, y + h * 0.75 + 8],
                    fill=(245, 242, 230))
    # podium front centre with globe + COP31 label
    d.rectangle([x + w * 0.42, y + h * 0.76, x + w * 0.58, y + h], fill=(70, 48, 30))
    d.ellipse([x + w * 0.44, y + h * 0.60, x + w * 0.56, y + h * 0.76],
              fill=(55, 130, 95))
    d.ellipse([x + w * 0.465, y + h * 0.625, x + w * 0.535, y + h * 0.735],
              fill=(130, 195, 155))
    t = "COP31"
    f = F(SSB, 10)
    d.text((x + w * 0.50 - tw(d, t, f) / 2, y + h * 0.84), t, font=f,
           fill=(255, 255, 255))

def draw_tankers(d, x, y, w, h):
    sky_band(d, (x, y, x + w, y + h * 0.52), (14, 22, 50), (64, 50, 90))
    # stars + small moon (tops sit under the red label bar, as in v3)
    for sx, sy in [(0.10, 0.12), (0.28, 0.07), (0.52, 0.16), (0.72, 0.08), (0.95, 0.20)]:
        d.ellipse([x + w * sx - 1, y + h * sy - 1, x + w * sx + 1, y + h * sy + 1],
                  fill=(255, 255, 220))
    d.ellipse([x + w * 0.90, y + 4, x + w * 0.90 + 13, y + 17], fill=(240, 230, 200))
    # sea
    sea_y = y + h * 0.52
    d.rectangle([x, sea_y, x + w, y + h], fill=(16, 38, 68))
    for i in range(5):
        yy = sea_y + 8 + i * 9
        for wx in range(0, int(w), 46):
            d.arc([x + wx, yy - 4, x + wx + 22, yy + 4], 180, 360, fill=(90, 140, 180))
    # ---- tanker 1: big, bow left, burning amidships ----
    # no big orange glow (that read as an orange hill); the flame is the fire
    hx, hy, hw = x + w * 0.04, sea_y - 14, w * 0.52
    # hull: raked stem bow, flat deck, slanted bottom corners, dark outline
    d.polygon([(hx, hy + 22), (hx + 6, hy + 6), (hx + hw, hy + 6),
               (hx + hw - 8, hy + 30), (hx + 10, hy + 30)],
              fill=(28, 28, 34), outline=(8, 8, 10))
    # white sheer stripe along the deck edge + red waterline stripe
    d.rectangle([hx + 6, hy + 6, hx + hw, hy + 9], fill=(225, 225, 228))
    d.rectangle([hx + 8, hy + 26, hx + hw - 8, hy + 29], fill=(150, 30, 30))
    # 3 cylindrical deck tanks with rounded tops + highlight
    for i in range(3):
        tx = hx + hw * (0.10 + i * 0.15)
        tw_ = hw * 0.11
        d.rectangle([tx, hy - 8, tx + tw_, hy + 6], fill=(165, 165, 170))
        d.ellipse([tx, hy - 12, tx + tw_, hy - 4], fill=(190, 190, 195))
        d.rectangle([tx + 2, hy - 8, tx + 4, hy + 6], fill=(210, 210, 215))
    # white superstructure at the stern with two window rows
    sx0 = hx + hw * 0.78
    d.rectangle([sx0, hy - 22, sx0 + hw * 0.16, hy + 6], fill=(235, 235, 230))
    for r in range(2):
        for c in range(3):
            d.rectangle([sx0 + 4 + c * 9, hy - 18 + r * 8,
                         sx0 + 4 + c * 9 + 5, hy - 18 + r * 8 + 4],
                        fill=(30, 60, 90))
    # funnel with black top + thin smoke (smoke kept below the label bar)
    d.rectangle([sx0 + hw * 0.17, hy - 18, sx0 + hw * 0.17 + 9, hy + 6],
                fill=(180, 50, 40))
    d.rectangle([sx0 + hw * 0.17, hy - 18, sx0 + hw * 0.17 + 9, hy - 14],
                fill=(25, 25, 28))
    smoke(d, sx0 + hw * 0.17 + 5, hy - 16, 5)
    # modest flame ON the deck amidships + thin smoke + orange reflection
    flame(d, hx + hw * 0.60, hy + 6, 13)
    smoke_big(d, hx + hw * 0.60, hy - 2, 7)
    for rx in (0.56, 0.60, 0.64):
        d.line([(hx + hw * rx, sea_y + 34), (hx + hw * (rx + 0.04), sea_y + 34)],
               fill=(230, 130, 50), width=2)
    # ---- tanker 2: smaller, bow right ----
    hx2, hy2, hw2 = x + w * 0.62, sea_y - 10, w * 0.32
    d.polygon([(hx2 + hw2, hy2 + 18), (hx2 + hw2 - 6, hy2 + 5), (hx2, hy2 + 5),
               (hx2 + 8, hy2 + 26), (hx2 + hw2 - 10, hy2 + 26)],
              fill=(42, 42, 50), outline=(10, 10, 12))
    d.rectangle([hx2, hy2 + 5, hx2 + hw2 - 6, hy2 + 8], fill=(225, 225, 228))
    d.rectangle([hx2 + 8, hy2 + 22, hx2 + hw2 - 8, hy2 + 25], fill=(150, 30, 30))
    for i in range(2):
        tx = hx2 + hw2 * (0.28 + i * 0.18)
        tw_ = hw2 * 0.13
        d.rectangle([tx, hy2 - 6, tx + tw_, hy2 + 5], fill=(165, 165, 170))
        d.ellipse([tx, hy2 - 10, tx + tw_, hy2 - 3], fill=(190, 190, 195))
    sx0 = hx2
    d.rectangle([sx0, hy2 - 16, sx0 + hw2 * 0.14, hy2 + 5], fill=(235, 235, 230))
    for r in range(2):
        d.rectangle([sx0 + 3, hy2 - 13 + r * 6, sx0 + 3 + 8, hy2 - 13 + r * 6 + 3],
                    fill=(30, 60, 90))
    flame(d, hx2 + hw2 * 0.62, hy2 + 5, 10)
    smoke_big(d, hx2 + hw2 * 0.62, hy2 - 2, 6)

def draw_merkury(d, x, y, w, h):
    sky_band(d, (x, y, x + w, y + h * 0.5), (250, 195, 125), (225, 145, 90))
    d.ellipse([x + w * 0.86, y + 20, x + w * 0.86 + 16, y + 36], fill=(255, 240, 200))
    # sea with whitecaps
    sea_y = y + h * 0.5
    d.rectangle([x, sea_y, x + w, y + h], fill=(38, 68, 92))
    for i in range(4):
        yy = sea_y + 10 + i * 10
        for wx in range(0, int(w), 52):
            d.arc([x + wx, yy - 4, x + wx + 24, yy + 4], 180, 360, fill=(115, 155, 185))
    # warship listing to starboard: bow low left dipping into the sea,
    # stern high right, burning at the stern
    hx, hy = x + w * 0.06, y + h * 0.52
    hw = w * 0.80
    bow_x, bow_y = hx, hy + 6
    stern_x, stern_y = hx + hw, hy - 14
    # hull: pointed bow, deck sloping up to the raised stern, dark outline
    d.polygon([(bow_x, bow_y), (stern_x, stern_y),
               (stern_x - 10, stern_y + 22), (bow_x + 18, bow_y + 20)],
              fill=(88, 98, 110), outline=(40, 46, 56))
    # pale deck-edge stripe following the slope + white waterline stripe
    d.line([(bow_x + 2, bow_y - 1), (stern_x - 2, stern_y - 1)],
           fill=(215, 220, 228), width=2)
    d.line([(bow_x + 10, bow_y + 15), (stern_x - 12, stern_y + 16)],
           fill=(235, 235, 240), width=2)
    # portholes along the hull (breaks the flat-slab look)
    for i in range(6):
        t = 0.12 + i * 0.14
        px = bow_x + t * hw
        py = bow_y + (stern_y - bow_y) * t + 10
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(30, 38, 48))
    # bridge tower with windows (midship)
    bx = hx + hw * 0.46
    d.rectangle([bx, hy - 30, bx + 34, hy + 2], fill=(98, 106, 118))
    for i in range(3):
        d.rectangle([bx + 5 + i * 10, hy - 26, bx + 5 + i * 10 + 6, hy - 16],
                    fill=(200, 220, 235))
    # mast with crossbar (kept below the red label bar)
    mx = bx + 17
    d.line([(mx, hy - 30), (mx, hy - 42)], fill=(60, 66, 76), width=2)
    d.line([(mx - 9, hy - 38), (mx + 9, hy - 38)], fill=(60, 66, 76), width=2)
    # funnel with smoke
    fx = hx + hw * 0.66
    d.rectangle([fx, hy - 22, fx + 12, hy + 2], fill=(70, 74, 82))
    smoke(d, fx + 6, hy - 26, 5)
    # gun turret forward with a long barrel angled up-forward
    gx = hx + hw * 0.16
    d.ellipse([gx - 10, hy - 8, gx + 12, hy + 8], fill=(58, 64, 74))
    d.line([(gx + 8, hy - 2), (gx + 34, hy - 24)], fill=(58, 64, 74), width=4)
    # fire + smoke at the raised stern (smoke kept below the label bar)
    flame(d, stern_x - 8, stern_y + 2, 11)
    smoke_big(d, stern_x - 8, stern_y - 2, 7)
    # foam + spray where the bow dips under
    for wx in range(0, 40, 12):
        d.arc([bow_x - 14 + wx, bow_y + 8, bow_x + 6 + wx, bow_y + 16], 180, 360,
              fill=(235, 242, 248))
    d.ellipse([bow_x - 6, bow_y + 2, bow_x + 10, bow_y + 10], fill=(225, 235, 242))
    # sea drone bottom right
    d.ellipse([x + w * 0.85, y + h * 0.80, x + w * 0.85 + 22, y + h * 0.80 + 8],
              fill=(30, 30, 36))
    d.line([(x + w * 0.85, y + h * 0.84), (x + w * 0.85 + 22, y + h * 0.84)],
           fill=(90, 90, 95), width=1)

def draw_capitol(d, x, y, w, h):
    sky_band(d, (x, y, x + w, y + h), (205, 218, 238), (175, 195, 218))
    # capitol building on the LEFT half
    bx0, bw = x + w * 0.04, w * 0.48
    d.rectangle([bx0, y + h * 0.62, bx0 + bw, y + h * 0.92], fill=(242, 240, 232))
    d.rectangle([bx0, y + h * 0.62, bx0 + bw, y + h * 0.68], fill=(205, 203, 192))
    for i in range(4):
        cx = bx0 + bw * (0.12 + i * 0.24)
        d.rectangle([cx, y + h * 0.70, cx + 5, y + h * 0.90], fill=(192, 190, 180))
    d.pieslice([bx0 + bw * 0.22, y + h * 0.26, bx0 + bw * 0.78, y + h * 0.68],
               180, 360, fill=(238, 236, 227))
    d.rectangle([bx0 + bw * 0.44, y + h * 0.20, bx0 + bw * 0.56, y + h * 0.28],
                fill=(238, 236, 227))
    # seat chart on a clean white panel, RIGHT half, clear of the building
    px0, py0, pw, ph = x + w * 0.56, y + h * 0.06, w * 0.40, h * 0.88
    d.rectangle([px0, py0, px0 + pw, py0 + ph], fill=(255, 255, 255),
                outline=(180, 180, 175))
    d.text((px0 + 6, py0 + 2), "HOUSE SEATS", font=F(SSB, 8), fill=(90, 90, 90))
    by1 = py0 + 13
    d.rectangle([px0 + 6, by1, px0 + 6 + pw * 0.60, by1 + 7], fill=(43, 95, 158))
    d.text((px0 + 6, by1 + 9), "Dem 258", font=F(SSB, 8), fill=(43, 95, 158))
    by2 = py0 + 31
    d.rectangle([px0 + 6, by2, px0 + 6 + pw * 0.60 * 0.686, by2 + 7],
                fill=(176, 30, 36))
    d.text((px0 + 6, by2 + 9), "Rep 177", font=F(SSB, 8), fill=(176, 30, 36))

def draw_dymer(d, x, y, w, h):
    sky_band(d, (x, y, x + w, y + h), (28, 32, 58), (75, 75, 95))
    # standing left part of the block, lit windows (some dark / broken)
    d.rectangle([x + w * 0.08, y + h * 0.22, x + w * 0.48, y + h * 0.92],
                fill=(150, 145, 135))
    for r in range(3):
        for c in range(2):
            wx = x + w * (0.13 + c * 0.16)
            wy = y + h * (0.30 + r * 0.20)
            d.rectangle([wx, wy, wx + 11, wy + 10],
                        fill=(240, 220, 130) if (r + c) % 2 else (60, 60, 66))
    # collapsed right part: tilted slab with a jagged break edge
    d.polygon([(x + w * 0.48, y + h * 0.22), (x + w * 0.60, y + h * 0.34),
               (x + w * 0.78, y + h * 0.55), (x + w * 0.86, y + h * 0.92),
               (x + w * 0.48, y + h * 0.92)], fill=(112, 107, 100))
    d.polygon([(x + w * 0.48, y + h * 0.22), (x + w * 0.54, y + h * 0.32),
               (x + w * 0.50, y + h * 0.42), (x + w * 0.57, y + h * 0.52),
               (x + w * 0.52, y + h * 0.62), (x + w * 0.48, y + h * 0.70)],
              fill=(85, 80, 75))
    # broken windows on the slab
    d.rectangle([x + w * 0.62, y + h * 0.45, x + w * 0.62 + 9, y + h * 0.45 + 8],
                fill=(50, 50, 55))
    d.rectangle([x + w * 0.70, y + h * 0.60, x + w * 0.70 + 9, y + h * 0.60 + 8],
                fill=(50, 50, 55))
    # rubble pile at the base
    d.polygon([(x + w * 0.45, y + h * 0.92), (x + w * 0.60, y + h * 0.78),
               (x + w * 0.75, y + h * 0.86), (x + w * 0.88, y + h * 0.92)],
              fill=(130, 125, 118))
    d.polygon([(x + w * 0.55, y + h * 0.92), (x + w * 0.63, y + h * 0.84),
               (x + w * 0.72, y + h * 0.92)], fill=(95, 90, 85))
    # dust cloud at the break
    smoke(d, x + w * 0.52, y + h * 0.30, 8, col=(150, 148, 140))
    # drone silhouette top right
    d.ellipse([x + w * 0.80, y + h * 0.10, x + w * 0.80 + 14, y + h * 0.10 + 5],
              fill=(20, 20, 26))
    d.line([(x + w * 0.78, y + h * 0.12), (x + w * 0.96, y + h * 0.12)],
           fill=(20, 20, 26), width=2)

def draw_khartoum(d, x, y, w, h):
    sky_band(d, (x, y, x + w, y + h), (240, 220, 180), (210, 180, 130))
    # UN building
    d.rectangle([x + w * 0.12, y + h * 0.35, x + w * 0.55, y + h * 0.95], fill=(235, 235, 225))
    for r in range(3):
        for c in range(4):
            d.rectangle([x + w * (0.16 + c * 0.10), y + h * (0.42 + r * 0.17),
                         x + w * (0.16 + c * 0.10) + 8, y + h * (0.42 + r * 0.17) + 8],
                        fill=(90, 120, 160))
    d.text((x + w * 0.16, y + h * 0.60), "UN", font=F(SSB, 11), fill=(43, 95, 158))
    # damaged corner + smoke
    d.polygon([(x + w * 0.55, y + h * 0.35), (x + w * 0.72, y + h * 0.5),
               (x + w * 0.72, y + h * 0.95), (x + w * 0.55, y + h * 0.95)],
              fill=(120, 115, 105))
    smoke(d, x + w * 0.62, y + h * 0.32, 9)
    # palm
    d.line([(x + w * 0.86, y + h * 0.95), (x + w * 0.86, y + h * 0.55)], fill=(90, 70, 40), width=3)
    for a in range(5):
        d.arc([x + w * 0.78, y + h * 0.42, x + w * 0.94, y + h * 0.62],
              200 + a * 25, 250 + a * 25, fill=(60, 120, 60))

def draw_rabigh(d, x, y, w, h):
    sky_band(d, (x, y, x + w, y + h), (250, 200, 130), (230, 150, 90))
    # refinery towers
    for i, tw_ in enumerate([0.14, 0.30, 0.48]):
        d.rectangle([x + w * tw_, y + h * (0.45 - i * 0.08), x + w * (tw_ + 0.12),
                     y + h * 0.95], fill=(140, 140, 145))
        d.rectangle([x + w * tw_, y + h * (0.45 - i * 0.08), x + w * (tw_ + 0.12),
                     y + h * (0.45 - i * 0.08) + 6], fill=(90, 90, 95))
    # flare stack + flame
    d.rectangle([x + w * 0.68, y + h * 0.25, x + w * 0.72, y + h * 0.95], fill=(110, 110, 115))
    flame(d, x + w * 0.70, y + h * 0.25, 10)
    smoke(d, x + w * 0.70, y + h * 0.12, 7)
    # pipes
    d.line([(x + w * 0.1, y + h * 0.8), (x + w * 0.9, y + h * 0.8)], fill=(90, 90, 95), width=3)

def draw_missile(d, x, y, w, h):
    # mountains behind
    sky_band(d, (x, y, x + w, y + h), (70, 70, 85), (40, 40, 55))
    d.polygon([(x, y + h), (x + w * 0.30, y + h * 0.25), (x + w * 0.55, y + h)],
              fill=(55, 55, 70))
    d.polygon([(x + w * 0.35, y + h), (x + w * 0.65, y + h * 0.15),
               (x + w * 0.95, y + h)], fill=(48, 48, 62))
    # ground
    d.rectangle([x, y + h * 0.72, x + w, y + h], fill=(35, 40, 30))
    # tunnel mouth (right) with warm glow inside
    d.ellipse([x + w * 0.70, y + h * 0.42, x + w * 0.98, y + h * 0.95],
              fill=(15, 15, 18))
    d.ellipse([x + w * 0.75, y + h * 0.55, x + w * 0.93, y + h * 0.95],
              fill=(255, 170, 60))
    d.ellipse([x + w * 0.78, y + h * 0.62, x + w * 0.90, y + h * 0.95],
              fill=(120, 70, 30))
    # launcher truck: cab + bed + wheels
    d.rectangle([x + w * 0.06, y + h * 0.66, x + w * 0.52, y + h * 0.84],
                fill=(74, 92, 62))
    d.rectangle([x + w * 0.06, y + h * 0.58, x + w * 0.18, y + h * 0.66],
                fill=(90, 108, 76))
    d.rectangle([x + w * 0.08, y + h * 0.60, x + w * 0.15, y + h * 0.66],
                fill=(180, 210, 225))
    for wx in (0.14, 0.30, 0.44):
        d.ellipse([x + w * wx, y + h * 0.80, x + w * wx + 10, y + h * 0.80 + 10],
                  fill=(18, 18, 20))
        d.ellipse([x + w * wx + 3, y + h * 0.80 + 3, x + w * wx + 7, y + h * 0.80 + 7],
                  fill=(120, 120, 125))
    # missile on an angled erector arm
    d.line([(x + w * 0.24, y + h * 0.66), (x + w * 0.42, y + h * 0.14)],
           fill=(120, 120, 125), width=3)
    d.line([(x + w * 0.30, y + h * 0.62), (x + w * 0.48, y + h * 0.12)],
           fill=(205, 205, 210), width=9)
    d.polygon([(x + w * 0.48, y + h * 0.12), (x + w * 0.44, y + h * 0.24),
               (x + w * 0.52, y + h * 0.24)], fill=(220, 60, 50))
    d.polygon([(x + w * 0.28, y + h * 0.66), (x + w * 0.24, y + h * 0.74),
               (x + w * 0.32, y + h * 0.74)], fill=(200, 60, 50))
    # second missile lying on a ground rack
    d.line([(x + w * 0.56, y + h * 0.80), (x + w * 0.68, y + h * 0.80)],
           fill=(180, 180, 185), width=6)
    d.polygon([(x + w * 0.68, y + h * 0.80), (x + w * 0.63, y + h * 0.75),
               (x + w * 0.63, y + h * 0.85)], fill=(220, 60, 50))

def draw_banten(d, x, y, w, h):
    sky_band(d, (x, y, x + w, y + h), (200, 210, 220), (165, 175, 185))
    # factory hall with sawtooth roof
    d.rectangle([x + w * 0.10, y + h * 0.42, x + w * 0.90, y + h * 0.90],
                fill=(170, 160, 145))
    d.polygon([(x + w * 0.10, y + h * 0.42), (x + w * 0.30, y + h * 0.28),
               (x + w * 0.50, y + h * 0.42), (x + w * 0.70, y + h * 0.28),
               (x + w * 0.90, y + h * 0.42)], fill=(120, 112, 102))
    # windows with a crossbar
    for i in range(4):
        wx = x + w * (0.16 + i * 0.19)
        d.rectangle([wx, y + h * 0.55, wx + 13, y + h * 0.55 + 15],
                    fill=(70, 75, 85))
        d.line([(wx, y + h * 0.625), (wx + 13, y + h * 0.625)],
               fill=(150, 155, 160), width=1)
    # chimney + thin smoke wisp
    d.rectangle([x + w * 0.84, y + h * 0.26, x + w * 0.90, y + h * 0.42],
                fill=(140, 100, 80))
    d.rectangle([x + w * 0.83, y + h * 0.24, x + w * 0.91, y + h * 0.28],
                fill=(110, 80, 65))
    d.ellipse([x + w * 0.845, y + h * 0.30, x + w * 0.845 + 8, y + h * 0.30 + 5],
              fill=(190, 190, 195))
    d.ellipse([x + w * 0.86, y + h * 0.22, x + w * 0.86 + 7, y + h * 0.22 + 5],
              fill=(200, 200, 205))
    # fence at the front
    for i in range(9):
        fx = x + w * (0.10 + i * 0.09)
        d.line([(fx, y + h * 0.90), (fx, y + h * 0.78)], fill=(90, 85, 75), width=2)
    d.line([(x + w * 0.08, y + h * 0.82), (x + w * 0.92, y + h * 0.82)],
           fill=(90, 85, 75), width=2)
    # body bags row on the ground in front of the fence
    for i in range(3):
        d.rounded_rectangle([x + w * (0.16 + i * 0.26), y + h * 0.86,
                             x + w * (0.16 + i * 0.26) + 28, y + h * 0.86 + 6],
                            radius=3, fill=(245, 245, 240))

def draw_tennis(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(70, 130, 90))
    d.rectangle([x + w * 0.12, y + h * 0.15, x + w * 0.88, y + h * 0.85], fill=(110, 170, 130))
    d.line([(x + w * 0.5, y + h * 0.15), (x + w * 0.5, y + h * 0.85)], fill=(255, 255, 255), width=2)
    d.line([(x + w * 0.12, y + h * 0.5), (x + w * 0.88, y + h * 0.5)], fill=(255, 255, 255), width=2)
    d.line([(x + w * 0.12, y + h * 0.15), (x + w * 0.88, y + h * 0.15)], fill=(255, 255, 255), width=2)
    d.line([(x + w * 0.12, y + h * 0.85), (x + w * 0.88, y + h * 0.85)], fill=(255, 255, 255), width=2)
    d.ellipse([x + w * 0.62, y + h * 0.30, x + w * 0.62 + 9, y + h * 0.30 + 9],
              fill=(220, 240, 60))

def draw_f1_car(d, x, y, w, col):
    """Side view of a Formula 1 car: long low body, cockpit, rear wing, wheels."""
    d.polygon([(x, y + 8), (x + w * 0.18, y + 2), (x + w * 0.75, y + 2),
               (x + w, y + 7), (x + w, y + 11), (x, y + 11)], fill=col)
    d.polygon([(x + w * 0.38, y + 2), (x + w * 0.44, y - 5), (x + w * 0.56, y - 5),
               (x + w * 0.62, y + 2)], fill=(30, 30, 35))
    d.ellipse([x + w * 0.46, y - 6, x + w * 0.54, y + 1], fill=(255, 255, 255))
    # rear wing
    d.rectangle([x, y - 4, x + 4, y + 8], fill=(25, 25, 30))
    d.rectangle([x - 2, y - 6, x + 8, y - 3], fill=(25, 25, 30))
    # front wing
    d.rectangle([x + w - 6, y + 6, x + w + 2, y + 11], fill=(25, 25, 30))
    # wheels
    for wx in (0.18, 0.72):
        d.ellipse([x + w * wx, y + 9, x + w * wx + 13, y + 22], fill=(12, 12, 14))
        d.ellipse([x + w * wx + 4, y + 13, x + w * wx + 9, y + 18],
                  fill=(150, 150, 155))

def draw_race(d, x, y, w, h):
    sky_band(d, (x, y, x + w, y + h * 0.5), (18, 18, 38), (60, 42, 82))
    # city lights
    for i, cc in enumerate([(255, 200, 80), (255, 120, 120), (120, 200, 255),
                            (255, 220, 140), (255, 160, 90)]):
        bx = x + w * (0.06 + i * 0.18)
        d.rectangle([bx, y + h * (0.32 - (i % 2) * 0.06), bx + 12, y + h * 0.5],
                    fill=cc)
    # track
    d.rectangle([x, y + h * 0.5, x + w, y + h], fill=(38, 38, 44))
    # red-white curb at the top edge of the track
    for i in range(10):
        d.rectangle([x + i * (w / 10), y + h * 0.5, x + (i + 1) * (w / 10),
                     y + h * 0.56],
                    fill=(220, 40, 40) if i % 2 == 0 else (245, 245, 245))
    # dashed centre line
    for i in range(6):
        d.rectangle([x + 8 + i * 32, y + h * 0.78, x + 8 + i * 32 + 18,
                     y + h * 0.78 + 2], fill=(240, 240, 230))
    # two race cars, side by side
    draw_f1_car(d, x + w * 0.10, y + h * 0.60, 62, (20, 80, 200))
    draw_f1_car(d, x + w * 0.52, y + h * 0.60, 62, (200, 40, 40))

def draw_patriot(d, x, y, w, h):
    sky_band(d, (x, y, x + w, y + h), (200, 215, 235), (160, 180, 205))
    # radar + launcher
    d.rectangle([x + w * 0.12, y + h * 0.70, x + w * 0.45, y + h * 0.88], fill=(90, 100, 85))
    d.ellipse([x + w * 0.16, y + h * 0.84, x + w * 0.16 + 10, y + h * 0.84 + 10], fill=(20, 20, 22))
    d.ellipse([x + w * 0.36, y + h * 0.84, x + w * 0.36 + 10, y + h * 0.84 + 10], fill=(20, 20, 22))
    # missile up
    d.line([(x + w * 0.28, y + h * 0.70), (x + w * 0.28, y + h * 0.22)], fill=(210, 210, 215), width=8)
    d.polygon([(x + w * 0.28, y + h * 0.22), (x + w * 0.24, y + h * 0.34),
               (x + w * 0.32, y + h * 0.34)], fill=(200, 50, 45))
    # radar dish
    d.pieslice([x + w * 0.64, y + h * 0.42, x + w * 0.86, y + h * 0.68], 180, 360,
               fill=(220, 220, 225))
    d.line([(x + w * 0.75, y + h * 0.55), (x + w * 0.75, y + h * 0.85)], fill=(100, 100, 105), width=3)
    # sky dots (drones)
    for sx, sy in [(0.55, 0.15), (0.68, 0.08), (0.85, 0.2)]:
        d.ellipse([x + w * sx - 2, y + h * sy - 1, x + w * sx + 2, y + h * sy + 1],
                  fill=(40, 40, 45))

def draw_ballot(d, x, y, w, h):
    sky_band(d, (x, y, x + w, y + h), (240, 235, 220), (215, 205, 185))
    # ballot box
    d.rectangle([x + w * 0.18, y + h * 0.45, x + w * 0.82, y + h * 0.92], fill=(176, 30, 36))
    d.rectangle([x + w * 0.14, y + h * 0.38, x + w * 0.86, y + h * 0.48], fill=(140, 22, 28))
    d.line([(x + w * 0.44, y + h * 0.40), (x + w * 0.56, y + h * 0.40)], fill=(250, 250, 245), width=3)
    # "99%" label centred on the red box front (clear of lid and check box)
    t99 = "99%"
    f99 = F(SSB, 16)
    d.text((x + w * 0.50 - tw(d, t99, f99) / 2, y + h * 0.62), t99, font=f99,
           fill=(255, 255, 255))
    d.rectangle([x + w * 0.66, y + h * 0.22, x + w * 0.84, y + h * 0.58], fill=(255, 255, 255))
    d.line([(x + w * 0.69, y + h * 0.42), (x + w * 0.73, y + h * 0.48), (x + w * 0.80, y + h * 0.32)],
           fill=(30, 140, 60), width=3)

# ---------------------------------------------------------------- world map
# Rough continent polygons in lon/lat, projected into the map box.
CONTINENTS = [
    # North America (Alaska, Hudson Bay notch, Florida, Central America)
    [(-168, 66), (-165, 60), (-158, 58), (-152, 60), (-140, 60), (-135, 58),
     (-130, 54), (-125, 49), (-124, 42), (-120, 34), (-114, 29), (-110, 24),
     (-105, 20), (-97, 16), (-94, 17), (-90, 14), (-86, 12), (-83, 9),
     (-80, 8), (-77, 7), (-79, 9), (-82, 10), (-84, 13), (-88, 15),
     (-90, 21), (-91, 19), (-87, 21), (-86, 16), (-84, 30), (-81, 25),
     (-80, 32), (-76, 35), (-74, 40), (-70, 42), (-68, 44), (-65, 44),
     (-60, 47), (-55, 47), (-53, 49), (-56, 52), (-60, 55), (-65, 60),
     (-70, 62), (-78, 62), (-85, 66), (-90, 66), (-95, 69), (-110, 68),
     (-125, 70), (-140, 70), (-155, 71), (-165, 68), (-168, 66)],
    # Greenland
    [(-58, 64), (-45, 60), (-40, 64), (-32, 68), (-22, 70), (-25, 76),
     (-35, 80), (-55, 80), (-60, 76), (-58, 70), (-58, 64)],
    # South America (wide north, tapering south)
    [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
     (-70, -23), (-70, -30), (-72, -37), (-73, -44), (-70, -52), (-66, -55),
     (-68, -50), (-65, -45), (-62, -41), (-58, -34), (-52, -32), (-48, -28),
     (-41, -23), (-39, -17), (-35, -9), (-35, -6), (-40, -3), (-44, 0),
     (-50, 0), (-54, 4), (-60, 8), (-70, 11), (-75, 10), (-79, 9)],
    # Europe (Scandinavia up, Iberia, Italy boot, Greece)
    [(-10, 36), (-9, 38), (-9, 43), (-4, 48), (-1, 50), (3, 51), (6, 54),
     (8, 57), (5, 58), (5, 60), (10, 62), (14, 67), (18, 70), (25, 71),
     (30, 70), (32, 68), (33, 64), (32, 60), (33, 56), (35, 52), (37, 48),
     (40, 45), (38, 43), (33, 42), (30, 41), (27, 37), (23, 36), (26, 40),
     (23, 40), (19, 42), (15, 45), (12, 44), (8, 44), (3, 43), (-1, 38),
     (-6, 36), (-10, 36)],
    # United Kingdom
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (-2, 51),
     (-5, 50)],
    # Ireland
    [(-10, 52), (-8, 51), (-6, 52), (-6, 55), (-8, 55), (-10, 54), (-10, 52)],
    # Africa (west bulge, Horn, southern taper)
    [(-6, 35), (-10, 31), (-15, 27), (-17, 21), (-17, 15), (-15, 11),
     (-11, 8), (-8, 5), (-4, 5), (0, 6), (6, 4), (9, 4), (9, 0), (12, -4),
     (13, -10), (12, -17), (14, -22), (16, -28), (18, -34), (20, -35),
     (26, -34), (32, -29), (35, -25), (36, -20), (40, -15), (40, -10),
     (42, -4), (46, -1), (51, 2), (51, 11), (48, 11), (44, 11), (43, 12),
     (40, 15), (38, 18), (37, 22), (35, 28), (34, 31), (32, 31), (25, 32),
     (19, 33), (11, 34), (10, 37), (-6, 35)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (49, -20), (46, -25), (43, -22),
     (44, -16)],
    # Asia (Siberia, Kamchatka, India, SE Asia, Arabia, Anatolia)
    [(28, 71), (35, 68), (40, 68), (45, 68), (55, 69), (65, 70), (75, 72),
     (90, 74), (105, 76), (120, 73), (140, 72), (158, 69), (170, 67),
     (178, 65), (170, 60), (162, 60), (158, 52), (150, 59), (142, 50),
     (140, 40), (135, 35), (130, 33), (127, 35), (122, 31), (120, 28),
     (117, 25), (114, 21.5), (110, 20), (108, 18), (105, 10), (103, 8),
     (100, 6), (98, 10),
     (94, 16), (92, 21), (89, 22), (86, 20), (80, 15), (77, 8), (75, 12),
     (72, 20), (68, 23), (66, 25), (61, 25), (57, 26), (56, 24), (54, 22),
     (52, 18), (50, 16), (48, 14), (44, 13), (42, 15), (39, 21), (37, 25),
     (35, 29), (36, 32), (36, 36), (33, 36), (30, 36), (27, 37), (30, 41),
     (33, 42), (36, 43), (38, 46), (40, 47), (41, 52), (44, 56), (44, 60),
     (45, 64), (43, 68), (40, 68), (35, 68), (28, 71)],
    # Sumatra
    [(95, 5), (98, 2), (101, -2), (104, -4), (106, -6), (104, -3), (100, 0),
     (97, 4), (95, 5)],
    # Java
    [(105, -5.9), (108, -6.1), (111, -6.3), (114, -6.6), (114, -7.8),
     (110, -7.9), (106, -7.5), (105, -6.5), (105, -5.9)],
    # Borneo
    [(109, 1), (112, 3), (116, 6), (118, 2), (117, -2), (114, -3),
     (110, -2), (109, 1)],
    # New Guinea
    [(131, -1), (136, -2), (141, -3), (146, -6), (150, -8), (147, -9),
     (142, -8), (137, -6), (132, -4), (131, -1)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 37), (141, 39),
     (141, 42), (143, 44), (141, 41), (139, 38), (136, 35), (133, 34),
     (130, 31)],
    # Philippines
    [(120, 18), (122, 16), (122, 14), (121, 13), (124, 11), (126, 7),
     (122, 7), (120, 10), (120, 18)],
    # Taiwan
    [(120, 22), (121, 23), (121, 25), (120, 24), (120, 22)],
    # Sri Lanka
    [(80, 6), (81, 7), (80, 9), (79, 8), (80, 6)],
    # Australia
    [(114, -22), (114, -30), (115, -35), (118, -35), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -23), (146, -19), (142, -15), (142, -11),
     (137, -12), (135, -15), (132, -12), (130, -13), (126, -14), (122, -17),
     (118, -20), (114, -22)],
    # Tasmania
    [(145, -41), (148, -41), (148, -43), (146, -44), (145, -42), (145, -41)],
    # New Zealand (North + South Islands)
    [(167, -45), (170, -42), (173, -40), (175, -38), (177, -38), (174, -41),
     (171, -43), (168, -46), (167, -45)],
    [(166, -46), (168, -47), (170, -46), (168, -45), (166, -46)],
]

def lonlat_to_xy(lon, lat, box):
    x0, y0, x1, y1 = box
    fx = (lon + 180) / 360.0
    fy = (90 - lat) / 180.0
    return (x0 + fx * (x1 - x0), y0 + fy * (y1 - y0))

def draw_map(d, box):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(196, 214, 234))
    for poly in CONTINENTS:
        pts = [lonlat_to_xy(lon, lat, box) for lon, lat in poly]
        d.polygon(pts, fill=(214, 196, 148), outline=(125, 108, 68))
    # graticule
    for lon in range(-150, 181, 30):
        px, _ = lonlat_to_xy(lon, 0, box)
        d.line([(px, y0), (px, y1)], fill=(208, 222, 236), width=1)
    for lat in range(-60, 91, 30):
        _, py = lonlat_to_xy(0, lat, box)
        d.line([(x0, py), (x1, py)], fill=(208, 222, 236), width=1)

# pins: (story_no, lon, lat, dx, dy) - nudged so the Europe / Middle East
# cluster separates into readable pins (base positions are only ~1 deg apart)
PINS = [
    (1, 30.7, 36.9, 16, -17), (2, 56.5, 26.5, 14, 0), (3, 20.1, 32.1, -13, 9),
    (4, -77.0, 38.9, 0, 0), (5, 30.3, 50.8, -9, -19), (6, 32.5, 15.6, -4, 12),
    (7, 39.0, 22.8, 12, 12), (8, 51.4, 35.7, 15, -9), (9, 106.2, -6.1, 0, 0),
    (10, 7.7, 45.1, -6, -14), (11, -115.1, 36.2, 0, 0), (12, 30.5, 50.5, 6, -20),
    (13, 114.2, 22.3, 0, 0),
]

def draw_pins(d, box):
    for num, lon, lat, dx, dy in PINS:
        cx, cy = lonlat_to_xy(lon, lat, box)
        bx, by = cx + dx, cy + dy
        if dx or dy:
            d.line([(cx, cy), (bx, by)], fill=(150, 40, 40), width=1)
            d.ellipse([cx - 2.5, cy - 2.5, cx + 2.5, cy + 2.5],
                      fill=RED, outline=(255, 255, 255), width=1)
        d.ellipse([bx - 5, by - 5, bx + 5, by + 5], fill=RED,
                  outline=(255, 255, 255), width=1)
        f = F(SSB, 6)
        t = str(num)
        d.text((bx - tw(d, t, f) / 2, by - 4), t, font=f, fill=(255, 255, 255))

# ---------------------------------------------------------------- story data
# (num, region, place, tag, label_bar, headline, body, source, painter)
LEADS = [
    (1, "WORLD", "ANTALYA, TÜRKIYE · CLIMATE", "REPORTED",
     "NO DEAL AFTER LONGEST SUMMIT",
     "COP31 collapses: no deal after longest summit",
     "Antalya talks end Sunday with no pact as the EU and Pacific islands "
     "reject a draft silent on fossil fuels, 44 hours past deadline.",
     "UN News / CNN", draw_cop31),
    (2, "MIDDLE EAST", "STRAIT OF HORMUZ · WAR", "CLAIM",
     "2 TANKERS MINED",
     "Two tankers mined near Hormuz; Trump warns Iran",
     "Two supertankers hit by mines off Ghanam Island and ablaze. Trump on "
     "Fox News Sunday: Iran's fleet 'will all be at the bottom of the sea'.",
     "Daily Summary / Fox News", draw_tankers),
    (3, "AFRICA", "BENGHAZI, LIBYA · WAR", "REPORTED",
     "WARSHIP SUNK",
     "Sea drones sink Russian warship off Libya",
     "Corvette Merkury hit at Benghazi naval base at dawn, capsizes and "
     "sinks; a Malta-flagged merchant ship hit hours later.",
     "Reuters / CNN", draw_merkury),
]

MEDIUMS = [
    (4, "AMERICAS", "WASHINGTON · POLITICS", "REPORTED",
     "DEMOCRATS 258",
     "Democrats win 258 House seats, biggest since 1992",
     "AP calls it Sunday after the recount: Hubbard beats Foxx by 330 votes.",
     "AP / CNN", draw_capitol),
    (5, "EUROPE", "DYMER, UKRAINE · WAR", "REPORTED",
     "14 MISSING",
     "Russian drone collapses flat in Dymer, 14 missing",
     "Five-storey block partly falls near Kyiv; 6 killed across Kyiv region.",
     "BBC", draw_dymer),
    (6, "AFRICA", "KHARTOUM · WAR", "REPORTED",
     "4 DEAD",
     "Drone strike kills 4, hits UN building in Khartoum",
     "RSF-blamed attack hits UN compound with staff inside; 3 more die in Omdurman.",
     "France 24", draw_khartoum),
    (7, "MIDDLE EAST", "RABIGH, SAUDI ARABIA · WAR", "CLAIM",
     "REFINERY CLAIM",
     "Houthis claim strike on Rabigh refinery",
     "Coalition intercepts a drone and a ballistic missile; 6 hurt in Sanaa blast.",
     "Straits Times", draw_rabigh),
    (8, "MIDDLE EAST", "TEHRAN · ARMS", "REPORTED",
     "MISSILE CITY",
     "Iran unveils dual launcher, underground 'missile city'",
     "IRGC shows a new launcher and an underground base in a Sunday ceremony.",
     "Tasnim / IRNA", draw_missile),
    (9, "ASIA", "SERANG, INDONESIA · DISASTER", "REPORTED",
     "24 BODY BAGS",
     "24 body bags lifted from Banten candy factory",
     "Search goes on Sunday after Saturday's fire; 3 dead, 36 missing at first.",
     "AP / BBC", draw_banten),
    (10, "EUROPE", "TURIN · TENNIS", "REPORTED",
     "ATP FINALS",
     "Alcaraz wins first ATP Finals title",
     "Beats world No. 1 Zverev 6-2, 7-6 in the Turin final on Sunday.",
     "BBC / Guardian", draw_tennis),
    (11, "AMERICAS", "LAS VEGAS · FORMULA 1", "REPORTED",
     "35 LEAD CHANGES",
     "Verstappen wins Las Vegas Grand Prix",
     "Third win in 4 years there; 35 lead changes in 50 laps. Sat. night Vegas, Sun. UTC.",
     "CBC", draw_race),
    (12, "EUROPE", "KYIV · WAR", "REPORTED",
     "PATRIOTS HELD",
     "Zelenskyy presses US to release Patriot missiles",
     "After ~2,700 drones and 165 missiles in a week, he says.",
     "Daily Summary", draw_patriot),
    (13, "ASIA", "HONG KONG · ELECTION", "REPORTED",
     "99% TURNOUT",
     "Record turnout in Hong Kong committee polls",
     "98.37% by 5 pm; 723 seats; 856 candidates for the 1,500-member body.",
     "SCMP", draw_ballot),
]

# (num, region, title, source)
ALSO = [
    (14, "MIDDLE EAST", "West Bank settlers burn 12 vehicles", "France 24"),
    (15, "MIDDLE EAST", "Likud-Eisenkot unity talks end", "Al Jazeera"),
    (16, "MIDDLE EAST", "Gaza strikes go on, 2 killed; WCK clarifies", "MEE"),
    (17, "MIDDLE EAST", "Gaza toll since Oct 2025: 1,661", "Daily Summary"),
    (18, "EUROPE", "Cost-of-living protests, day 3", "Daily Summary"),
    (19, "ASIA", "S Korea minister quits over AI cheating", "BBC"),
    (20, "OCEANIA", "Cyclone Xavier weakens, Cook Islands", "RNZ Pacific"),
    (21, "AMERICAS", "Masked ICE agents arrest 2 at Seattle", "Al Jazeera"),
    (22, "ASIA", "Thai court upholds royal defamation verdict", "AP"),
    (23, "MIDDLE EAST", "Iran starts power rationing for winter", "BBC Persian"),
    (24, "ASIA", "China chip makers gain; Nvidia pressed", "Reuters"),
    (25, "ASIA", "Lowy: US-China power gap narrows", "Standard"),
    (26, "ASIA", "India Youth Congress protests at Meta", "Standard"),
    (27, "ASIA", "Delhi forum ends, no India-Pakistan talks", "Standard"),
    (28, "AMERICAS", "Haiti, El Salvador agree to build 3 prisons", "Guardian"),
    (29, "AMERICAS", "Skubal agrees $450m Mets deal", "Guardian"),
    (30, "AMERICAS", "KC Current win first NWSL title 2-1", "Al Jazeera"),
    (31, "AMERICAS", "Boca win Copa Sudamericana 2-0", "BA Times"),
    (32, "EUROPE", "Marquez seals 8th MotoGP title", "Guardian"),
    (33, "EUROPE", "England hosts 2035 Women's World Cup", "BBC Sport"),
    (34, "AFRICA", "Ammo depot blast at Benghazi", "Daily Summary"),
    (35, "WORLD", "Chess title match begins in Geneva", "Al Jazeera"),
]

NUMBERS = [
    ("NO DEAL", "COP31 collapses"),
    ("2", "tankers mined, Hormuz"),
    ("258", "House seats, Democrats"),
    ("24", "body bags, Banten factory"),
    ("99%", "turnout, Hong Kong vote"),
    ("$450m", "Skubal Mets deal, record pitcher"),
]

REGION_TABS = [
    ("EUROPE", 6), ("MIDDLE EAST", 8), ("AMERICAS", 7), ("ASIA-PACIFIC", 8),
    ("AFRICA", 3), ("OCEANIA", 1), ("WORLD", 2),
]

UTC_ITEMS = [
    ("00:04", "Gaza 1,661"),
    ("04:19", "Banten search"),
    ("07:47", "W. Bank arson"),
    ("12:00", "COP31 ends"),
    ("14:20", "Missile city"),
    ("15:36", "Merkury hit"),
    ("17:13", "Tankers mined"),
    ("Evening", "Foxx concedes, Dems 258"),
]

# ---------------------------------------------------------------- build
TAG_FILL = {"REPORTED": (46, 110, 80), "CLAIM": (200, 140, 20),
            "CONFIRMED": (40, 120, 60), "PENDING": (43, 95, 158)}

def build():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    MX = 10
    CW = W - 2 * MX

    # 1. dark top bar
    d.rectangle([0, 0, W, 22], fill=NAVY)
    d.text((MX, 5), "THE WORLD IN ONE DAY", font=F(SSB, 11), fill=(255, 255, 255))
    rt = "35 STORIES · 7 REGIONS · EVERY ONE DATED SUNDAY 22 NOVEMBER 2026"
    d.text((W - MX - tw(d, rt, F(SS, 10)), 6), rt, font=F(SS, 10), fill=(255, 255, 255))

    # 2. masthead
    y = 22
    title = "Sunday 22 November 2026"
    tf = F(FB, 48)
    d.text(((W - tw(d, title, tf)) / 2, y), title, font=tf, fill=INK)
    sub = "COP31 ends with no deal  ·  Two tankers mined off Hormuz  ·  Democrats take 258 House seats"
    sf = F(SI, 15)
    d.text(((W - tw(d, sub, sf)) / 2, y + 65), sub, font=sf, fill=RED)
    d.line([(MX, 114), (W - MX, 114)], fill=INK, width=2)
    d.line([(MX, 117), (W - MX, 117)], fill=INK, width=1)

    # 3. number strip
    y = 124
    cw = CW / 6
    for i, (num, lab) in enumerate(NUMBERS):
        cx = MX + i * cw
        nf = F(SB, 30)
        d.text((cx + (cw - tw(d, num, nf)) / 2, y), num, font=nf, fill=RED)
        lf = F(SS, 9)
        d.text((cx + (cw - tw(d, lab, lf)) / 2, y + 34), lab, font=lf, fill=GREY)
        if i:
            d.line([(cx, y + 2), (cx, y + 46)], fill=(200, 195, 180), width=1)
    d.line([(MX, y + 50), (W - MX, y + 50)], fill=INK, width=1)

    # 4. region tabs
    y = 178
    total_w = sum(int(tw(d, f"{n} {c}", F(SSB, 10))) + 18 for n, c in REGION_TABS)
    gap = (CW - total_w) / (len(REGION_TABS) - 1)
    x = MX
    for name, cnt in REGION_TABS:
        txt = f"{name} {cnt}"
        fnt = F(SSB, 10)
        w = int(tw(d, txt, fnt)) + 18
        d.rectangle([x, y, x + w, y + 18], fill=REGION_COLORS[name])
        d.text((x + 9, y + 3), txt, font=fnt, fill=(255, 255, 255))
        x += w + gap

    # 5. UTC strip
    y = 200
    d.rectangle([0, y, W, y + 18], fill=NAVY)
    d.text((MX, y + 3), "THE DAY IN UTC", font=F(SSB, 10), fill=GOLD)
    parts = []
    for t, what in UTC_ITEMS:
        parts.append((t, what))
    ux = MX + 118
    uf = F(SS, 9.5)
    for i, (t, what) in enumerate(parts):
        seg = f"{t}  {what}"
        d.text((ux, y + 3), seg, font=uf, fill=(255, 255, 255))
        ux += tw(d, seg, uf) + 8
        if i < len(parts) - 1:
            d.text((ux - 6, y + 3), "·", font=uf, fill=GOLD)

    # 6. three leads
    y = 222
    LW = (CW - 20) / 3
    LH_ILL = 112
    for i, (num, region, place, tag, label, head, body, src, painter) in enumerate(LEADS):
        lx = MX + i * (LW + 10)
        # illustration + label bar
        painter(d, int(lx), y, int(LW), LH_ILL)
        d.rectangle([lx, y, lx + LW, y + 16], fill=RED)
        d.text((lx + 6, y + 3), label, font=F(SSB, 9), fill=(255, 255, 255))
        yy = y + LH_ILL + 5
        # location line + tag chip
        d.text((lx, yy), f"{num}  {place}", font=F(SSB, 10), fill=RED)
        chip_w = tag_chip(d, lx + LW - 62, yy - 1, tag, TAG_FILL[tag])
        yy += 16
        # headline
        hl = fit_lines(d, head, F(SB, 19), LW, 2)
        yy = draw_text_block(d, lx, yy, hl, F(SB, 19), INK, 22)
        # body
        bl = fit_lines(d, body, F(SS, 10.5), LW, 3)
        yy = draw_text_block(d, lx, yy + 2, bl, F(SS, 10.5), INK, 14)
        # attribution
        d.text((lx, yy + 3), f"({src})", font=F(SI, 9), fill=GREY)

    # 7. medium grid 5 x 2
    y = 472
    MW = (CW - 4 * 6) / 5
    MH = 140
    for row in range(2):
        for col in range(5):
            idx = row * 5 + col
            num, region, place, tag, label, head, body, src, painter = MEDIUMS[idx]
            mx = MX + col * (MW + 6)
            my = y + row * (MH + 6)
            painter(d, int(mx), my, int(MW), 56)
            d.rectangle([mx, my, mx + MW, my + 13], fill=RED)
            d.text((mx + 5, my + 2), label, font=F(SSB, 8), fill=(255, 255, 255))
            yy = my + 60
            d.text((mx, yy), f"{num}  {place}", font=F(SSB, 8.5), fill=RED)
            yy += 13
            hl = fit_lines(d, head, F(SB, 12.5), MW, 2)
            yy = draw_text_block(d, mx, yy, hl, F(SB, 12.5), INK, 16)
            bl = fit_lines(d, body, F(SS, 9), MW, 2)
            yy = draw_text_block(d, mx, yy + 1, bl, F(SS, 9), INK, 12)
            d.text((mx, yy + 2), f"({src})", font=F(SI, 8), fill=GREY)

    # 8. map + also list (20px side margins for the whole bottom band)
    y = 770
    BMX = 20
    map_w = 260
    d.text((BMX, y), "WHERE IT HAPPENED", font=F(SSB, 11), fill=INK)
    rt = "pins match story numbers"
    d.text((BMX + map_w - tw(d, rt, F(SI, 9)), y + 1), rt, font=F(SI, 9), fill=GREY)
    map_box = (BMX, y + 16, BMX + map_w, y + 16 + 124)
    draw_map(d, map_box)
    draw_pins(d, map_box)

    ax = BMX + map_w + 10
    aw = W - BMX - ax
    d.text((ax, y), "ALSO ON SUNDAY 22 NOVEMBER — 22 MORE STORIES",
           font=F(SSB, 11), fill=INK)
    col_w = (aw - 12) / 2
    lf = F(SS, 9)
    nf = F(SSB, 9)
    rf = F(SSB, 8.5)
    # fixed-width region column so every title starts at the same x
    region_slot = int(tw(d, "MIDDLE EAST", rf)) + 8
    for i, (num, region, title, src) in enumerate(ALSO):
        col = i // 11
        r = i % 11
        xx = ax + col * (col_w + 12)
        yy = y + 16 + r * 13
        d.text((xx, yy), str(num), font=nf, fill=RED)
        d.text((xx + 18, yy), region, font=rf, fill=RED)
        rest = f"{title} — {src}"
        rl = fit_lines(d, rest, lf, col_w - 18 - region_slot - 6, 1)
        d.text((xx + 18 + region_slot + 6, yy), rl[0], font=lf, fill=INK)

    # 9. DATE CHECK (roomy: 11pt, 2 lines, bold red lead-in, 6 exclusions)
    y = 930
    d.rectangle([BMX, y, W - BMX, y + 42], outline=RED, width=2)
    prefix = "DATE CHECK — "
    pf = F(SSB, 11)
    bf = F(SS, 11)
    prefix_w = tw(d, prefix, pf)
    dc_body = ("BepiColombo entered Mercury orbit Sat 21 Nov · 'El Chapo Isidro' "
               "arrested Sat 21 Nov · Bahrain attack Sat 21 Nov · Sparta II hit "
               "Sat 21 Nov · WCK food-truck strike Sat 21 Nov · EU-Indonesia "
               "trade deal signed Sat 21 Nov. The Banten fire was Sat 21 Nov — "
               "Sunday's story is the search.")
    inner_w = (W - 2 * BMX) - 16
    dl = fit_lines(d, dc_body, bf, inner_w - prefix_w - 4, 2)
    d.text((BMX + 8, y + 10), prefix, font=pf, fill=RED)
    for i, ln in enumerate(dl):
        tx = BMX + 8 + (prefix_w if i == 0 else 0)
        d.text((tx, y + 10 + i * 14), ln, font=bf, fill=INK)

    # 10. footer (20px side margins, slightly larger type)
    y = 980
    d.text((BMX, y), "Sources: Reuters, BBC, AP, Al Jazeera, The Guardian, UN News, CNN, "
                    "France 24, Daily Summary, SCMP, Straits Times, Tasnim. Scenes are drawn "
                    "illustrations of reported events, not photographs.",
           font=F(SS, 9.5), fill=GREY)
    d.text((BMX, y + 11), "CERTAINTY:  REPORTED = carried by the day's wires   ·   "
                         "CLAIM = one side's account, labelled as such",
           font=F(SSB, 9.5), fill=GREY)
    d.rectangle([0, 1002, W, H], fill=NAVY)
    d.text((BMX, 1008), "THE WORLD IN ONE DAY", font=F(SSB, 10), fill=(255, 255, 255))
    rt = "SUNDAY 22 NOVEMBER 2026  ·  ONE PAGE"
    d.text((W - BMX - tw(d, rt, F(SS, 10)), 1008), rt, font=F(SS, 10), fill=(255, 255, 255))

    return img

if __name__ == "__main__":
    import os
    out = os.environ.get("OUT", "entry.png")
    img = build()
    img.save(out, optimize=True)
    print(out, img.size, os.path.getsize(out), "bytes")
    print("sha256", hashlib.sha256(open(out, "rb").read()).hexdigest())
