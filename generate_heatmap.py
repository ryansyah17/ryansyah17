#!/usr/bin/env python3
"""
Generate an animated GitHub contribution heatmap as an SVG (no dependencies).

    python scripts/generate_heatmap.py --user ryansyah17 --out contrib-heatmap.svg
    python scripts/generate_heatmap.py --demo --out contrib-heatmap.svg   # fake data, offline

Data source:
  * GH_TOKEN / GITHUB_TOKEN set  -> GitHub GraphQL API (used by the GitHub Action)
  * no token                      -> public profile calendar (handy for running locally)
"""
import argparse
import datetime as dt
import json
import os
import random
import re
import urllib.request

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

# ---- look & feel ------------------------------------------------------------
CELL, GAP = 11, 3
STEP = CELL + GAP
LEFT, TOP_HEADER, TOP_GRID = 40, 78, 100
LEVEL_COLORS = ["#161b22", "#0e4a5c", "#1a7a94", "#2fa8c9", "#5BCDEC"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fetch_days(login, token):
    today = dt.datetime.now(dt.timezone.utc)
    start = today - dt.timedelta(days=365)
    payload = json.dumps({
        "query": QUERY,
        "variables": {
            "login": login,
            "from": start.strftime("%Y-%m-%dT00:00:00Z"),
            "to": today.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-heatmap"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "errors" in data or not data.get("data", {}).get("user"):
        raise SystemExit(f"GitHub API error: {data.get('errors') or 'user not found'}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [(dt.date.fromisoformat(d["date"]), d["contributionCount"])
            for w in weeks for d in w["contributionDays"]]


def fetch_days_public(login):
    """Read the public contribution calendar (no token needed)."""
    req = urllib.request.Request(
        f"https://github.com/users/{login}/contributions",
        headers={"User-Agent": "Mozilla/5.0 (profile-heatmap)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", "replace")
    cells = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"\s+id="([^"]+)"', html)
    tips = dict(re.findall(r'for="(contribution-day-component-[^"]+)"[^>]*>\s*([^<]+?)\s*<', html))
    if not cells:
        raise SystemExit("Could not read the public contribution calendar.")
    days = []
    for date, cid in cells:
        m = re.match(r"(\d+) contributions? on", tips.get(cid, ""))
        days.append((dt.date.fromisoformat(date), int(m.group(1)) if m else 0))
    return sorted(days)


def demo_days():
    rng = random.Random(7)
    end = dt.date.today()
    days = []
    for i in range(364, -1, -1):
        d = end - dt.timedelta(days=i)
        busy = rng.random() < (0.35 if d.weekday() >= 5 else 0.7)
        days.append((d, rng.choice([1, 2, 3, 5, 8, 12]) if busy else 0))
    return days


def stats(days):
    counts = [c for _, c in days]
    total = sum(counts)
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    seq = counts[:]
    if seq and seq[-1] == 0:          # today not committed yet -> streak still alive
        seq = seq[:-1]
    current = 0
    for c in reversed(seq):
        if not c:
            break
        current += 1
    return total, current, longest, max(counts, default=0)


def level(count, peak):
    if count == 0 or peak == 0:
        return 0
    r = count / peak
    return 1 if r <= .25 else 2 if r <= .5 else 3 if r <= .75 else 4


def render(login, days, demo=False):
    first = days[0][0]
    grid_start = first - dt.timedelta(days=(first.weekday() + 1) % 7)   # weeks start on Sunday
    weeks = (days[-1][0] - grid_start).days // 7 + 1
    width = LEFT + weeks * STEP + 24
    height = TOP_GRID + 7 * STEP + 52
    total, current, longest, best = stats(days)
    peak = max(c for _, c in days)

    cells, month_labels, last_label_x = [], [], -99
    for d, c in days:
        offset = (d - grid_start).days
        col, row = offset // 7, offset % 7
        x, y = LEFT + col * STEP, TOP_GRID + row * STEP
        lv = level(c, peak)
        is_last = d == days[-1][0]
        cls = ' class="today"' if is_last else ""
        cells.append(
            f'<rect{cls} x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{LEVEL_COLORS[lv]}" '
            f'style="animation-delay:{col * 0.03:.2f}s"><title>{c} contributions on {d.isoformat()}</title></rect>'
        )
        if row == 0 and d.day <= 7 and x - last_label_x > 34:
            month_labels.append(f'<text x="{x}" y="{TOP_GRID - 8}" class="dim">{MONTHS[d.month - 1]}</text>')
            last_label_x = x

    day_labels = "".join(
        f'<text x="{LEFT - 8}" y="{TOP_GRID + r * STEP + 9}" class="dim" text-anchor="end">{n}</text>'
        for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )
    legend_x = width - 24 - (5 * STEP) - 58
    legend = "".join(
        f'<rect x="{legend_x + 30 + i * STEP}" y="{height - 30}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>'
        for i, c in enumerate(LEVEL_COLORS)
    )
    stamp = "sample data" if demo else "updated " + dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d UTC")
    blocks = [("CONTRIBUTIONS", f"{total:,}", "last 12 months"),
              ("CURRENT STREAK", f"{current}", "days"),
              ("LONGEST STREAK", f"{longest}", "days"),
              ("BEST DAY", f"{best}", "contributions")]
    stat_svg = "".join(
        f'<g class="stat" style="animation-delay:{0.15 * i:.2f}s">'
        f'<text x="{LEFT + i * 170}" y="46" class="label">{label}</text>'
        f'<text x="{LEFT + i * 170}" y="68" class="big">{value}<tspan class="dim unit" dx="6">{unit}</tspan></text></g>'
        for i, (label, value, unit) in enumerate(blocks)
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{login} GitHub contribution heatmap">
  <title>{login} - contributions in the last 12 months</title>
  <style>
    text {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace; }}
    .dim {{ fill: #8b949e; font-size: 10px; }}
    .label {{ fill: #8b949e; font-size: 10px; letter-spacing: 1.2px; }}
    .big {{ fill: #5BCDEC; font-size: 22px; font-weight: 700; }}
    .unit {{ font-size: 11px; font-weight: 400; }}
    .prompt {{ fill: #3fb950; font-size: 11px; }}
    rect[style] {{ animation: pop .45s ease-out both; }}
    .stat {{ animation: rise .6s ease-out both; }}
    .today {{ animation: pop .45s ease-out both, pulse 2s ease-in-out 1.8s infinite; stroke: #5BCDEC; stroke-width: 1; }}
    @keyframes pop {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .35; }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>
  <rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="12" fill="#0d1117" stroke="#30363d"/>
  <text x="{LEFT}" y="24" class="prompt">$ gh contributions --user {login}</text>
  {stat_svg}
  {day_labels}
  {"".join(month_labels)}
  {"".join(cells)}
  <text x="{LEFT}" y="{height - 21}" class="dim">{stamp}</text>
  <text x="{legend_x}" y="{height - 21}" class="dim">Less</text>
  {legend}
  <text x="{legend_x + 30 + 5 * STEP + 4}" y="{height - 21}" class="dim">More</text>
</svg>
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "ryansyah17"))
    ap.add_argument("--out", default="contrib-heatmap.svg")
    ap.add_argument("--demo", action="store_true", help="use fake data (offline preview)")
    args = ap.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if args.demo:
        days = demo_days()
    elif token:
        days = fetch_days(args.user, token)
    else:
        print("No token found - reading the public profile calendar instead.")
        days = fetch_days_public(args.user)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(render(args.user, days, demo=args.demo))
    print(f"wrote {args.out} ({len(days)} days)")


if __name__ == "__main__":
    main()
