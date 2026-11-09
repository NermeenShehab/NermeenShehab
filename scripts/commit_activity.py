"""Generate a GitHub-contribution-graph-style 'Commit activity per quarter' heatmap (light + dark SVG).

Data: monthly counts taken from GitHub's own contribution activity for @NermeenShehab
  - commits  = "Created N commits in M repositories" (commits GitHub attributes to the account,
               including private repositories the account can access; each commit counted once)
  - private  = "N contributions in private repositories" (GitHub reports these only as a total,
               without saying whether they are commits, PRs or reviews, so they are NOT counted as commits)

Usage: python scripts/commit_activity.py scripts/commits-monthly.csv assets
CSV rows: YYYY-MM,commits,private  (update the CSV from your GitHub contribution activity, then re-run;
set AS_OF below to the date you collected the data)
"""
import csv
import sys
from collections import OrderedDict
from xml.sax.saxutils import escape

SRC, OUT = sys.argv[1], sys.argv[2]
AS_OF = "Nov 9, 2026"
LEVELS = [0, 1, 25, 75, 150]          # commits per quarter -> colour level 0..4

THEMES = {  # GitHub's own contribution-graph palettes
    "light": dict(text="#1f2328", muted="#59636e", border="#d1d9e0",
                  lv=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
                  on=["#59636e", "#1f2328", "#1f2328", "#ffffff", "#ffffff"]),
    "dark": dict(text="#f0f6fc", muted="#9198a1", border="#3d444d",
                 lv=["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"],
                 on=["#9198a1", "#f0f6fc", "#f0f6fc", "#ffffff", "#0d1117"]),
}

# ---- aggregate months -> quarters ----------------------------------------------------------
quarters = OrderedDict()
with open(SRC) as f:
    for ym, c, p in csv.reader(f):
        y, m = ym.split("-")
        q = quarters.setdefault((int(y), (int(m) - 1) // 3 + 1), [0, 0])
        q[0] += int(c)
        q[1] += int(p)

years = sorted({y for y, _ in quarters})
last = max(quarters)                                   # the (partial) current quarter
total_c = sum(v[0] for v in quarters.values())
total_p = sum(v[1] for v in quarters.values())


def level(c):
    return max(i for i, t in enumerate(LEVELS) if c >= t)


# ---- layout ---------------------------------------------------------------------------------
W = 880
L, TOP = 64, 92                 # left label column, top of grid
GAP, CH = 6, 40                 # gap between cells, cell height
TOTW = 96                       # yearly total column
CW = (W - L - 16 - TOTW - GAP * 4) / 4
H = TOP + len(years) * (CH + GAP) + 44


def svg(theme):
    t = THEMES[theme]
    o = []
    a = o.append
    title = "Commit activity per quarter"
    desc = (f"Heatmap of quarterly commits for GitHub user NermeenShehab, {years[0]} to {years[-1]} "
            f"(as of {AS_OF}): {total_c} commits in total. Cells also note {total_p} contributions in private "
            f"repositories that GitHub reports without a type; these are not counted as commits. "
            f"Source: GitHub contribution activity.")
    a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" '
      f'aria-labelledby="t d" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',\'Noto Sans\',Helvetica,Arial,sans-serif">')
    a(f'<title id="t">{title}</title><desc id="d">{escape(desc)}</desc>')
    a(f'<text x="{L}" y="28" font-size="15" font-weight="600" fill="{t["text"]}">{total_c} commits '
      f'<tspan font-weight="400" fill="{t["muted"]}">from {years[0]} to {AS_OF}</tspan></text>')
    a(f'<text x="{L}" y="48" font-size="11.5" fill="{t["muted"]}">Source: GitHub contribution activity · '
      f'each commit counted once · includes private repositories</text>')
    # column headers
    for qi in range(4):
        cx = L + qi * (CW + GAP) + CW / 2
        a(f'<text x="{cx:.1f}" y="{TOP - 10}" font-size="11.5" text-anchor="middle" fill="{t["muted"]}">Q{qi + 1}</text>')
    tx = L + 4 * (CW + GAP) + TOTW / 2
    a(f'<text x="{tx:.1f}" y="{TOP - 10}" font-size="11.5" text-anchor="middle" fill="{t["muted"]}">Total</text>')
    # rows
    for ri, yr in enumerate(years):
        y0 = TOP + ri * (CH + GAP)
        a(f'<text x="{L - 12}" y="{y0 + CH / 2 + 4:.1f}" font-size="12" font-weight="600" text-anchor="end" '
          f'fill="{t["text"]}">{yr}</text>')
        yc = 0
        for qi in range(4):
            key = (yr, qi + 1)
            x0 = L + qi * (CW + GAP)
            if key not in quarters:                       # future quarter: outline only
                a(f'<rect x="{x0:.1f}" y="{y0}" width="{CW:.1f}" height="{CH}" rx="6" fill="none" '
                  f'stroke="{t["border"]}" stroke-dasharray="3 3"/>')
                continue
            c, p = quarters[key]
            yc += c
            lv = level(c)
            partial = key == last
            tip = f"Q{qi + 1} {yr}: {c} commit{'s' if c != 1 else ''}"
            if p:
                tip += f"; plus {p} private-repo contributions (type not reported)"
            if partial:
                tip += f" (partial quarter, to {AS_OF})"
            a(f'<g><title>{escape(tip)}</title>')
            a(f'<rect x="{x0:.1f}" y="{y0}" width="{CW:.1f}" height="{CH}" rx="6" fill="{t["lv"][lv]}" '
              f'stroke="{t["border"]}" stroke-opacity="0.35"/>')
            label = f"{c}{'*' if partial else ''}"
            if p:
                a(f'<text x="{x0 + 14:.1f}" y="{y0 + CH / 2 + 5:.1f}" font-size="14" font-weight="600" '
                  f'fill="{t["on"][lv]}">{label}</text>')
                a(f'<text x="{x0 + CW - 12:.1f}" y="{y0 + CH / 2 + 4:.1f}" font-size="10.5" text-anchor="end" '
                  f'fill="{t["on"][lv]}" fill-opacity="0.85">+{p} private</text>')
            else:
                a(f'<text x="{x0 + CW / 2:.1f}" y="{y0 + CH / 2 + 5:.1f}" font-size="14" font-weight="600" '
                  f'text-anchor="middle" fill="{t["on"][lv]}">{label}</text>')
            a('</g>')
        a(f'<text x="{tx:.1f}" y="{y0 + CH / 2 + 5:.1f}" font-size="13" font-weight="600" text-anchor="middle" '
          f'fill="{t["text"]}">{yc}</text>')
    # legend + footnote
    ly = H - 22
    a(f'<text x="{L}" y="{ly + 4}" font-size="10.5" fill="{t["muted"]}">* Partial quarter · '
      f'"+N private" = private-repo contributions GitHub reports without a type (not counted as commits)</text>')
    lx = W - 16 - 5 * 15 - 70
    a(f'<text x="{lx}" y="{ly + 4}" font-size="10.5" fill="{t["muted"]}">Less</text>')
    for i, col in enumerate(t["lv"]):
        a(f'<rect x="{lx + 30 + i * 15}" y="{ly - 6}" width="11" height="11" rx="2" fill="{col}" '
          f'stroke="{t["border"]}" stroke-opacity="0.35"/>')
    a(f'<text x="{lx + 30 + 5 * 15 + 4}" y="{ly + 4}" font-size="10.5" fill="{t["muted"]}">More</text>')
    a('</svg>')
    return "".join(o)


for th in THEMES:
    with open(f"{OUT}/commit-activity-{th}.svg", "w") as f:
        f.write(svg(th))
print("years:", years, "total commits:", total_c, "private contributions:", total_p)
print({f"{y}": [quarters.get((y, q), ['-'])[0] for q in range(1, 5)] for y in years})
