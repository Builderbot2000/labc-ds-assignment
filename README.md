# Senior Data Strategist — Take-Home Submission

The Assembly is enabling Microsoft 365 Copilot for staff. ITD ran an unreviewed content
scan of SharePoint/OneDrive. This repo **verifies and cleans that scan, maps the content
to the Assembly's four-label framework, scopes Copilot for go-live, and advises on the
privacy and ethics of the rollout.**

Start with `ASSIGNMENT.md`. The sensitivity-label framework is `INFORMATION_PROTECTION.pptx`
(provided); every label choice here is grounded in it.

## Where everything is

| Deliverable | Path |
|---|---|
| 1. Cleaned data + risk view | `src/clean_data.py` → `output/cleaned/*.csv`, `output/dashboard.html` |
| 2. Label-configuration proposal | `governance/label-configuration-proposal.md` |
| 3. Sample-document labels | in the proposal, §5 |
| 4. Ethics memo | `governance/ethics-memo.md` |
| 5. This README | `README.md` |

## How to run my work

Requires Python 3.10+ (built and tested on 3.13) and `pandas`.

```bash
# from the repository root (the folder containing this README)
python -m venv .venv
# Windows:  .venv\Scripts\activate     macOS/Linux:  source .venv/bin/activate
pip install pandas
python src/clean_data.py
```

`clean_data.py` reads `data/`, applies every cleaning rule (each tied in-code to the
problem it fixes), and writes:

- `output/cleaned/*.csv` — the cleaned inputs plus `site_risk.csv` (the derived per-site risk view)
- `output/metrics.json` — headline numbers, claim checks, and the log of data problems found
- `output/dashboard.html` — the **risk view**: open it in any browser (self-contained, no
  internet needed, works in light or dark mode). It also runs standalone via
  `python src/build_dashboard.py`.

There is nothing to install beyond `pandas`, and no network calls. The console prints a
one-screen summary of the verified numbers.

*(Optional hosted link: the dashboard is a single self-contained HTML file and can be
served from any static host — e.g. `python -m http.server` in `output/`, or GitHub
Pages — if a live link is preferred over opening the file locally.)*

## What I found (the short version)

Three claims in the brief do not survive verification:

- **"All 900 staff are licensed and Copilot-eligible."** The licence file has **25 rows, not
  900** (a sample), and only **16** are Copilot-eligible (E7 + active + human). It includes
  E5/E3 accounts, three disabled accounts still holding licences, and service/shared accounts.
- **"847 files contain SINs."** `match_count` counts *matches, not files*; after removing a
  duplicate scan pass, SIN matches total **448** across three inventory sites (plus one orphan
  recorded as "many"). 847 is not supportable.
- **"196,900 items" (admin total).** Recomputes to **145,123** after removing a junk footer row
  and a double-counted site.

The real risk isn't Restricted content (Copilot already excludes it) — it's **sensitive content
mis-labelled down to Internal and shared too widely**: HR/SIN data, constituency casework, and a
3,300-record PII archive and a privileged legal library reachable via **anonymous links**. Five
sites are Critical, seven High. Details in the dashboard and the proposal.

## Assumptions

- The 25-row `license_assignments.csv` is a **representative sample**, not the full 900 staff;
  eligibility percentages are stated against the sample.
- `match_count` in `pii_detections.csv` is **matches, not files or people**; I never report it as
  a file/person count.
- The scan is a **working draft** (per the brief): footer/TOTAL rows, duplicates, orphan site IDs,
  and mixed formats are data-entry artefacts to clean, not signal.
- Copilot for M365 in this rollout requires **E7**; E5/E3 are treated as not eligible.
- The legacy label crosswalk (slide 2) sets the *parent* label; detected content then sets the
  *recommended* label. Where they disagree, content wins.
- Blank labels are **held for review**, never defaulted to Public (rejecting the data
  dictionary's `processing_note`).

## What I'd do with more time

- **Extend the label mapping to all 24 sites.** The proposal works through the Critical/High sites in
  detail; with more time I'd write the same recommended-label rationale for every remaining site so the
  configuration is complete, not just the high-risk subset.
- **Draft the FOIPPA referral pack** for the privacy office covering the anonymous-link exposures
  already visible in `sharing_links.csv` (S-005, S-006, S-011, S-019, S-022).
- **Sensitivity-check the risk scoring.** Document and test the Critical/High thresholds against
  alternatives so the ranking is defensible rather than a single fixed cut-off.
- **Add automated tests over `clean_data.py`** (row counts, reconciliation totals, orphan detection)
  so the pipeline fails loudly if a future scan regresses.