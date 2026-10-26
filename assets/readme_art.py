"""Generate the animated README art: python3 assets/readme_art.py (writes the SVGs next to this file).

GitHub renders SVG images with their own CSS animations, so all motion lives here; the README
only places the images (light and dark variants through <picture>).
"""
from pathlib import Path

HERE = Path(__file__).parent
SANS = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
THEMES = {
    "light": {"bg": "#F6F3EA", "ink": "#15181A", "muted": "#6E726C", "faint": "#DDD8CB", "grid": "#ECE7DA",
              "accent": "#E5532D", "accent2": "#B93A18", "green": "#1F9D55", "panel": "#FFFDF7"},
    "dark": {"bg": "#0D1012", "ink": "#F3F0E7", "muted": "#9CA19B", "faint": "#2A3033", "grid": "#151A1C",
             "accent": "#FF6B3D", "accent2": "#C2441C", "green": "#3FD07A", "panel": "#12171A"},
}


def pct(t, total):
    return f"{max(0.0, min(100.0, t / total * 100)):.3f}%"


# Hero: wordmark, a plumb bob that is flicked, swings, settles true, and a rail of the five stages.

def hero(c):
    T = 9.0
    swing = [(0, 0), (0.45, 24), (1.25, -18), (2.05, 13), (2.85, -9), (3.6, 6), (4.3, -3.5), (4.95, 1.8),
             (5.55, -0.6), (6.1, 0)]
    frames = " ".join(f"{pct(t, T)} {{ transform: rotate({a}deg); }}" for t, a in swing)
    stages = ["triage", "plan", "build", "review", "reconcile"]
    rail_x0, rail_x1, rail_y = 72, 700, 470
    step = (rail_x1 - rail_x0) / (len(stages) - 1)
    R = 7.5  # rail loop seconds
    station_css, station_svg = [], []
    for i, name in enumerate(stages):
        x = rail_x0 + i * step
        at = 0.6 + i * 1.2
        station_css.append(
            f"@keyframes st{i} {{ 0%, {pct(at - 0.05, R)} {{ fill: {c['bg']}; }} {pct(at, R)}, 92% {{ fill: {c['accent']}; }} "
            f"100% {{ fill: {c['bg']}; }} }} .st{i} {{ animation: st{i} {R}s linear infinite; }}")
        station_svg.append(
            f'<circle class="st{i}" cx="{x:.1f}" cy="{rail_y}" r="7" stroke="{c["ink"]}" stroke-width="2"/>'
            f'<text x="{x:.1f}" y="{rail_y + 34}" text-anchor="middle" font-family="{MONO}" font-size="15" '
            f'letter-spacing="1.5" fill="{c["muted"]}">{name.upper()}</text>')
    travel = rail_x1 - rail_x0
    css = f"""
    .bob {{ transform-box: view-box; transform-origin: 1010px 92px; animation: swing {T}s infinite; }}
    @keyframes swing {{ {frames} 100% {{ transform: rotate(0deg); }} }}
    .bob {{ animation-timing-function: ease-in-out; }}
    .trueline {{ stroke-dasharray: 340; stroke-dashoffset: 340; animation: draw {T}s infinite; }}
    @keyframes draw {{ 0%, {pct(6.15, T)} {{ stroke-dashoffset: 340; opacity: 0; }} {pct(6.2, T)} {{ opacity: 1; }}
      {pct(6.9, T)}, {pct(8.6, T)} {{ stroke-dashoffset: 0; opacity: 1; }} 100% {{ stroke-dashoffset: 0; opacity: 0; }} }}
    .settled {{ animation: settled {T}s infinite; }}
    @keyframes settled {{ 0%, {pct(6.5, T)} {{ opacity: 0; }} {pct(6.9, T)}, {pct(8.6, T)} {{ opacity: 1; }} 100% {{ opacity: 0; }} }}
    .measuring {{ animation: measuring {T}s infinite; }}
    @keyframes measuring {{ 0%, {pct(6.3, T)} {{ opacity: 1; }} {pct(6.5, T)}, {pct(8.8, T)} {{ opacity: 0; }} 100% {{ opacity: 1; }} }}
    .target {{ animation: target {T}s infinite; transform-box: fill-box; transform-origin: center; }}
    @keyframes target {{ 0%, {pct(6.5, T)} {{ stroke: {c['faint']}; transform: scale(1); }}
      {pct(6.8, T)} {{ stroke: {c['green']}; transform: scale(1.35); }} {pct(7.2, T)}, {pct(8.6, T)} {{ stroke: {c['green']}; transform: scale(1); }}
      100% {{ stroke: {c['faint']}; }} }}
    .runner {{ animation: run {R}s cubic-bezier(.65,0,.35,1) infinite; }}
    @keyframes run {{ 0%, 6% {{ transform: translateX(0); opacity: 0; }} 8% {{ opacity: 1; }}
      70% {{ transform: translateX({travel}px); opacity: 1; }} 92% {{ transform: translateX({travel}px); opacity: 1; }}
      100% {{ transform: translateX({travel}px); opacity: 0; }} }}
    {' '.join(station_css)}
    """
    ticks = "".join(f'<line x1="{x}" y1="560" x2="{x}" y2="{568 if x % 50 else 574}" stroke="{c["faint"]}" stroke-width="1.5"/>'
                    for x in range(870, 1160, 10))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="600" viewBox="0 0 1280 600" role="img" aria-labelledby="t d">
  <title id="t">Plumb</title>
  <desc id="d">The Plumb wordmark. A plumb bob swings, settles, and a line marks it true. Below, a rail runs through triage, plan, build, review and reconcile.</desc>
  <defs>
    <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="{c['grid']}" stroke-width="1"/></pattern>
    <radialGradient id="glow" cx="1010" cy="330" r="260" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{c['accent']}" stop-opacity="0.16"/><stop offset="1" stop-color="{c['accent']}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="brass" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c['accent2']}"/><stop offset="0.45" stop-color="{c['accent']}"/><stop offset="0.6" stop-color="#FFB089"/>
      <stop offset="1" stop-color="{c['accent2']}"/>
    </linearGradient>
    <style>{css}</style>
  </defs>
  <rect width="1280" height="600" fill="{c['bg']}"/>
  <rect width="1280" height="600" fill="url(#grid)"/>
  <rect x="760" y="40" width="500" height="540" fill="url(#glow)"/>
  <text x="72" y="92" font-family="{MONO}" font-size="15" letter-spacing="2" fill="{c['muted']}">AGENT SKILLS · VERSIONED PLANS · CHECKED BUILDS</text>
  <text x="62" y="272" font-family="{SANS}" font-weight="900" font-size="212" letter-spacing="-10" fill="{c['ink']}">PLUMB<tspan fill="{c['accent']}">.</tspan></text>
  <text x="74" y="340" font-family="{SANS}" font-weight="600" font-size="34" letter-spacing="-0.5" fill="{c['ink']}">Agents that ask before they build,</text>
  <text x="74" y="384" font-family="{SANS}" font-weight="600" font-size="34" letter-spacing="-0.5" fill="{c['muted']}">and build what you agreed to.</text>
  <line x1="{rail_x0}" y1="{rail_y}" x2="{rail_x1}" y2="{rail_y}" stroke="{c['faint']}" stroke-width="2"/>
  {''.join(station_svg)}
  <circle class="runner" cx="{rail_x0}" cy="{rail_y}" r="5" fill="{c['accent']}"/>
  <path d="M 900 300 A 230 230 0 0 0 1120 300" fill="none" stroke="{c['faint']}" stroke-width="1.5" stroke-dasharray="3 7" transform="translate(0 40)"/>
  <rect x="940" y="72" width="140" height="10" rx="5" fill="{c['ink']}"/>
  <rect x="1003" y="82" width="14" height="14" rx="3" fill="{c['ink']}"/>
  <line class="trueline" x1="1010" y1="92" x2="1010" y2="430" stroke="{c['green']}" stroke-width="2"/>
  <g class="bob">
    <line x1="1010" y1="92" x2="1010" y2="318" stroke="{c['ink']}" stroke-width="2"/>
    <rect x="1001" y="314" width="18" height="10" rx="2" fill="{c['ink']}"/>
    <path d="M 982 324 L 1038 324 L 1038 340 C 1038 362 1022 380 1010 410 C 998 380 982 362 982 340 Z" fill="url(#brass)"/>
    <path d="M 1018 330 L 1030 330 L 1030 340 C 1030 352 1024 362 1018 372 Z" fill="#FFFFFF" opacity="0.25"/>
  </g>
  <circle class="target" cx="1010" cy="436" r="10" fill="none" stroke="{c['faint']}" stroke-width="2"/>
  <line x1="860" y1="560" x2="1160" y2="560" stroke="{c['faint']}" stroke-width="1.5"/>
  {ticks}
  <text class="measuring" x="1010" y="520" text-anchor="middle" font-family="{MONO}" font-size="16" fill="{c['muted']}">settling…</text>
  <text class="settled" x="1010" y="520" text-anchor="middle" font-family="{MONO}" font-size="16" font-weight="700" fill="{c['green']}">0.00° · true</text>
</svg>
"""


# Session: an illustrative terminal run, typed out and looped. Every line maps to a real step.

def session():
    ink, muted, dim, acc, green, blue = "#ECE9E1", "#8E948F", "#5D6360", "#FF6B3D", "#3FD07A", "#7AA8FF"
    T, cw, lh, x0, y0 = 24.0, 9.03, 27, 36, 92
    lines = [  # (kind, at seconds, spans); kind cmd and you are typed
        ("cmd", 0.5, [(acc, "❯ "), (ink, "/plumb-triage "), (muted, "add a CSV export for the filtered orders table")]),
        ("out", 3.0, [(muted, "  What I found")]),
        ("out", 3.3, [(dim, "    web  "), (ink, "TypeScript · vitest   "), (muted, "pnpm test      "), (green, "✓ baseline green")]),
        ("out", 3.6, [(dim, "    api  "), (ink, "Go · go test          "), (muted, "go test ./...  "), (green, "✓ baseline green")]),
        ("out", 4.2, [(muted, "  Track  "), (ink, "standard"), (muted, " · a new endpoint and a new button")]),
        ("gap", 0, []),
        ("cmd", 5.2, [(acc, "❯ "), (ink, "/plumb-plan "), (muted, "csv-export")]),
        ("out", 6.6, [(muted, "  We're making  "), (ink, "a CSV of exactly what the table shows")]),
        ("out", 7.2, [(acc, "  1  "), (ink, "An admin hides the Price column, then exports.")]),
        ("out", 7.5, [(dim, "       "), (acc, "A ★ "), (ink, "the file leaves Price out     "), (muted, "B  every column")]),
        ("out", 8.0, [(acc, "  2  "), (ink, "Someone edits an order during the export.")]),
        ("out", 8.3, [(dim, "       "), (acc, "A ★ "), (ink, "rows as they were loaded      "), (muted, "B  re-read each row")]),
        ("you", 9.3, [(blue, "  you › "), (ink, "1A 2A")]),
        ("out", 10.6, [(green, "  ✓ plan approved"), (muted, " · 4 documents · bound by hash")]),
        ("gap", 0, []),
        ("cmd", 11.6, [(acc, "❯ "), (ink, "/plumb-build "), (muted, "csv-export")]),
        ("bar", 12.9, [(muted, "  slice 01  "), (ink, "export endpoint ")]),
        ("bar", 14.7, [(muted, "  slice 02  "), (ink, "export button   ")]),
        ("out", 16.7, [(muted, "  review    "), (ink, "0 blocking"), (muted, " · "), (ink, "5/5"), (muted, " examples pass on the running app")]),
        ("out", 17.5, [(green, "  ✓ ready for your sign-off")]),
        ("end", 18.3, [(acc, "❯ ")]),
    ]
    css, body = [
        f".line {{ opacity: 0; }}",
        f"@keyframes blink {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}",
        f".blink {{ animation: blink 1s steps(1) infinite; }}",
    ], []
    y = y0
    for n, (kind, at, spans) in enumerate(lines):
        if kind == "gap":
            y += lh // 2
            continue
        appear = at if kind in ("out", "bar", "end") else at
        css.append(
            f"@keyframes l{n} {{ 0%, {pct(appear, T)} {{ opacity: 0; transform: translateY(6px); }} "
            f"{pct(appear + 0.25, T)}, 95% {{ opacity: 1; transform: translateY(0); }} 98%, 100% {{ opacity: 0; }} }} "
            f".l{n} {{ animation: l{n} {T}s ease-out infinite; }}" if kind in ("out", "bar", "end") else
            f"@keyframes l{n} {{ 0%, {pct(appear - 0.01, T)} {{ opacity: 0; }} {pct(appear, T)}, 95% {{ opacity: 1; }} 98%, 100% {{ opacity: 0; }} }} "
            f".l{n} {{ animation: l{n} {T}s linear infinite; }}")
        tspans = "".join(f'<tspan fill="{color}">{text.replace("&", "&amp;").replace("<", "&lt;")}</tspan>' for color, text in spans)
        parts = [f'<text x="{x0}" y="{y}" xml:space="preserve">{tspans}</text>']
        if kind in ("cmd", "you"):
            prefix = len(spans[0][1])
            typed = sum(len(s[1]) for s in spans) - prefix
            speed = 30 if kind == "cmd" else 7
            done = at + typed / speed
            start_x = x0 + prefix * cw
            width = typed * cw + 14
            css.append(
                f"@keyframes c{n} {{ 0%, {pct(at, T)} {{ transform: translateX(0); }} {pct(done, T)}, 100% {{ transform: translateX({width - 14 + 2:.1f}px); }} }} "
                f".c{n} {{ animation: c{n} {T}s infinite; }} .c{n} {{ animation-timing-function: steps({typed}, end); }} "
                f"@keyframes k{n} {{ 0%, {pct(done + 0.15, T)} {{ opacity: 1; }} {pct(done + 0.2, T)}, 100% {{ opacity: 0; }} }} "
                f".k{n} {{ animation: k{n} {T}s linear infinite; }}")
            parts.append(f'<g class="c{n}"><rect x="{start_x:.1f}" y="{y - 19}" width="{width + 900:.1f}" height="{lh}" fill="#0B0E10"/>'
                         f'<g class="k{n}"><rect class="blink" x="{start_x:.1f}" y="{y - 17}" width="9" height="20" fill="{acc}"/></g></g>')
        if kind == "bar":
            bx = x0 + 28 * cw
            fill_at = at + 0.3
            css.append(
                f"@keyframes b{n} {{ 0%, {pct(fill_at, T)} {{ transform: scaleX(0); }} {pct(fill_at + 1.3, T)}, 100% {{ transform: scaleX(1); }} }} "
                f".b{n} {{ transform-box: fill-box; transform-origin: left; animation: b{n} {T}s ease-in-out infinite; }} "
                f"@keyframes g{n} {{ 0%, {pct(fill_at + 1.35, T)} {{ opacity: 0; }} {pct(fill_at + 1.5, T)}, 100% {{ opacity: 1; }} }} "
                f".g{n} {{ animation: g{n} {T}s linear infinite; }}")
            parts.append(f'<rect x="{bx:.1f}" y="{y - 13}" width="150" height="10" rx="5" fill="#1E2427"/>'
                         f'<rect class="b{n}" x="{bx:.1f}" y="{y - 13}" width="150" height="10" rx="5" fill="{green}"/>'
                         f'<text class="g{n}" x="{bx + 168:.1f}" y="{y}" xml:space="preserve"><tspan fill="#FF8A80">red</tspan>'
                         f'<tspan fill="{muted}"> → </tspan><tspan fill="{green}">green  ✓</tspan></text>')
        if kind == "end":
            parts.append(f'<rect class="blink" x="{x0 + 2 * cw:.1f}" y="{y - 17}" width="9" height="20" fill="{acc}"/>')
        body.append(f'<g class="line l{n}">{"".join(parts)}</g>')
        y += lh
    height = y + 30
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}" role="img" aria-labelledby="t d">
  <title id="t">An illustrative Plumb session</title>
  <desc id="d">Triage finds the modules and picks the standard track. The plan asks two scenario questions with recommended answers, the user replies 1A 2A, and the plan is approved. Build turns two slices from red to green, review finds nothing blocking, and five of five examples pass on the running app.</desc>
  <defs>
    <clipPath id="card"><rect x="8" y="8" width="984" height="{height - 16}" rx="16"/></clipPath>
    <style>{' '.join(css)}</style>
  </defs>
  <g clip-path="url(#card)">
    <rect x="8" y="8" width="984" height="{height - 16}" fill="#0B0E10"/>
    <rect x="8" y="8" width="984" height="44" fill="#13181B"/>
    <circle cx="34" cy="30" r="6.5" fill="#FF5F57"/><circle cx="56" cy="30" r="6.5" fill="#FEBC2E"/><circle cx="78" cy="30" r="6.5" fill="#28C840"/>
    <text x="500" y="35" text-anchor="middle" font-family="{MONO}" font-size="13" fill="#6F7672">~/shop-admin · plumb</text>
    <g font-family="{MONO}" font-size="15">{''.join(body)}</g>
  </g>
  <rect x="8.5" y="8.5" width="983" height="{height - 17}" rx="16" fill="none" stroke="#263035"/>
</svg>
"""


# Scoreboard: the published benchmark and where it lost, bars growing on load.

def scoreboard(c):
    css, body = [], []

    def bar(n, x, y, value, total, width, color, delay, label=None):
        w = width * value / total
        css.append(f"@keyframes s{n} {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }} "
                   f".s{n} {{ transform-box: fill-box; transform-origin: left; animation: s{n} 1.1s cubic-bezier(.2,.8,.2,1) {delay}s both; }} "
                   f"@keyframes v{n} {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }} .v{n} {{ animation: v{n} .4s ease-out {delay + 0.9}s both; }}")
        body.append(f'<rect x="{x}" y="{y}" width="{width}" height="22" rx="6" fill="{c["grid"]}"/>'
                    f'<rect class="s{n}" x="{x}" y="{y}" width="{w:.1f}" height="22" rx="6" fill="{color}"/>'
                    f'<text class="v{n}" x="{x + width + 12:.1f}" y="{y + 17}" font-family="{MONO}" font-size="15" font-weight="700" fill="{c["ink"]}">{label or f"{value}/{total}"}</text>')

    arms = [("Bare agent", 14, c["muted"]), ("Agent + good CLAUDE.md", 14, c["muted"]), ("Plumb, sequential", 9, c["accent"])]
    body.append(f'<text x="48" y="138" font-family="{MONO}" font-size="13" letter-spacing="1.5" fill="{c["muted"]}">ACCEPTED, ALL 20 TASKS</text>')
    for i, (name, value, color) in enumerate(arms):
        y = 162 + i * 62
        body.append(f'<text x="48" y="{y}" font-family="{SANS}" font-size="16" font-weight="600" fill="{c["ink"]}">{name}</text>')
        bar(i, 48, y + 10, value, 20, 360, color, 0.2 + i * 0.25)
    body.append(f'<line x1="530" y1="120" x2="530" y2="352" stroke="{c["faint"]}" stroke-width="1.5"/>')
    groups = [("Critical track, 9", [5, 5, 2], 9), ("The other 11", [9, 9, 10], 11)]
    for g, (title, values, total) in enumerate(groups):
        gx = 578 + g * 222
        body.append(f'<text x="{gx}" y="138" font-family="{MONO}" font-size="13" letter-spacing="1.5" fill="{c["muted"]}">{title.upper()}</text>')
        for i, value in enumerate(values):
            y = 162 + i * 62
            body.append(f'<text x="{gx}" y="{y}" font-family="{SANS}" font-size="14" fill="{c["muted"]}">{["Bare", "CLAUDE.md", "Plumb"][i]}</text>')
            bar(10 + g * 3 + i, gx, y + 10, value, total, 128, c["accent"] if i == 2 else c["muted"], 1.2 + g * 0.5 + i * 0.15)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="420" viewBox="0 0 1040 420" role="img" aria-labelledby="t d">
  <title id="t">Benchmark scoreboard</title>
  <desc id="d">On 20 real merged pull requests, blind review accepted 14 for a bare agent, 14 for an agent with a good CLAUDE.md, and 9 for sequential Plumb. On the 9 critical-track tasks: 5, 5 and 2. On the other 11: 9, 9 and 10.</desc>
  <defs><style>{' '.join(css)}</style></defs>
  <rect x="1" y="1" width="1038" height="418" rx="18" fill="{c['panel']}" stroke="{c['faint']}" stroke-width="1.5"/>
  <text x="48" y="62" font-family="{SANS}" font-size="26" font-weight="800" letter-spacing="-0.5" fill="{c['ink']}">20 real merged PRs. Blind review. Three arms.</text>
  <text x="48" y="92" font-family="{SANS}" font-size="16" fill="{c['muted']}">We publish where we lose: the critical track timed out on 8 of 9 tasks. Outside it, Plumb led on quality, 6–7× slower.</text>
  {''.join(body)}
  <text x="48" y="394" font-family="{MONO}" font-size="12.5" fill="{c['muted']}">Measured 2026-10-19 on the sequential workflow, before the rename. A rerun on 20 new PRs is planned.</text>
</svg>
"""


if __name__ == "__main__":
    for name, theme in THEMES.items():
        (HERE / f"hero-{name}.svg").write_text(hero(theme))
        (HERE / f"scoreboard-{name}.svg").write_text(scoreboard(theme))
    (HERE / "session.svg").write_text(session())
    print("wrote hero, scoreboard (light, dark) and session")
