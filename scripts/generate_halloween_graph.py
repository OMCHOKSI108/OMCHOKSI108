#!/usr/bin/env python3
"""Generate dynamic GitHub Halloween contribution graph SVG for OMCHOKSI108."""

import os
import sys
import json
import urllib.request
import subprocess
from pathlib import Path


def fetch_contributions(username: str = "OMCHOKSI108") -> dict:
    query = f"""
    query {{
      user(login: "{username}") {{
        contributionsCollection {{
          contributionCalendar {{
            totalContributions
            weeks {{
              contributionDays {{
                date
                contributionCount
                weekday
              }}
            }}
          }}
        }}
      }}
    }}"""

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": query}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "Halloween-Graph-Generator",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    else:
        res = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}"], capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)

    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def get_color(count: int) -> str:
    if count == 0:
        return "#161b22"
    elif count < 4:
        return "#FDF156"
    elif count < 10:
        return "#FFC722"
    elif count < 20:
        return "#FF9711"
    else:
        return "#04001B"


def get_border(count: int) -> str:
    if count >= 20:
        return 'stroke="#FF9711" stroke-width="1"'
    return ""


def build_svg(cal: dict) -> str:
    total = cal["totalContributions"]
    weeks = cal["weeks"]

    cell_size = 11
    cell_gap = 4
    step = cell_size + cell_gap
    offset_x = 40
    offset_y = 65
    width = offset_x + len(weeks) * step + 20
    height = offset_y + 7 * step + 50

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="background-color: #0d1117; border: 1px solid #30363d; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif;">',
        '<style>',
        '  .title { fill: #c9d1d9; font-size: 15px; font-weight: 600; }',
        '  .subtitle { fill: #8b949e; font-size: 12px; }',
        '  .spooky { fill: #FF9711; font-weight: 600; }',
        '  .label { fill: #8b949e; font-size: 10px; }',
        '  .day-label { fill: #8b949e; font-size: 9px; }',
        '  rect.day:hover { stroke: #ffffff; stroke-width: 1.5px; }',
        '</style>',
        f'<text x="20" y="28" class="title">Contributions in the last year: <tspan class="spooky">{total:,}</tspan> total</text>',
        f'<text x="20" y="46" class="subtitle">A <tspan class="spooky">spooky</tspan> summary of Pull Requests, issues opened, and commits 🎃</text>',
    ]

    # Weekday labels
    day_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for day_idx, label in day_labels.items():
        y = offset_y + day_idx * step + 9
        svg_parts.append(f'<text x="12" y="{y}" class="day-label">{label}</text>')

    # Months
    months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    last_month = None
    for w_idx, week in enumerate(weeks):
        first_day = week["contributionDays"][0] if week["contributionDays"] else None
        if first_day:
            m = int(first_day["date"].split("-")[1])
            if m != last_month and w_idx < len(weeks) - 2:
                x = offset_x + w_idx * step
                svg_parts.append(f'<text x="{x}" y="{offset_y - 8}" class="label">{months[m]}</text>')
                last_month = m

    # Contribution Grid
    for w_idx, week in enumerate(weeks):
        for day in week["contributionDays"]:
            x = offset_x + w_idx * step
            y = offset_y + day["weekday"] * step
            c = get_color(day["contributionCount"])
            border = get_border(day["contributionCount"])
            cnt = day["contributionCount"]
            dt = day["date"]
            unit = "contribution" if cnt == 1 else "contributions"
            svg_parts.append(
                f'<rect class="day" x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="2" ry="2" fill="{c}" {border}>'
                f'<title>{dt}: {cnt} {unit}</title></rect>'
            )

    # Legend
    leg_y = height - 20
    leg_x = width - 150
    svg_parts.append(f'<text x="{leg_x - 30}" y="{leg_y + 9}" class="label">Less</text>')
    legend_colors = ["#161b22", "#FDF156", "#FFC722", "#FF9711", "#04001B"]
    for i, lc in enumerate(legend_colors):
        bx = leg_x + i * (cell_size + 3)
        extra_b = 'stroke="#FF9711" stroke-width="1"' if lc == "#04001B" else ""
        svg_parts.append(f'<rect x="{bx}" y="{leg_y}" width="{cell_size}" height="{cell_size}" rx="2" ry="2" fill="{lc}" {extra_b} />')
    svg_parts.append(f'<text x="{leg_x + len(legend_colors)*(cell_size+3) + 6}" y="{leg_y + 9}" class="label">More</text>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def main():
    root = Path(__file__).resolve().parents[1]
    output_path = root / "assets" / "github-contribution-halloween.svg"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching live contributions for OMCHOKSI108...")
    cal = fetch_contributions("OMCHOKSI108")
    svg_content = build_svg(cal)

    output_path.write_text(svg_content, encoding="utf-8")
    print(f"Generated {output_path} ({len(svg_content)} bytes)")


if __name__ == "__main__":
    main()
