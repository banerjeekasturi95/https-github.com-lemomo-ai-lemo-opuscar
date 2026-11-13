"""Original synthesized sound bed for Reel 1 (no samples, no copyrighted music)."""
import numpy as np, wave, os

SR = 48000; DUR = 21.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
mix = np.zeros(N)
HERE = os.path.dirname(os.path.abspath(__file__))

def add(sig, t0, gain=1.0):
    i = int(t0 * SR); j = min(N, i + len(sig))
    if j > i: mix[i:j] += gain * sig[: j - i]

def tt(d): return np.arange(int(d * SR)) / SR
def env(d, a=0.01, r=None):
    t = tt(d); e = np.minimum(1, t / a)
    if r: e *= np.exp(-t / r)
    return e

def bandnoise(d, lo, hi):
    x = rng.standard_normal(int(d * SR)); X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, len(x)); return y / (np.abs(y).max() + 1e-9)

def pluck(freq, d=1.6, bright=0.5):
    n = int(d * SR); p = int(SR / freq)
    buf = list(rng.uniform(-1, 1, p)); out = [0.0] * n
    for i in range(n):
        a = buf[i % p]; out[i] = a
        buf[i % p] = 0.498 * (a + buf[(i + 1) % p])
    return np.array(out) * np.exp(-tt(d) / 0.9)

def pad(freqs, d):
    t = tt(d); s = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) for f in freqs)
    e = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.4)
    return s / len(freqs) * e

def note(m): return 440 * 2 ** ((m - 69) / 12)

# 0-1.5 s: soft heartbeat
for k in range(3):
    for off, g in ((0, 1.0), (0.18, 0.7)):
        t = tt(0.25); add((np.sin(2 * np.pi * 70 * t) + 0.6 * np.sin(2 * np.pi * 140 * t)) * np.exp(-t / 0.06) * np.minimum(1, t / 0.005), 0.1 + k * 0.62 + off, 0.55 * g)

# ~1.75-3.3 s: door creak (wobbly, resonant sawtooth + grit)
d = 1.55; t = tt(d)
f0 = 140 + 90 * np.sin(2 * np.pi * 0.6 * t) + 25 * np.sin(2 * np.pi * 7 * t) + 40 * t
ph = 2 * np.pi * np.cumsum(f0) / SR
saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
grit = (rng.random(len(t)) < 0.02) * rng.standard_normal(len(t))
creak = (0.6 * saw + 0.4 * np.sin(3 * ph) + 0.6 * grit) * np.minimum(1, t / 0.08) * np.minimum(1, (d - t) / 0.2)
add(creak, 1.75, 0.38)

# music: gentle plucked progression (C - Am - F - G), original
prog = [(60, 64, 67), (57, 60, 64), (53, 57, 60), (55, 59, 62)]
melody = [72, 74, 76, 79, 76, 74, 72, 69, 72, 71, 67, 71, 72]
def music(t0, t1, gain, warm=False):
    seg = np.zeros(N); beat = 0.42; i = 0; tcur = t0
    global mix
    keep = mix; mix = seg
    while tcur < t1:
        ch = prog[(i // 4) % 4]
        if i % 4 == 0: add(pad([note(m - 12) for m in ch], beat * 4) * 0.35, tcur)
        add(pluck(note(ch[i % 3] + 12), 1.2) * 0.4, tcur)
        if warm and i % 2 == 0: add(pluck(note(melody[(i // 2) % len(melody)]), 1.0) * 0.35, tcur + 0.02)
        i += 1; tcur += beat
    mix = keep
    a, b = int(t0 * SR), int(t1 * SR)
    fade = np.ones(b - a); fl = int(0.25 * SR); fade[:fl] = np.linspace(0, 1, fl)
    mix[a:b] += gain * seg[a:b] * fade

music(4.0, 7.62, 0.55)                     # cuts when the monitor lights up
music(14.0, 21.0, 0.6, warm=True)          # returns, warmer

# 7.6 s monitor beep + 7.8 s happy coo
t = tt(0.12); add(np.sin(2 * np.pi * 1320 * t) * env(0.12, 0.005, 0.05), 7.6, 0.25)
def coo(t0, f_start, f_end, d=0.45, g=0.3):
    t = tt(d); f = np.linspace(f_start, f_end, len(t)) * (1 + 0.03 * np.sin(2 * np.pi * 7 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    v = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)
    add(v * np.sin(np.pi * t / d) ** 1.5, t0, g)
coo(7.8, 420, 640); coo(8.3, 600, 520, 0.35, 0.22)

# 9.0 s record scratch
d = 0.5; t = tt(d)
sc = bandnoise(d, 300, 4000) * np.sin(2 * np.pi * (900 - 1500 * t) * t)
add(sc * np.exp(-t / 0.25), 9.0, 1.0)

# 11.5 s single piano note (low, sustained)
d = 2.4; t = tt(d); f = note(52)
pn = sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t * (0.9 + 0.6 * h)) / h for h in range(1, 7))
add(pn * np.minimum(1, t / 0.005), 11.5, 0.3)

# 18.4 s and 19.5 s Koko giggles
for base in (18.4, 19.5):
    for k in range(5):
        coo(base + k * 0.11, 700 + 40 * k, 620 + 30 * k, 0.09, 0.2)

# master: gentle limiter + loop-friendly fade
mix = np.tanh(mix * 1.2) * 0.85
fo = int(0.5 * SR); mix[-fo:] *= np.linspace(1, 0, fo)
pcm = (mix * 32767).astype(np.int16)
with wave.open(os.path.join(HERE, "build", "sound.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok")
