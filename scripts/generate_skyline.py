import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

NAME = "Анастасия"
ROLE = "Фронтенд-разработчик"
CITY = "Томск"
TZ_NAME = "Asia/Tomsk"       
TZ_FALLBACK_HOURS = 7       

W, H = 900, 320
GROUND = 18
BASE = H - GROUND

TOP = [(0, "#0b1030"), (5, "#1a1b4b"), (6.5, "#f59e6b"), (9, "#7cc6f2"), (15, "#6fb7ee"),
       (18, "#f97d5b"), (19.5, "#3b2a6e"), (21, "#0b1030"), (24, "#0b1030")]
BOT = [(0, "#1b2160"), (5, "#3b3b7a"), (6.5, "#fcd29a"), (9, "#cfeaff"), (15, "#bfe3ff"),
       (18, "#fdba74"), (19.5, "#7c3a8a"), (21, "#1b2160"), (24, "#1b2160")]


def city_hour():
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo(TZ_NAME))
    except Exception:
        now = datetime.now(timezone(timedelta(hours=TZ_FALLBACK_HOURS)))
    return now.hour + now.minute / 60


def rgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def mix(a, b, t):
    return [x + (y - x) * t for x, y in zip(a, b)]


def hexs(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in c)


def ramp(stops, x):
    for (h0, c0), (h1, c1) in zip(stops, stops[1:]):
        if h0 <= x <= h1:
            return mix(rgb(c0), rgb(c1), (x - h0) / (h1 - h0))
    return rgb(stops[-1][1])


def clamp(x):
    return max(0.0, min(1.0, x))


def night_factor(h):
    if h < 5 or h > 21:
        return 1.0
    if h < 7:
        return clamp((7 - h) / 2)
    if h > 18:
        return clamp((h - 18) / 3)
    return 0.0


def phase_word(h, n):
    if n > 0.95:
        return "ночь"
    if 5 <= h < 9:
        return "утро"
    if 9 <= h < 17:
        return "день"
    if 17 <= h < 21:
        return "вечер"
    return "сумерки"


def build(hour):
    n = night_factor(hour)
    top, bot = ramp(TOP, hour), ramp(BOT, hour)
    lum = 0.299 * top[0] + 0.587 * top[1] + 0.114 * top[2]   # яркость неба там, где текст
    ink = "#f1f5ff" if lum < 140 else "#10203a"
    out = []
    add = out.append

    add('<?xml version="1.0" encoding="UTF-8"?>')
    add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-labelledby="t d">')
    add(f'<title id="t">{NAME} — {ROLE.lower()}, {CITY}</title>')
    add(f'<desc id="d">{CITY}: {phase_word(hour, n)}. Город меняется в зависимости от времени суток.</desc>')
    add("<style>"
        ".tw{animation:tw 4s ease-in-out infinite}"
        "@keyframes tw{0%,100%{opacity:.25}50%{opacity:1}}"
        ".bl{animation:bl 6s ease-in-out infinite}"
        "@keyframes bl{0%,88%,100%{opacity:1}93%{opacity:.1}}"
        ".cm{animation:cm 12s linear infinite;opacity:0}"
        "@keyframes cm{0%{transform:translate(-120px,-20px);opacity:0}6%{opacity:1}"
        "26%{transform:translate(1000px,180px);opacity:0}100%{transform:translate(1000px,180px);opacity:0}}"
        "@media (prefers-reduced-motion:reduce){.tw,.bl,.cm{animation:none}}"
        "</style>")
    add("<defs>"
        f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{hexs(top)}"/><stop offset="1" stop-color="{hexs(bot)}"/></linearGradient>'
        '<radialGradient id="sg"><stop offset="0" stop-color="#fde047" stop-opacity=".55"/>'
        '<stop offset="1" stop-color="#fde047" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="mg"><stop offset="0" stop-color="#c7d2fe" stop-opacity=".4"/>'
        '<stop offset="1" stop-color="#c7d2fe" stop-opacity="0"/></radialGradient>'
        '<clipPath id="r"><rect width="%d" height="%d" rx="16"/></clipPath>' % (W, H) +
        "</defs>")
    add('<g clip-path="url(#r)">')
    add(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')

    # звёзды
    rnd = random.Random(11)
    if n > 0.05:
        add(f'<g opacity="{n:.2f}" fill="#fff">')
        for i in range(70):
            x, y, r = rnd.random() * W, rnd.random() * H * 0.62, 0.7 + rnd.random() * 1.0
            delay = rnd.random() * 4
            add(f'<circle class="tw" cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" style="animation-delay:-{delay:.1f}s"/>')
        add("</g>")
        if n > 0.6:
            add('<g class="cm"><line x1="0" y1="0" x2="-70" y2="-14" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/></g>')

    # солнце и луна
    def body(p, r, core, glow):
        if p < 0 or p > 1:
            return
        x, y = W * (0.08 + 0.84 * p), H * 0.74 - math.sin(math.pi * p) * H * 0.52
        add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r * 4}" fill="url(#{glow})"/>')
        add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{core}"/>')

    body((hour - 6) / 12, 22, "#fde047", "sg")
    body(((hour + 6) % 24) / 12, 16, "#eef2ff", "mg")

    # дома
    bcol = mix(rgb("#8793ad"), rgb("#151c33"), n)
    far = mix(bcol, bot, 0.55)
    rnd = random.Random(7)
    x = -20.0
    add(f'<g fill="{hexs(far)}">')
    while x < W:
        w, h = 60 + rnd.random() * 50, 80 + rnd.random() * 90
        add(f'<rect x="{x:.0f}" y="{BASE - h:.0f}" width="{w:.0f}" height="{h:.0f}"/>')
        x += w * (0.55 + rnd.random() * 0.3)
    add("</g>")

    day_win = hexs(mix(rgb("#c9d9ee"), bot, 0.25))
    off_win = hexs(mix(bcol, [255, 255, 255], 0.08))
    thr = 0.12 + 0.6 * n
    x = -5.0
    while x < W:
        w, h = 42 + rnd.random() * 40, 50 + rnd.random() * 85
        cols, rows = max(1, int((w - 10) // 12)), max(1, int((h - 12) // 16))
        add(f'<rect x="{x:.0f}" y="{BASE - h:.0f}" width="{w:.0f}" height="{h:.0f}" fill="{hexs(bcol)}"/>')
        ox = x + (w - cols * 12 + 6) / 2
        oy = BASE - h + 9
        for r in range(rows):
            for c in range(cols):
                v = rnd.random()
                if n < 0.15:
                    fill, cls = day_win, ""
                elif v < thr:
                    fill = "#fcd34d"
                    cls = ' class="bl" style="animation-delay:-%.1fs"' % (rnd.random() * 6) if v < 0.05 else ""
                else:
                    fill, cls = off_win, ""
                add(f'<rect x="{ox + c * 12:.0f}" y="{oy + r * 16:.0f}" width="5" height="8" fill="{fill}"{cls}/>')
        x += w + 2 + rnd.random() * 8
    add(f'<rect y="{BASE}" width="{W}" height="{GROUND}" fill="{hexs(mix(rgb("#4b5568"), rgb("#0a0f22"), n))}"/>')

    # текст
    add(f'<g fill="{ink}" font-family="Segoe UI, Helvetica, Arial, sans-serif">')
    add(f'<text x="40" y="78" font-size="54" font-weight="700" letter-spacing="-1">{NAME}</text>')
    add(f'<text x="42" y="112" font-size="22">{ROLE}</text>')
    add(f'<text x="42" y="138" font-size="17" opacity=".8">{CITY} · {phase_word(hour, n)}</text>')
    add("</g>")
    add("</g></svg>")
    return "\n".join(out)


def main():
    hour = city_hour()
    if "--hour" in sys.argv:
        hour = float(sys.argv[sys.argv.index("--hour") + 1])
    target = Path(__file__).resolve().parent.parent / "skyline.svg"
    if "--out" in sys.argv:
        target = Path(sys.argv[sys.argv.index("--out") + 1])
    target.write_text(build(hour), encoding="utf-8")
    print(f"skyline.svg: hour={hour:.2f} -> {target}")


if __name__ == "__main__":
    main()
