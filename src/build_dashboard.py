"""
build_dashboard.py — Render output/dashboard.html (self-contained, no CDN) from the
cleaned data produced by clean_data.py.

The page is a single HTML file with inline SVG charts. It is theme-aware (light/dark)
and uses the validated reference data-viz palette (blue single-hue for magnitude;
the reserved status palette — critical/serious/warning/good — for risk tiers, always
paired with a legend + labels so colour never carries meaning alone).

Run standalone:
    python src/build_dashboard.py      # after clean_data.py has written output/
or it is called automatically at the end of clean_data.py.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
CLEAN = OUT / "cleaned"

# ---- palette (reference instance; light / dark) ---------------------------
BLUE = "#2a78d6"
STATUS = {  # reserved status palette
    "Critical": "#d03b3b",
    "High": "#ec835a",
    "Medium": "#fab219",
    "Low": "#0ca30c",
}
STATUS_ICON = {"Critical": "◆", "High": "▲", "Medium": "■", "Low": "●"}


def esc(x) -> str:
    return html.escape(str(x))


def hbar_chart(rows, value_key, label_key, color_fn, unit="", max_val=None) -> str:
    """Horizontal bar chart. rows: list of dicts. Baseline at left, rounded data-end."""
    pad_l, pad_r, pad_t = 8, 8, 8
    bar_h, gap = 24, 12
    plot_w = 560
    label_w = 230
    val_w = 90
    max_val = max_val or max((r[value_key] for r in rows), default=1) or 1
    total_w = label_w + plot_w + val_w
    total_h = pad_t * 2 + len(rows) * (bar_h + gap) - gap
    parts = [
        f'<svg viewBox="0 0 {total_w} {total_h}" width="100%" '
        f'role="img" preserveAspectRatio="xMinYMin meet" class="chart">'
    ]
    y = pad_t
    for r in rows:
        v = r[value_key]
        w = max(3, v / max_val * plot_w)
        color = color_fn(r)
        lab = esc(r[label_key])
        parts.append(
            f'<text x="{label_w - 10}" y="{y + bar_h/2}" text-anchor="end" '
            f'dominant-baseline="central" class="cat">{lab}</text>'
        )
        parts.append(
            f'<rect x="{label_w}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="4" '
            f'fill="{color}"><title>{lab}: {v:,}{esc(unit)}</title></rect>'
        )
        parts.append(
            f'<text x="{label_w + w + 8:.1f}" y="{y + bar_h/2}" '
            f'dominant-baseline="central" class="val">{v:,}{esc(unit)}</text>'
        )
        y += bar_h + gap
    parts.append("</svg>")
    return "".join(parts)


def build() -> None:
    metrics = json.loads((OUT / "metrics.json").read_text(encoding="utf-8"))
    risk = pd.read_csv(CLEAN / "site_risk.csv")
    links = pd.read_csv(CLEAN / "sharing_links_clean.csv")

    cc = metrics["claims_checked"]
    lic = cc["claim_900_licensed_eligible"]
    sinc = cc["claim_847_sin_files"]

    # ---- Section A: three claims (stat tiles) ----
    tiles = [
        {
            "claim": "All 900 staff are licensed and Copilot-eligible.",
            "verdict": "Unsupported",
            "big": f"{lic['copilot_eligible_in_sample']} of {lic['sampled_rows']}",
            "sub": (f"sampled accounts are Copilot-eligible (E7 + active + human). "
                    f"The file has {lic['sampled_rows']} rows, not 900: "
                    f"{lic['non_e7']} non-E7, {lic['disabled_with_licence']} disabled, "
                    f"{lic['service_accounts']} service accounts, duplicate identity "
                    f"{lic['duplicate_identities']}."),
        },
        {
            "claim": "An early read suggests 847 files contain SINs.",
            "verdict": "Unsupported",
            "big": f"{sinc['sin_matches_after_dedup']:,} matches",
            "sub": (f"not files. match_count counts matches; after removing a duplicate "
                    f"scan pass, SIN matches total {sinc['sin_matches_after_dedup']:,} "
                    f"across {esc(', '.join(sinc['sin_sites']))} (S-099 = 'many', an "
                    f"orphan not in the inventory). 847 conflates matches with files."),
        },
        {
            "claim": "Item total is 196,900 (as reported by ITD admin).",
            "verdict": "Does not reconcile",
            "big": f"{cc['true_total_items_dedup']:,} items",
            "sub": (f"recomputed from source ({cc['true_total_items_raw']:,} before "
                    f"de-duplicating the double-counted ITD Project Plans site). The "
                    f"admin footer of {cc['reported_total_items']:,} is ~{cc['reported_total_items']-cc['true_total_items_dedup']:,} high."),
        },
    ]
    tile_html = "".join(
        f'<div class="tile"><div class="claim">CLAIM &middot; {esc(t["claim"])}</div>'
        f'<div class="verdict">{esc(t["verdict"])}</div>'
        f'<div class="big">{esc(t["big"])}</div>'
        f'<div class="sub">{t["sub"]}</div></div>'
        for t in tiles
    )

    # ---- Section B: label coverage (items by mapped label) ----
    cov = sorted(metrics["label_coverage"], key=lambda r: -r["items"])
    def cov_color(r):
        return STATUS["Critical"] if r["mapped_label"].startswith("UNLABELLED") else BLUE
    cov_rows = [{"mapped_label": r["mapped_label"], "items": r["items"], "sites": r["sites"]} for r in cov]
    cov_chart = hbar_chart(cov_rows, "items", "mapped_label", cov_color, unit="")

    # ---- Section C: Copilot-reach risk (sensitive sites by match count) ----
    sens = risk[risk["has_sensitive"]].copy().sort_values("total_matches", ascending=False)
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    sens["ord"] = sens["risk_level"].map(order)
    sens = sens.sort_values(["ord", "total_matches"], ascending=[True, False])
    sens_rows = [
        {"site": f'{r.site_id} {r.site_name}', "total_matches": int(r.total_matches),
         "risk_level": r.risk_level}
        for r in sens.itertuples()
    ]
    risk_chart = hbar_chart(
        sens_rows, "total_matches", "site",
        lambda r: STATUS[r["risk_level"]], unit=" matches",
    )
    legend = "".join(
        f'<span class="lg"><span class="dot" style="color:{STATUS[k]}">{STATUS_ICON[k]}</span>{k}</span>'
        for k in ["Critical", "High", "Medium", "Low"]
    )

    # ---- Section D: over-sharing (anonymous links) ----
    anon = links[links["link_type"] == "anonymous"].merge(
        risk[["site_id", "site_name", "mapped_label", "detection_types", "total_matches"]],
        on="site_id", how="left",
    )
    anon = anon.sort_values("total_matches", ascending=False, na_position="last")
    anon_rows = "".join(
        f'<tr><td>{esc(r.site_id)}</td><td>{esc(r.site_name)}</td>'
        f'<td>{esc(r.mapped_label)}</td>'
        f'<td>{esc(r.detection_types) or "&mdash;"}</td>'
        f'<td class="num">{"" if pd.isna(r.total_matches) else f"{int(r.total_matches):,}"}</td>'
        f'<td>{esc(r.target_external_domain)}</td></tr>'
        for r in anon.itertuples()
    )

    # ---- Section E: data problems ----
    prob_rows = "".join(
        f'<tr><td class="mono">{esc(p["area"])}</td><td>{esc(p["problem"])}</td>'
        f'<td>{esc(p["handling"])}</td></tr>'
        for p in metrics["data_problems"]
    )

    critical_n = metrics["risk_counts"].get("Critical", 0)
    high_n = metrics["risk_counts"].get("High", 0)

    page = f"""<div class="viz-root">
<header>
  <h1>Copilot Go-Live Risk View</h1>
  <p class="lede">ITD content scan &mdash; verified and cleaned. Every figure below is
  recomputed from source by <code>src/clean_data.py</code>; admin-reported figures are
  treated as claims to check, not facts. <strong>{critical_n} sites are Critical</strong>
  and {high_n} High for Copilot exposure.</p>
</header>

<section>
  <h2>Three claims we were asked to accept</h2>
  <p class="note">The brief states these as facts. The data does not support them.</p>
  <div class="tiles">{tile_html}</div>
</section>

<section>
  <h2>Where the content sits &mdash; label coverage</h2>
  <p class="note">Items by mapped label after crosswalking the retired Microsoft-default
  scheme to the Assembly&rsquo;s four labels. <strong style="color:{STATUS['Critical']}">
  Unlabelled content (S-007 Member Services, S-022 Old Records) is the second-largest
  bucket</strong> &mdash; the data dictionary told us to blanket-label it Public. We did
  not; blank labels are held for review.</p>
  {cov_chart}
</section>

<section>
  <h2>What Copilot will be able to reach</h2>
  <p class="note">Sites holding sensitive content, ranked by detection matches and
  coloured by risk tier (sensitive content &times; Copilot-reachable &times; over-shared).
  Restricted sites are excluded from Copilot entirely (deck slide 18), so they score
  lower here even when sensitive &mdash; the exposure that matters for Copilot is
  sensitive content sitting under Public/Internal/Confidential with broad sharing.</p>
  <div class="legend">{legend}</div>
  {risk_chart}
</section>

<section>
  <h2>Over-sharing &mdash; anonymous links</h2>
  <p class="note">Anonymous links make content reachable without sign-in. Two are
  acute: <strong>S-006</strong> (a Restricted legal library shared to external counsel)
  and <strong>S-022</strong> (unlabelled Old Records holding a 3,300-match PII bundle).
  Both must be remediated before go-live.</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Site</th><th>Name</th><th>Mapped label</th><th>Sensitive content</th>
    <th class="num">Matches</th><th>External domain</th></tr></thead>
    <tbody>{anon_rows}</tbody>
  </table></div>
</section>

<section>
  <h2>Data problems found &amp; how we handled them</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Where</th><th>Problem</th><th>Handling</th></tr></thead>
    <tbody>{prob_rows}</tbody>
  </table></div>
</section>

<footer>Generated from the cleaned data pack &middot; self-contained, no external
resources &middot; Senior Data Strategist take-home.</footer>
</div>
"""

    (OUT / "dashboard.html").write_text(_HEAD + page + _TAIL, encoding="utf-8")
    print("Wrote", OUT / "dashboard.html")


_HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Copilot Go-Live Risk View</title>
<style>
:root{
  --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
  --grid:#e1e0d9; --border:rgba(11,11,11,0.10); --accent:#2a78d6;
}
@media (prefers-color-scheme: dark){
  :root{ --page:#0d0d0d; --surface:#1a1a19; --ink:#fff; --ink2:#c3c2b7; --muted:#898781;
    --grid:#2c2c2a; --border:rgba(255,255,255,0.10); --accent:#3987e5; }
}
:root[data-theme="dark"]{ --page:#0d0d0d; --surface:#1a1a19; --ink:#fff; --ink2:#c3c2b7;
  --muted:#898781; --grid:#2c2c2a; --border:rgba(255,255,255,0.10); --accent:#3987e5; }
:root[data-theme="light"]{ --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e;
  --muted:#898781; --grid:#e1e0d9; --border:rgba(11,11,11,0.10); --accent:#2a78d6; }
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5;
  -webkit-font-smoothing:antialiased;}
.viz-root{max-width:900px;margin:0 auto;padding:40px 24px 64px;}
header{margin-bottom:32px;}
h1{font-size:30px;margin:0 0 8px;letter-spacing:-0.02em;}
.lede{font-size:16px;color:var(--ink2);margin:0;max-width:66ch;}
section{background:var(--surface);border:1px solid var(--border);border-radius:14px;
  padding:22px 24px;margin:18px 0;}
h2{font-size:18px;margin:0 0 6px;letter-spacing:-0.01em;}
.note{font-size:13.5px;color:var(--ink2);margin:0 0 16px;max-width:74ch;}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;}
.tile{border:1px solid var(--border);border-radius:12px;padding:16px;background:var(--page);}
.claim{font-size:11px;letter-spacing:0.04em;color:var(--muted);text-transform:uppercase;
  margin-bottom:10px;line-height:1.4;}
.verdict{display:inline-block;font-size:11px;font-weight:700;letter-spacing:0.03em;
  text-transform:uppercase;color:#fff;background:#d03b3b;border-radius:999px;
  padding:2px 9px;margin-bottom:8px;}
.big{font-size:26px;font-weight:700;letter-spacing:-0.02em;margin-bottom:6px;}
.sub{font-size:12.5px;color:var(--ink2);}
.chart{display:block;margin-top:4px;overflow:visible;}
.chart .cat{fill:var(--ink);font-size:12.5px;}
.chart .val{fill:var(--ink2);font-size:12px;font-variant-numeric:tabular-nums;}
.legend{display:flex;gap:18px;flex-wrap:wrap;margin-bottom:12px;font-size:12.5px;color:var(--ink2);}
.lg{display:inline-flex;align-items:center;gap:6px;}
.dot{font-size:12px;}
.tbl-wrap{overflow-x:auto;}
table{border-collapse:collapse;width:100%;font-size:13px;}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--grid);vertical-align:top;}
th{color:var(--muted);font-weight:600;font-size:11.5px;text-transform:uppercase;
  letter-spacing:0.03em;white-space:nowrap;}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}
.mono,td.mono{font-family:ui-monospace,"Cascadia Code",Consolas,monospace;font-size:12px;white-space:nowrap;}
code{font-family:ui-monospace,Consolas,monospace;font-size:0.9em;background:var(--page);
  padding:1px 5px;border-radius:5px;border:1px solid var(--border);}
footer{margin-top:28px;font-size:12px;color:var(--muted);text-align:center;}
</style></head><body>
"""

_TAIL = "\n</body></html>"


if __name__ == "__main__":
    build()
