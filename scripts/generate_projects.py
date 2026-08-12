"""Generate projects.svg - PROJECTS.LIST terminal window for GitHub profile README.

Fetches real repo data (languages, stars, pushed_at) from the GitHub API and
renders a 2-column grid of terminal cards with donut charts + language bars.

Usage:
    python scripts/generate_projects.py [owner] [token]
Runs standalone (uses urllib, no third-party deps) so it also works in a
GitHub Action cron job.
"""
import json
import math
import os
import sys
import urllib.request
from datetime import datetime, timezone

OWNER = "riorizqi-dev"
REPOS = [
    ("kantinku", "Digital canteen ordering system", ["Next.js", "Supabase", "Tailwind"]),
    ("vantor", "Luxury watch brand landing page", ["Next.js 15", "GSAP", "Framer Motion"]),
    ("cafe-yo", "Cafe management system", ["ASP.NET Core", "MVC", "MySQL"]),
    ("rfm-market", "Stocks & crypto dashboard UI", ["HTML", "Tailwind"]),
    ("the-killer", "Noir contract specialists page", ["HTML", "CSS", "JS"]),
    ("portfolio-rio", "Personal portfolio site", ["React 19", "TypeScript", "Vite"]),
]

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
LANG_COLORS = {
    "TypeScript": "#3178C6", "JavaScript": "#F1E05A", "HTML": "#E34C26",
    "CSS": "#663399", "Python": "#3572A5", "C#": "#178600", "Kotlin": "#A97BFF",
    "SCSS": "#C6538C", "PHP": "#4F5D95", "C++": "#F34B7D", "TSQL": "#e38c00",
}

# dark / light palettes
PAL = {
    "dark": dict(bg="#0B0F1A", tb="#111827", bd="#1E293B", tx="#E2E8F0", dim="#94A3B8",
                 fnt="#64748B", pur="#A78BFA", cyn="#22D3EE", grn="#34D399",
                 red="#F87171", yel="#FBBF24", card="#0F172A", dot1="#22D3EE", dot2="#7C3AED"),
    "light": dict(bg="#F8FAFC", tb="#F1F5F9", bd="#E2E8F0", tx="#0F172A", dim="#475569",
                  fnt="#94A3B8", pur="#7C3AED", cyn="#0891B2", grn="#059669",
                  red="#DC2626", yel="#D97706", card="#FFFFFF", dot1="#0E7490", dot2="#6D28D9"),
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def http_json(url, token=None):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "profile-readme-generator")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def ago(pushed_at):
    try:
        dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        diff = datetime.now(timezone.utc) - dt
        secs = diff.total_seconds()
    except Exception:
        return "updated recently"
    if secs < 86400:
        return "updated today"
    days = int(secs // 86400)
    if days < 30:
        return f"updated {days}d ago"
    months = int(days // 30)
    if months < 12:
        return f"updated {months}mo ago"
    return f"updated {int(months // 12)}y ago"


def fetch_data(token):
    out = []
    for name, desc, badges in REPOS:
        try:
            meta = http_json(f"https://api.github.com/repos/{OWNER}/{name}", token)
            langs = http_json(f"https://api.github.com/repos/{OWNER}/{name}/languages", token)
        except Exception as e:
            print(f"warn: {name} fetch failed: {e}", file=sys.stderr)
            continue
        total = sum(langs.values()) or 1
        lang_rows = sorted(langs.items(), key=lambda kv: -kv[1])[:3]
        lang_pct = [(k, v * 100.0 / total) for k, v in lang_rows]
        primary = lang_pct[0][0] if lang_pct else "Unknown"
        out.append({
            "name": name, "desc": desc, "badges": badges,
            "langs": lang_pct, "primary": primary,
            "primary_pct": lang_pct[0][1] if lang_pct else 0,
            "stars": meta.get("stargazers_count", 0),
            "updated": ago(meta.get("pushed_at", "")),
            "icon_letter": name[0].upper(),
            "icon_color": LANG_COLORS.get(primary, "#4F46E5"),
        })
    return out


def donut(x, y, r, pct, theme):
    p = PAL[theme]
    C = 2 * math.pi * r
    dash = max(0.5, C * pct / 100.0)
    txt = f"{round(pct)}%"
    return (
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{p["bd"]}" stroke-width="5"/>'
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="url(#hd)" stroke-width="5" '
        f'stroke-linecap="round" stroke-dasharray="{dash:.2f} {C:.2f}" transform="rotate(-90 {x} {y})"/>'
        f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-size="11" font-family="{FONT}" '
        f'fill="{p["tx"]}">{txt}</text>'
    )


def lang_bar(name, pct, x, y, w, theme):
    p = PAL[theme]
    color = LANG_COLORS.get(name, "#4F46E5")
    bar_w = w - 96
    fill = max(0.0, min(100.0, pct))
    return (
        f'<circle cx="{x + 5}" cy="{y}" r="3.5" fill="{color}"/>'
        f'<text x="{x + 14}" y="{y + 4}" font-size="11" font-family="{FONT}" fill="{p["dim"]}">{esc(name)}</text>'
        f'<text x="{x + w}" y="{y + 4}" font-size="11" font-family="{FONT}" fill="{p["dim"]}" text-anchor="end">{pct:.1f}%</text>'
        f'<rect x="{x}" y="{y + 10}" width="{bar_w}" height="5" rx="2.5" fill="{p["bd"]}"/>'
        f'<rect x="{x}" y="{y + 10}" width="{bar_w * fill / 100.0:.1f}" height="5" rx="2.5" fill="url(#hd)"/>'
    )


def card(repo, x, y, w, h, theme):
    p = PAL[theme]
    inner_x = x + 14
    top_y = y + 12
    return [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{p["card"]}" stroke="{p["bd"]}" stroke-width="1"/>',
        f'<text x="{inner_x}" y="{top_y}" font-size="10.5" font-family="{FONT}" fill="{p["fnt"]}">{OWNER}/{esc(repo["name"])}</text>',
        f'<rect x="{inner_x}" y="{top_y + 12}" width="30" height="30" rx="8" fill="{repo["icon_color"]}"/>',
        f'<text x="{inner_x + 15}" y="{top_y + 33}" text-anchor="middle" font-size="14" font-weight="700" font-family="{FONT}" fill="{p["bg"]}">{repo["icon_letter"]}</text>',
        f'<text x="{inner_x + 40}" y="{top_y + 28}" font-size="13.5" font-weight="700" font-family="{FONT}" fill="{p["tx"]}">{esc(repo["name"].upper())}</text>',
        f'<text x="{inner_x + 40}" y="{top_y + 43}" font-size="11.5" font-family="{FONT}" fill="{p["dim"]}">{esc(repo["desc"])}</text>',
    ] + [badge(b, x + 14 + i * (len(b) * 7.2 + 16), y + 66, theme) for i, b in enumerate(repo["badges"])] \
      + [lang_bar(repo["langs"][i][0], repo["langs"][i][1],
                  x + 14, y + 92 + i * 28, w - 28, theme) for i in range(len(repo["langs"]))] \
      + [donut(x + w - 46, y + 44, 15, repo["primary_pct"], theme),
         f'<text x="{inner_x}" y="{y + h - 12}" font-size="11" font-family="{FONT}" fill="{p["fnt"]}">'
         f'&#9733; {repo["stars"]} &#183; {repo["updated"]}</text>']


def badge(text, x, y, theme):
    p = PAL[theme]
    w = len(text) * 7.4 + 16
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="20" rx="10" fill="{p["dot2"]}" opacity="0.85"/>'
        f'<text x="{x + w / 2}" y="{y + 14}" text-anchor="middle" font-size="10.5" font-family="{FONT}" fill="#FFFFFF">{esc(text)}</text>'
    )


def socials(y, theme, W):
    p = PAL[theme]
    items = [
        ("in  LinkedIn", "https://www.linkedin.com/in/rio-rizqi-saputra-a86441417", "#0077B5"),
        ("Instagram", "https://www.instagram.com/riio_gorioio", "#E4405F"),
        ("f  Facebook · soon", None, "#1877F2"),
        ("@  Email", "mailto:riorizqi918@gmail.com", "#10B981"),
    ]
    parts = []
    total_w = 0
    segs = []
    for text, href, color in items:
        w = len(text) * 7.6 + 30
        segs.append((text, href, color, w))
        total_w += w + 18
    x0 = (W - total_w + 18) / 2
    cx = x0
    for text, href, color, w in segs:
        rx = cx
        if href:
            seg = f'<a href="{href}" style="text-decoration:none">'
        else:
            seg = ""
        seg += (f'<rect x="{rx}" y="{y}" width="{w}" height="26" rx="8" fill="{color}"/>'
                f'<text x="{rx + w / 2}" y="{y + 17}" text-anchor="middle" font-size="12" font-weight="700" '
                f'font-family="{FONT}" fill="#FFFFFF">{esc(text)}</text>')
        if href:
            seg += "</a>"
        parts.append(seg)
        cx += w + 18
    return parts


def build(repos, theme):
    p = PAL[theme]
    W = 1180
    TITLE_H = 38
    PAD = 26
    CARD_W = (W - PAD * 2 - 14) / 2
    CARD_H = 168
    grid_h = 3 * CARD_H + 2 * 14
    H = TITLE_H + PAD + 30 + grid_h + 26 + 30 + 26 + 20
    s = []
    a = s.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="PROJECTS.LIST">')
    a(f'<defs><linearGradient id="hd" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0" stop-color="{p["dot2"]}"/><stop offset="1" stop-color="{p["dot1"]}"/></linearGradient></defs>')
    a(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{p["bg"]}"/>')
    a(f'<rect x="0" y="0" width="{W}" height="{TITLE_H}" fill="{p["tb"]}"/>')
    a(f'<line x1="0" y1="{TITLE_H}" x2="{W}" y2="{TITLE_H}" stroke="{p["bd"]}" stroke-width="1"/>')
    for i, c in enumerate([p["red"], p["yel"], p["grn"]]):
        a(f'<circle cx="{22 + i * 20}" cy="{TITLE_H / 2}" r="6" fill="{c}"/>')
    a(f'<text x="92" y="{TITLE_H / 2 + 5}" font-size="13" font-family="{FONT}" fill="{p["fnt"]}">'
      f'rio@github.dev  -  <tspan fill="{p["cyn"]}">%</tspan>  ./projects.sh --all</text>')
    # header label
    a(f'<text x="{PAD}" y="{TITLE_H + PAD}" font-size="11" font-family="{FONT}" fill="{p["pur"]}" letter-spacing="2">PROJECTS.LIST</text>')

    top = TITLE_H + PAD + 18
    for i in range(3):
        for j in range(2):
            idx = i * 2 + j
            if idx >= len(repos):
                break
            x = PAD + j * (CARD_W + 14)
            y = top + i * (CARD_H + 14)
            s.extend(card(repos[idx], x, y, CARD_W, CARD_H, theme))
    s.extend(socials(top + grid_h + 18, theme, W))
    a("</svg>")
    return "\n".join(s)


def main():
    owner = sys.argv[1] if len(sys.argv) > 1 else OWNER
    token = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("GITHUB_TOKEN")
    repos = fetch_data(token)
    for theme in ("dark", "light"):
        svg = build(repos, theme)
        with open(f"projects-{theme}.svg", "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote projects-{theme}.svg with {len(repos)} repos, {len(svg)} bytes")


if __name__ == "__main__":
    main()
