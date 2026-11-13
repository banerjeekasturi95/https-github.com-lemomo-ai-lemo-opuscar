"""Reel 1 "The 4-Minute Nap" - animatic built from the ToonParenting character bibles.
Renders 1080x1920 frames at 30 fps to build/frames/, then audio.py + ffmpeg make the mp4."""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1080, 1920, 30, 21.0
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "frames")
os.makedirs(OUT, exist_ok=True)
exec(open(os.path.join(HERE, "crops.py")).read())

F_BOLD = os.path.join(HERE, "fonts", "Fredoka-700.ttf")
F_SEMI = os.path.join(HERE, "fonts", "Fredoka-600.ttf")
def font(sz, bold=True): return ImageFont.truetype(F_BOLD if bold else F_SEMI, sz)

NAVY = (31, 42, 68); NIGHT = (24, 30, 52); CREAM = (250, 242, 233); CORAL = (240, 112, 98)
PINK = (244, 176, 170); BROWN = (92, 58, 40); TAN = (214, 170, 120); SAGE = (164, 184, 152)
WHITE = (255, 255, 255); INK = (50, 36, 32)

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_in_out(t): t = clamp(t); return 3 * t * t - 2 * t * t * t
def ease_back(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

# ---------- assets ----------
SRC = {k: Image.open(os.path.join(HERE, "assets", f"bible-{k}.png")).convert("RGB") for k in ("mimi", "lala", "koko")}

def make_card(name, width, border=16, radius=56):
    s, box = CROPS[name]
    im = SRC[s].crop(box)
    h = int(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
    cw, ch = width + 2 * border, h + 2 * border
    pad = 40
    card = Image.new("RGBA", (cw + 2 * pad, ch + 2 * pad), (0, 0, 0, 0))
    # shadow
    sh = Image.new("L", card.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 14, pad + cw, pad + ch + 14), radius, fill=110)
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    card.paste((0, 0, 0, 255), (0, 0), sh)
    frame = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle((0, 0, cw - 1, ch - 1), radius, fill=CREAM + (255,))
    mask = Image.new("L", (width, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, h - 1), radius - border, fill=255)
    frame.paste(im, (border, border), mask)
    card.alpha_composite(frame, (pad, pad))
    return card

CARDS = {}
def card(name, width):
    key = (name, width)
    if key not in CARDS: CARDS[key] = make_card(name, width)
    return CARDS[key]

def place(canvas, img, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01: return
    im = img
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.05: im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1:
        a = im.getchannel("A").point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# ---------- backgrounds ----------
def radial(size, center, radius, color, strength):
    g = Image.new("L", size, 0)
    d = ImageDraw.Draw(g)
    cx, cy = center
    for i in range(30, 0, -1):
        r = radius * i / 30
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=int(strength * (1 - (i - 1) / 30) * 255))
    g = g.filter(ImageFilter.GaussianBlur(radius / 6))
    layer = Image.new("RGBA", size, color + (0,)); layer.putalpha(g)
    return layer

def bg_night():
    im = Image.new("RGBA", (W, H), NIGHT + (255,))
    im.alpha_composite(radial((W, H), (880, 520), 900, (255, 190, 120), 0.35))
    d = ImageDraw.Draw(im)
    for x, y, r in [(120, 300, 4), (260, 210, 3), (960, 260, 3), (180, 1600, 3), (900, 1700, 4), (70, 980, 3), (1010, 1180, 3)]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 236, 200, 200))
    # crescent moon decal
    d.ellipse((920, 1560, 1010, 1650), fill=(255, 226, 170, 255)); d.ellipse((945, 1548, 1030, 1633), fill=NIGHT + (255,))
    return im

def bg_hall():
    im = Image.new("RGBA", (W, H), (236, 214, 186, 255))
    im.alpha_composite(radial((W, H), (540, 300), 1100, (255, 236, 200), 0.6))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 1560, W, H), fill=(196, 160, 120, 255))  # floor
    for y in range(1600, H, 70): d.line((0, y, W, y), fill=(180, 144, 106, 255), width=3)
    return im

def bg_living(warm=1.0):
    base = tuple(int(c) for c in CREAM)
    im = Image.new("RGBA", (W, H), base + (255,))
    im.alpha_composite(radial((W, H), (200, 250), 1000, (255, 214, 170), 0.45 * warm))
    d = ImageDraw.Draw(im)
    # window light stripes
    for i in range(3):
        x = 80 + i * 70
        d.polygon([(x, 0), (x + 40, 0), (x + 380, 1920), (x + 300, 1920)], fill=(255, 250, 240, 60))
    # sofa silhouette at bottom
    d.rounded_rectangle((-40, 1480, W + 40, 2100), 80, fill=(232, 216, 196, 255))
    d.rounded_rectangle((-40, 1420, 220, 2100), 70, fill=(222, 204, 182, 255))
    d.rounded_rectangle((W - 220, 1420, W + 40, 2100), 70, fill=(222, 204, 182, 255))
    return im

def bg_frozen():
    im = Image.new("RGBA", (W, H), (226, 222, 220, 255))
    v = Image.new("L", (W, H), 0)
    ImageDraw.Draw(v).ellipse((-300, 100, W + 300, H - 100), fill=255)
    v = v.filter(ImageFilter.GaussianBlur(200))
    dark = Image.new("RGBA", (W, H), (120, 116, 130, 255)); dark.putalpha(v.point(lambda p: 255 - p))
    im.alpha_composite(dark)
    return im

BG = {"night": bg_night(), "hall": bg_hall(), "living": bg_living(), "living_warm": bg_living(1.6), "frozen": bg_frozen()}

# ---------- props ----------
def draw_cot(canvas, x, y, w, h, alpha=255):
    d = ImageDraw.Draw(canvas)
    wood = (200, 150, 100, alpha); dark = (150, 104, 66, alpha)
    d.rounded_rectangle((x, y, x + w, y + 26), 13, fill=wood)
    d.rounded_rectangle((x, y + h - 26, x + w, y + h), 13, fill=wood)
    n = int(w / 62)
    for i in range(n + 1):
        bx = x + 10 + i * (w - 20) / n
        d.rounded_rectangle((bx - 9, y + 20, bx + 9, y + h - 20), 9, fill=wood)
    d.rounded_rectangle((x - 22, y - 60, x + 22, y + h + 50), 20, fill=dark)
    d.rounded_rectangle((x + w - 22, y - 60, x + w + 22, y + h + 50), 20, fill=dark)

def draw_zzz(canvas, x, y, t):
    d = ImageDraw.Draw(canvas)
    for i in range(3):
        p = (t * 0.6 + i / 3) % 1
        a = int(255 * math.sin(p * math.pi))
        d.text((x + i * 40 + p * 30, y - p * 160), "z", font=font(56 + i * 14), fill=(255, 236, 200, a))

def draw_door(canvas, xleft):
    d = ImageDraw.Draw(canvas)
    d.rectangle((xleft, 0, W + 50, H), fill=(156, 104, 64, 255))
    d.rectangle((xleft, 0, xleft + 22, H), fill=(120, 78, 46, 255))
    for (a, b) in [(220, 820), (960, 1560)]:
        d.rounded_rectangle((xleft + 80, a, xleft + 600, b), 24, outline=(128, 84, 50, 255), width=10)
    d.ellipse((xleft + 50, 900, xleft + 100, 950), fill=(232, 196, 120, 255))

def draw_steam(canvas, cx, top, t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    for k in range(3):
        pts = []
        for j in range(11):
            yy = top - j * 12
            xx = cx + (k - 1) * 34 + 12 * math.sin(j * 0.45 + t * 4 + k)
            pts.append((xx, yy))
        d.line(pts, fill=(255, 255, 255, 170), width=11, joint="curve")
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(5)))

def draw_monitor(canvas, cx, cy, glow, t):
    if glow > 0:
        canvas.alpha_composite(radial((W, H), (cx, cy), 420, (140, 220, 255), 0.55 * glow))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((cx - 150, cy - 190, cx + 150, cy + 190), 48, fill=(245, 245, 245, 255), outline=(200, 196, 192, 255), width=6)
    d.line((cx + 90, cy - 190, cx + 120, cy - 290), fill=(200, 196, 192, 255), width=12)
    scr = (cx - 112, cy - 150, cx + 112, cy + 60)
    d.rounded_rectangle(scr, 22, fill=(40, 50, 70, 255))
    if glow > 0.3:
        k = card("koko_mischievous", 190)
        place(canvas, k, cx, cy - 45, 0.96, alpha=clamp(glow))
    for i in range(5):
        on = glow > 0 and (i < 2 + 3 * (0.5 + 0.5 * math.sin(t * 18)))
        col = (120, 220, 120, 255) if on else (210, 206, 202, 255)
        d.rounded_rectangle((cx - 90 + i * 40, cy + 100, cx - 66 + i * 40, cy + 140), 6, fill=col)

def coffee_icon(canvas, x, y, s=1.0):
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((x, y, x + 70 * s, y + 66 * s), 14 * s, fill=WHITE)
    d.arc((x + 52 * s, y + 12 * s, x + 92 * s, y + 50 * s), -90, 90, fill=WHITE, width=int(10 * s))
    for k in range(2):
        d.arc((x + (16 + k * 24) * s, y - 40 * s, x + (34 + k * 24) * s, y - 4 * s), 120, 300, fill=WHITE, width=int(6 * s))

# ---------- text ----------
def text_pill(canvas, lines, cy, t_in, t, bg=CORAL, fg=WHITE, size=78, icon=False):
    p = ease_back((t - t_in) / 0.35)
    if t < t_in: return
    f = font(size)
    d0 = ImageDraw.Draw(canvas)
    widths = [d0.textlength(l, font=f) for l in lines]
    lh = int(size * 1.18)
    bw = max(widths) + 110 + (110 if icon else 0); bh = lh * len(lines) + 60
    layer = Image.new("RGBA", (int(bw) + 60, int(bh) + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sh = Image.new("L", layer.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((30, 40, 30 + bw, 40 + bh), 46, fill=90)
    layer.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(10)))
    d.rounded_rectangle((30, 30, 30 + bw, 30 + bh), 46, fill=bg + (255,))
    for i, l in enumerate(lines):
        x = 30 + (bw - widths[i] - (110 if icon else 0)) / 2
        d.text((x, 30 + 26 + i * lh), l, font=f, fill=fg)
    if icon: coffee_icon(layer, 30 + bw - 150, 30 + bh / 2 - 22, 0.95)
    place(canvas, layer, W / 2, cy, scale=0.6 + 0.4 * p, rot=(1 - clamp((t - t_in) / 0.35)) * -4, alpha=clamp((t - t_in) / 0.15))

def bubble(canvas, speaker, line, cx, cy, t_in, t, t_out=99, tail="up", size=62):
    if t < t_in or t > t_out: return
    p = ease_back((t - t_in) / 0.3)
    f = font(size); fs = font(36, bold=False)
    d0 = ImageDraw.Draw(canvas)
    tw = d0.textlength(line, font=f)
    bw, bh = tw + 100, size * 1.2 + 60
    layer = Image.new("RGBA", (int(bw) + 80, int(bh) + 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = 40, 70
    d.rounded_rectangle((ox, oy, ox + bw, oy + bh), 40, fill=WHITE, outline=INK, width=6)
    if tail == "up":
        d.polygon([(ox + 90, oy + 4), (ox + 120, oy - 50), (ox + 160, oy + 4)], fill=WHITE)
        d.line([(ox + 90, oy + 3), (ox + 120, oy - 50), (ox + 160, oy + 3)], fill=INK, width=6)
    d.text((ox + 50, oy + 26), line, font=f, fill=INK)
    # speaker tag
    tag = speaker.upper()
    tw2 = d.textlength(tag, font=fs)
    d.rounded_rectangle((ox + bw - tw2 - 70, oy + bh - 22, ox + bw - 20, oy + bh + 34), 24, fill=NAVY)
    d.text((ox + bw - tw2 - 45, oy + bh - 18), tag, font=fs, fill=WHITE)
    place(canvas, layer, cx, cy, scale=0.5 + 0.5 * p, alpha=clamp((t - t_in) / 0.12))

def sfx_word(canvas, word, cx, cy, t_in, t, t_out, color, size=96, rot=-8):
    if t < t_in or t > t_out: return
    p = ease_back((t - t_in) / 0.25)
    f = font(size)
    d0 = ImageDraw.Draw(canvas)
    tw = d0.textlength(word, font=f)
    layer = Image.new("RGBA", (int(tw) + 60, int(size * 1.5) + 40), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((30, 20), word, font=f, fill=color, stroke_width=8, stroke_fill=WHITE)
    fade = clamp((t_out - t) / 0.25)
    place(canvas, layer, cx, cy, scale=p, rot=rot, alpha=fade)

# ---------- shots ----------
def frame(t):
    if t < 1.5:   # 1: tiptoe away from cot
        c = BG["night"].copy()
        draw_cot(c, 90, 1180, 420, 300)
        draw_zzz(c, 230, 1130, t)
        tip = math.sin(t * 9) * 10
        place(c, card("mimi_worried", 500), 640 - t * 30, 990 + abs(tip), scale=1.0 + 0.03 * t, rot=tip * 0.25)
        text_pill(c, ["Baby finally asleep.", "Don't. Breathe."], 400, 0.0, max(t, 0.35))
        return c
    if t < 4.0:   # 2: door creak
        lt = t - 1.5
        c = BG["hall"].copy()
        shake = 6 * math.sin(lt * 60) if 0.3 < lt < 1.7 else 0
        place(c, card("mimi_stressed", 600), 470 + shake, 930, scale=1.0 + 0.04 * lt)
        draw_door(c, int(W + 20 - 420 * ease_in_out(lt / 2.5)))
        sfx_word(c, "creeeak…", 640, 1450, 0.2 + 1.5, t, 3.9, BROWN, 104, -6)
        return c
    if t < 7.0:   # 3: hello, old friend
        lt = t - 4.0
        c = BG["living"].copy()
        sink = 30 * ease_out(lt / 1.0)
        place(c, card("mimi_coffee", 640), 540, 880 + sink, scale=1.0 + 0.025 * lt)
        draw_steam(c, 650, 1030 + sink, t)
        text_pill(c, ["First hot coffee in 6 days"], 330, 4.0, t, size=64)
        bubble(c, "Mimi", "Hello, old friend.", 560, 1420, 4.6, t)
        return c
    if t < 9.0:   # 4: monitor lights up
        lt = t - 7.0
        c = BG["living"].copy()
        glow = clamp((lt - 0.55) / 0.15)
        place(c, card("mimi_happy" if lt < 0.6 else "mimi_surprised", 470), 330, 880, scale=1.0 + 0.05 * lt)
        draw_monitor(c, 820, 900, glow * (0.8 + 0.2 * math.sin(t * 20)), t)
        sfx_word(c, "coo!", 860, 560, 7.75, t, 9.0, (80, 160, 210), 90, 8)
        return c
    if t < 11.5:  # 5: Koko wide awake
        lt = t - 9.0
        c = BG["night"].copy()
        shake = 14 * math.sin(lt * 70) * clamp(1 - lt / 0.4)
        place(c, card("koko_mischievous", 620), 540 + shake, 900, scale=1.12 - 0.12 * ease_out(lt / 0.4) + 0.02 * lt)
        draw_cot(c, 150, 1180, 780, 290)
        text_pill(c, ["Nap duration: 4 minutes"], 360, 9.15, t, bg=NAVY, size=70)
        return c
    if t < 14.0:  # 6: frozen
        lt = t - 11.5
        c = BG["frozen"].copy()
        place(c, card("mimi_overwhelmed", 640), 540, 880, scale=1.0 + 0.06 * ease_in_out(lt / 2.5))
        bubble(c, "Mimi", "Four minutes. Four.", 540, 1440, 12.0, t)
        return c
    if t < 18.0:  # 7: Lala to the rescue
        lt = t - 14.0
        c = BG["living_warm"].copy()
        place(c, card("mimi_happy", 400), 790, 760, scale=1.0 + 0.02 * lt)
        x = -300 + 600 * ease_out(lt / 0.7)
        place(c, card("lala_casual_mug", 380), x, 980, rot=2 * (1 - ease_out(lt / 0.7)))
        bubble(c, "Lala", "Drink. I've got the boss.", 560, 1440, 14.6, t, size=58)
        return c
    # 8: teamwork payoff + loop
    lt = t - 18.0
    c = BG["living_warm"].copy()
    place(c, card("lala_playing", 700), 540, 860, scale=0.8 + 0.2 * ease_back(lt / 0.45) + 0.02 * lt)
    place(c, card("mimi_coffee", 300), 820, 1290, scale=ease_back((lt - 0.5) / 0.35), rot=-4)
    text_pill(c, ["Teamwork = hot coffee"], 360, 18.3, t, size=66, icon=True)
    sfx_word(c, "hee hee!", 300, 560, 18.4, t, 20.3, CORAL, 84, -10)
    fade = clamp((t - 20.4) / 0.6)
    if fade > 0:
        nb = BG["night"].copy(); nb.putalpha(int(255 * fade)); c.alpha_composite(nb)
    return c

if __name__ == "__main__":
    only = [float(a) for a in sys.argv[1:]]
    if only:
        for tt in only:
            frame(tt).convert("RGB").save(os.path.join(HERE, "build", f"still_{tt:05.2f}.png"))
    else:
        n = int(DUR * FPS)
        for i in range(n):
            frame(i / FPS).convert("RGB").save(os.path.join(OUT, f"f{i:04d}.png"), compress_level=1)
            if i % 60 == 0: print(i, "/", n, flush=True)
