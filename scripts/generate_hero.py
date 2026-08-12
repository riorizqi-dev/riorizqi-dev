"""Generate hero-light.svg / hero-dark.svg - terminal window hero for GitHub profile README.

Avatar is rendered as a monochrome purple/cyan halftone dot-grid from a real photo.
Pure python + Pillow for the avatar, hand-built SVG for the window.
"""
import math
import sys
from PIL import Image

AVATAR_SRC = "avatar-src.png"

DATA = {
    "subject": "Rio Rizqi Saputra",
    "role": "Website Engineer & Full Stack",
    "origin": "Jakarta, Indonesia",
    "education": "RPL @ SMKN 17 Jakarta",
    "status": "open_for_freelance()",
    "toolchain": "VS Code  Git  Vercel",
    "core_lang": "TS  JS  PHP  Python  Kotlin",
    "core_frontend": "React  Next.js  Tailwind",
    "core_backend": "Laravel  Node.js  .NET",
    "core_db": "MySQL  Supabase",
    "core_infra": "Vercel  GitHub Actions",
    "mail": "riorizqi918@gmail.com",
    "portfolio": "portfolio-rio-green.vercel.app",
    "linkedin": "in/rio-rizqi-saputra",
    "instagram": "@riio_gorioio",
    "github": "github.com/riorizqi-dev",
    "facebook": "coming soon",
}

LINKS = {
    "mail": "mailto:riorizqi918@gmail.com",
    "portfolio": "https://portfolio-rio-green.vercel.app/",
    "linkedin": "https://www.linkedin.com/in/rio-rizqi-saputra-a86441417",
    "instagram": "https://www.instagram.com/riio_gorioio",
    "github": "https://github.com/riorizqi-dev",
    "facebook": None,
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def halftone_grid(img, cols=90, max_dots=1):
    """Downsample to cols-wide grayscale grid. Returns (r,g,b,a,lum) per cell."""
    w, h = img.size
    ratio = cols / w
    rows = max(1, round(h * ratio))
    small = img.resize((cols, rows), Image.LANCZOS).convert("RGBA")
    grid = []
    px = small.load()
    for y in range(rows):
        row = []
        for x in range(cols):
            r, g, b, a = px[x, y]
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            row.append((r, g, b, a, lum))
        grid.append(row)
    return grid, cols, rows


def avatar_svg(theme, x, y, size):
    """Dot-matrix halftone avatar. Returns svg fragment positioned at (x,y)."""
    img = Image.open(AVATAR_SRC)
    grid, cols, rows = halftone_grid(img, cols=88)
    cell = size / cols
    parts = []
    for cy, row in enumerate(grid):
        for cx, (r, g, b, a, lum) in enumerate(row):
            if a < 60:
                continue
            # halftone: dot radius proportional to darkness, bigger = darker
            rad = cell * 0.42 * max(0.0, 1.0 - lum) ** 0.7 + 0.06 * cell
            if rad < 0.35:
                continue
            px = x + cx * cell + cell / 2
            py = y + cy * cell + cell / 2
            if theme == "dark":
                if lum < 0.28:
                    c = "#22D3EE" if lum < 0.15 else "#7C3AED"
                elif lum < 0.55:
                    c = "#A78BFA"
                else:
                    c = "#4F46E5"
            else:
                if lum < 0.28:
                    c = "#0891B2" if lum < 0.15 else "#6D28D9"
                elif lum < 0.55:
                    c = "#7C3AED"
                else:
                    c = "#4F46E5"
            op = min(1.0, 0.35 + 0.9 * (1.0 - lum))
            parts.append(
                f'<circle cx="{px:.2f}" cy="{py:.2f}" r="{rad:.2f}" fill="{c}" opacity="{op:.2f}"/>'
            )
    return "\n".join(parts)


def dots_line(x1, y, x2):
    return (
        f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
        'stroke="currentColor" stroke-width="1.4" stroke-linecap="round" '
        'stroke-dasharray="0.5 4.5"/>'
    )


def row(label, value, y, label_color, value_color, label_x, value_x, dots_x1, dots_x2, font=13):
    label = esc(label)
    value = esc(value)
    return (
        f'<text x="{label_x}" y="{y}" font-size="{font}" font-family="{FONT}" fill="{label_color}">{label}</text>'
        + dots_line(dots_x1, y, dots_x2)
        + f'<text x="{value_x}" y="{y}" font-size="{font}" font-family="{FONT}" fill="{value_color}" text-anchor="end">{value}</text>'
    )


def build(theme):
    dark = theme == "dark"
    if dark:
        BG = "#0B0F1A"; TB = "#111827"; BD = "#1E293B"; TX = "#E2E8F0"; DIM = "#94A3B8"
        FNT = "#64748B"; PUR = "#A78BFA"; CYN = "#22D3EE"; GRN = "#34D399"
        RED = "#F87171"; YEL = "#FBBF24"; DOT1 = "#22D3EE"; DOT2 = "#7C3AED"
        CURS = "#22D3EE"
    else:
        BG = "#F8FAFC"; TB = "#F1F5F9"; BD = "#E2E8F0"; TX = "#0F172A"; DIM = "#475569"
        FNT = "#94A3B8"; PUR = "#7C3AED"; CYN = "#0891B2"; GRN = "#059669"
        RED = "#DC2626"; YEL = "#D97706"; DOT1 = "#0E7490"; DOT2 = "#6D28D9"
        CURS = "#0891B2"

    W, TITLE_H, PAD = 1180, 38, 26
    AV_SIZE = 330
    AV_X, AV_Y = PAD, TITLE_H + PAD + 26
    COL_GAP = 34
    RX = AV_X + AV_SIZE + COL_GAP
    RX2 = W - PAD
    label_x = RX
    dots_x1 = RX + 118
    dots_x2 = RX2 - 96
    value_x = RX2

    # ---- measure right column height to size window ----
    rows_h = 11 * 24  # system.info rows
    crows_h = 6 * 21  # contact rows
    body_h = max(AV_SIZE + 26 + 22, rows_h + 26 + 24 + crows_h)
    body_h += 46  # footer
    H = TITLE_H + PAD + body_h + PAD

    s = []
    a = s.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Rio Rizqi Saputra - Website Engineer and Full Stack Developer">')
    a(f'<defs><linearGradient id="hd" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0" stop-color="{DOT2}"/><stop offset="1" stop-color="{DOT1}"/></linearGradient></defs>')

    # window body
    a(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{BG}"/>')
    a(f'<rect x="0" y="0" width="{W}" height="{TITLE_H}" fill="{TB}"/>')
    a(f'<line x1="0" y1="{TITLE_H}" x2="{W}" y2="{TITLE_H}" stroke="{BD}" stroke-width="1"/>')

    # traffic dots
    for i, c in enumerate([RED, YEL, GRN]):
        cx = 22 + i * 20
        a(f'<circle cx="{cx}" cy="{TITLE_H/2}" r="6" fill="{c}"/>')

    # header path
    path = f'rio@github.dev  -  <tspan fill="{CYN}">%</tspan>  ./profile.sh --live'
    a(f'<text x="92" y="{TITLE_H/2 + 5}" font-size="13" font-family="{FONT}" fill="{FNT}">{path}</text>')

    # LIVE indicator right, red blinking
    a(f'<text x="{W-24}" y="{TITLE_H/2 + 5}" font-size="12" font-family="{FONT}" fill="{RED}" text-anchor="end">'
      f'<tspan>LIVE</tspan></text>')
    a(f'<circle cx="{W-64}" cy="{TITLE_H/2 - 1}" r="4.5" fill="{RED}">'
      f'<animate attributeName="opacity" values="1;0.15;1" dur="1.1s" repeatCount="indefinite"/></circle>')

    # column labels
    a(f'<text x="{AV_X}" y="{TITLE_H + PAD}" font-size="11" font-family="{FONT}" fill="{FNT}" letter-spacing="2">VISUAL.MAP</text>')
    a(f'<text x="{RX}" y="{TITLE_H + PAD}" font-size="11" font-family="{FONT}" fill="{PUR}" letter-spacing="2">SYSTEM.INFO</text>')

    # avatar + frame
    a(f'<rect x="{AV_X-8}" y="{AV_Y-8}" width="{AV_SIZE+16}" height="{AV_SIZE+16}" rx="10" fill="none" stroke="{BD}" stroke-width="1.5"/>')
    a(avatar_svg(theme, AV_X, AV_Y, AV_SIZE))
    a(f'<text x="{AV_X + AV_SIZE/2}" y="{AV_Y + AV_SIZE + 18}" font-size="11" font-family="{FONT}" fill="{FNT}" text-anchor="middle">pixel_map --halftone 88x88</text>')

    # SYSTEM.INFO rows
    y = TITLE_H + PAD + 24
    rows = [
        ("Subject", DATA["subject"], TX),
        ("Role", DATA["role"], TX),
        ("Origin", DATA["origin"], TX),
        ("Education", DATA["education"], TX),
        ("Status", DATA["status"], GRN),
        ("ToolChain", DATA["toolchain"], TX),
        ("Core.Lang", DATA["core_lang"], TX),
        ("Core.Frontend", DATA["core_frontend"], TX),
        ("Core.Backend", DATA["core_backend"], TX),
        ("Core.Database", DATA["core_db"], TX),
        ("Core.Infra", DATA["core_infra"], TX),
    ]
    for label, value, vc in rows:
        a(row(label, value, y, PUR, vc, label_x, value_x, dots_x1, dots_x2))
        y += 24

    y += 12
    a(f'<text x="{label_x}" y="{y}" font-size="11" font-family="{FONT}" fill="{PUR}" letter-spacing="2">CONTACT.GRID</text>')
    y += 26
    contacts = [
        ("Grid.Mail", DATA["mail"], LINKS["mail"]),
        ("Grid.Portfolio", DATA["portfolio"], LINKS["portfolio"]),
        ("Grid.LinkedIn", DATA["linkedin"], LINKS["linkedin"]),
        ("Grid.Instagram", DATA["instagram"], LINKS["instagram"]),
        ("Grid.GitHub", DATA["github"], LINKS["github"]),
        ("Grid.Facebook", DATA["facebook"], None),
    ]
    for label, value, link in contacts:
        if link:
            seg = f'<a href="{link}" style="text-decoration:none">{row(label, value, y, FNT, CYN, label_x, value_x, dots_x1, dots_x2, font=12)}</a>'
        else:
            seg = row(label, value, y, FNT, FNT, label_x, value_x, dots_x1, dots_x2, font=12)
        a(seg)
        y += 21

    # footer with blinking cursor
    fy = H - PAD - 6
    a(f'<line x1="{PAD}" y1="{fy+6}" x2="{W-PAD}" y2="{fy+6}" stroke="{BD}" stroke-width="1"/>')
    a(f'<text x="{PAD}" y="{fy}" font-size="13" font-family="{FONT}" fill="{FNT}">More about me &amp; projects below in README &#8595;</text>')
    cw = 10
    a(f'<rect x="{PAD+318}" y="{fy-13}" width="8" height="15" fill="{CURS}">'
      f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect>')

    a("</svg>")
    return "\n".join(s)


FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "hero-dark.svg"
    theme = "dark" if "dark" in out else "light"
    svg = build(theme)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out}: {len(svg)} bytes")
