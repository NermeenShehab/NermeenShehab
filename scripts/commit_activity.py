"""Generate GitHub-style 'Commit activity per quarter' SVGs (light + dark) for a profile README.

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

THEMES = {
    "light": dict(text="#1f2328", muted="#59636e", grid="#d1d9e0", commit="#2da44e", private="#aceebb",
                  partial="#2da44e"),
    "dark": dict(text="#f0f6fc", muted="#9198a1", grid="#3d444d", commit="#3fb950", private="#196c2e",
                 partial="#3fb950"),
}

# ---- aggregate months -> quarters -------------------------------------------------------
quarters = OrderedDict()
with open(SRC) as f:
    for ym, c, p in csv.reader(f):
        y, m = ym.split("-")
        key = (int(y), (int(m) - 1) // 3 + 1)
        q = quarters.setdefault(key, [0, 0])
        q[0] += int(c)
        q[1] += int(p)

keys = sorted(quarters)
first = next(k for k in keys if sum(quarters[k]))          # start at first quarter with activity
keys = [k for k in keys if k >= first]
data = [(y, q, *quarters[(y, q)]) for y, q in keys]
total_c = sum(d[2] for d in data)
total_p = sum(d[3] for d in data)
peak = max(d[2] + d[3] for d in data)
step = 100 if peak > 200 else 50
ymax = ((peak // step) + 1) * step

# ---- layout -------------------------------------------------------------------------------
W, H = 880, 330
L, R, T, B = 48, 16, 74, 62                                   # plot margins
pw, ph = W - L - R, H - T - B
n = len(data)
slot = pw / n
bw = slot * 0.62


def ypos(v):
    return T + ph - v / ymax * ph


def svg(theme):
    t = THEMES[theme]
    o = []
    a = o.append
    title = "Commit activity per quarter"
    desc = (f"Quarterly commits for GitHub user NermeenShehab from Q{data[0][1]} {data[0][0]} to "
            f"Q{data[-1][1]} {data[-1][0]} (partial, as of {AS_OF}): {total_c} commits. "
            f"Lighter segments show {total_p} additional contributions in private repositories that GitHub "
            f"reports without a type. Source: GitHub contribution activity.")
    a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" '
      f'aria-labelledby="t d" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',\'Noto Sans\',Helvetica,Arial,sans-serif">')
    a(f'<title id="t">{title}</title><desc id="d">{escape(desc)}</desc>')
    # header
    a(f'<text x="{L}" y="26" font-size="15" font-weight="600" fill="{t["text"]}">{title}</text>')
    a(f'<text x="{L}" y="45" font-size="11.5" fill="{t["muted"]}">{total_c} commits · '
      f'Q{data[0][1]} {data[0][0]} – Q{data[-1][1]} {data[-1][0]} (to {AS_OF}) · Source: GitHub contribution activity</text>')
    # legend
    lx = W - R - 330
    a(f'<rect x="{lx}" y="17" width="10" height="10" rx="2" fill="{t["commit"]}"/>'
      f'<text x="{lx + 15}" y="26" font-size="11.5" fill="{t["muted"]}">Commits</text>')
    a(f'<rect x="{lx + 80}" y="17" width="10" height="10" rx="2" fill="{t["private"]}"/>'
      f'<text x="{lx + 95}" y="26" font-size="11.5" fill="{t["muted"]}">Private-repo contributions (type not reported)</text>')
    # grid + y axis
    for v in range(0, ymax + 1, step):
        y = ypos(v)
        a(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="{t["grid"]}" stroke-width="1"'
          f'{" stroke-dasharray=\"3 3\"" if v else ""}/>')
        a(f'<text x="{L - 8}" y="{y + 4:.1f}" font-size="10.5" text-anchor="end" fill="{t["muted"]}">{v}</text>')
    # bars
    year_span = OrderedDict()
    for i, (yr, q, c, p) in enumerate(data):
        cx = L + slot * i + slot / 2
        x = cx - bw / 2
        partial = (yr, q) == (data[-1][0], data[-1][1])
        tip = f"Q{q} {yr}: {c} commit{'s' if c != 1 else ''}"
        if p:
            tip += f" + {p} private-repo contributions (type not reported)"
        if partial:
            tip += f" (partial quarter, to {AS_OF})"
        a(f'<g><title>{escape(tip)}</title>')
        yc = ypos(c)
        if c:
            a(f'<rect x="{x:.1f}" y="{yc:.1f}" width="{bw:.1f}" height="{T + ph - yc:.1f}" rx="2" '
              f'fill="{t["commit"]}"/>')
        top = yc
        if p:
            yp = ypos(c + p)
            a(f'<rect x="{x:.1f}" y="{yp:.1f}" width="{bw:.1f}" height="{yc - yp:.1f}" rx="2" fill="{t["private"]}"/>')
            top = yp
        if c:
            a(f'<text x="{cx:.1f}" y="{top - 5:.1f}" font-size="10.5" font-weight="600" text-anchor="middle" '
              f'fill="{t["text"]}">{c}{"*" if partial else ""}</text>')

        a('</g>')
        a(f'<text x="{cx:.1f}" y="{T + ph + 16}" font-size="10" text-anchor="middle" fill="{t["muted"]}">Q{q}</text>')
        year_span.setdefault(yr, []).append(cx)
    # year labels + separators
    for j, (yr, xs) in enumerate(year_span.items()):
        a(f'<text x="{(xs[0] + xs[-1]) / 2:.1f}" y="{T + ph + 34}" font-size="11.5" font-weight="600" '
          f'text-anchor="middle" fill="{t["text"]}">{yr}</text>')
        if j:
            sx = xs[0] - slot / 2
            a(f'<line x1="{sx:.1f}" x2="{sx:.1f}" y1="{T + ph + 4}" y2="{T + ph + 38}" stroke="{t["grid"]}"/>')
    a(f'<text x="{W - R}" y="{H - 8}" font-size="10" text-anchor="end" fill="{t["muted"]}">'
      f'* Partial quarter · Each commit counted once · Private-repo contributions are not counted as commits</text>')
    a('</svg>')
    return "".join(o)


for th in THEMES:
    with open(f"{OUT}/commit-activity-{th}.svg", "w") as f:
        f.write(svg(th))
print("quarters:", [(f"{y}Q{q}", c, p) for y, q, c, p in data])
print("total commits:", total_c, "private contributions:", total_p)
