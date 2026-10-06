#!/usr/bin/env python3
"""
Build info-card.svg (animated terminal-style card). Edit CONFIG, then run:

    python scripts/build_info_card.py
"""
from html import escape

CONFIG = {
    "prompt_user": "ryansyah@putra",
    "name": "Ryansyah Putra",
    "role": "Mobile & Web Developer",
    "location": "West Sumatera, Indonesia",
    "focus": "Flutter · Laravel · UI design",
    "stack": [  # (label, dot color)
        ("Dart", "#0175C2"), ("Flutter", "#54C5F8"), ("Laravel", "#FF2D20"),
        ("PHP", "#777BB4"), ("Java", "#ED8B00"), ("HTML", "#E34F26"),
        ("MySQL", "#4479A1"), ("Figma", "#F24E1E"), ("VS Code", "#0078D4"),
    ],
    "highlights": [
        "10+ client projects delivered",
        "Cross-platform apps with Flutter & Dart",
        "Web systems with Laravel & MySQL",
        "Design in Figma, build in code",
    ],
    "out": "info-card.svg",
}

W, H = 480, 440
PAD = 24
CHAR = 6.6          # approx. glyph width of the 11px monospace font
LH = 20             # line height


def build(c):
    out, y, i = [], 74, 0

    def delay():
        nonlocal i
        i += 1
        return f'style="animation-delay:{i * 0.28:.2f}s"'

    def prompt(cmd):
        nonlocal y
        out.append(f'<text x="{PAD}" y="{y}" class="ln" {delay()}><tspan class="g">$</tspan> <tspan class="cmd">{escape(cmd)}</tspan></text>')
        y += LH

    def kv(key, val):
        nonlocal y
        out.append(
            f'<g class="ln" {delay()}><text x="{PAD + 14}" y="{y}" class="dim">{key}</text>'
            f'<text x="{PAD + 14 + 62}" y="{y}" class="val">{escape(val)}</text></g>'
        )
        y += LH

    prompt("whoami")
    out.append(f'<text x="{PAD + 14}" y="{y + 4}" class="name ln" {delay()}>{escape(c["name"])}</text>')
    y += LH + 12

    prompt("cat profile.txt")
    kv("role", c["role"])
    kv("based", c["location"])
    kv("focus", c["focus"])
    y += 8

    prompt("ls ./stack")
    x, row_y = PAD + 14, y + 2
    for label, color in c["stack"]:
        w = len(label) * CHAR + 30
        if x + w > W - PAD:
            x, row_y = PAD + 14, row_y + 26
        out.append(
            f'<g class="chip" {delay()}><rect x="{x}" y="{row_y - 12}" width="{w:.1f}" height="20" rx="10" '
            f'fill="#161b22" stroke="#30363d"/><circle cx="{x + 11}" cy="{row_y - 2}" r="3.5" fill="{color}"/>'
            f'<text x="{x + 20}" y="{row_y + 2}" class="chiptxt">{escape(label)}</text></g>'
        )
        x += w + 6
    y = row_y + 30

    prompt("cat highlights.md")
    for item in c["highlights"]:
        out.append(f'<text x="{PAD + 14}" y="{y}" class="ln" {delay()}><tspan class="acc">▸</tspan> <tspan class="val">{escape(item)}</tspan></text>')
        y += LH
    y += 6
    out.append(f'<text x="{PAD}" y="{y}" class="ln" {delay()}><tspan class="g">$</tspan> <tspan class="cursor">█</tspan></text>')

    body = "\n  ".join(out)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(c["name"])} - role, stack and highlights">
  <title>{escape(c["name"])} - role, stack and highlights</title>
  <style>
    text {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace; font-size: 12px; fill: #c9d1d9; }}
    .dim {{ fill: #8b949e; }}  .g {{ fill: #3fb950; }}  .acc {{ fill: #5BCDEC; }}
    .cmd {{ fill: #e6edf3; }}  .val {{ fill: #c9d1d9; }}
    .name {{ font-size: 24px; font-weight: 700; fill: #5BCDEC; }}
    .chiptxt {{ font-size: 11px; fill: #c9d1d9; }}
    .cursor {{ fill: #5BCDEC; animation: blink 1s steps(1) infinite; }}
    .ln, .chip {{ animation: lineIn .45s ease-out both; }}
    @keyframes lineIn {{ from {{ opacity: 0; transform: translateX(-6px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="#0d1117" stroke="#30363d"/>
  <path d="M.5 12.5a12 12 0 0 1 12-12h{W - 25}a12 12 0 0 1 12 12V34H.5z" fill="#161b22"/>
  <line x1=".5" y1="34.5" x2="{W - .5}" y2="34.5" stroke="#30363d"/>
  <circle cx="22" cy="18" r="5.5" fill="#ff5f56"/><circle cx="42" cy="18" r="5.5" fill="#ffbd2e"/><circle cx="62" cy="18" r="5.5" fill="#27c93f"/>
  <text x="{W / 2}" y="22" text-anchor="middle" class="dim" style="font-size:11px">{escape(c["prompt_user"])}: ~</text>
  {body}
</svg>
'''


if __name__ == "__main__":
    svg = build(CONFIG)
    with open(CONFIG["out"], "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", CONFIG["out"])
