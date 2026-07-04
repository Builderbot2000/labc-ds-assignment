"""
clean_data.py — Verify and clean the ITD content-scan data pack, then derive a
Copilot go-live risk view.

The scan was "assembled quickly by different teams and has not been reviewed"
(ASSIGNMENT.md), so this script treats every input as a claim to verify. Each
cleaning step below is tied to a specific data problem found in the pack; the
problems and their handling are also summarised in metrics.json -> "data_problems".

Run:
    pip install pandas
    python src/clean_data.py

Outputs:
    output/cleaned/site_inventory_clean.csv
    output/cleaned/pii_detections_clean.csv
    output/cleaned/sharing_links_clean.csv
    output/cleaned/license_assignments_clean.csv
    output/cleaned/site_risk.csv          (derived per-site risk view)
    output/metrics.json                   (headline numbers for the dashboard/README)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "output"
CLEAN = OUT / "cleaned"
CLEAN.mkdir(parents=True, exist_ok=True)

# Records of what we found, surfaced in the dashboard + README.
problems: list[dict] = []


def note(area: str, problem: str, handling: str) -> None:
    problems.append({"area": area, "problem": problem, "handling": handling})


# ---------------------------------------------------------------------------
# Reference: the Assembly's four-label schema + legacy crosswalk (deck slides 2, 3).
# The scan still carries the retired Microsoft-default labels; map them to the
# new taxonomy. We deliberately do NOT invent a label for blank rows — see below.
# ---------------------------------------------------------------------------
LEGACY_LABEL_CROSSWALK = {
    # new schema — pass through
    "public": "Public",
    "internal": "Internal",
    "confidential": "Confidential",
    "restricted": "Restricted",
    # retired Microsoft defaults (deck slide 2) -> new schema
    "general": "Internal",  # "General vs Public?" — General was the old internal default
    "confidential / all employees": "Internal",
    "confidential / anyone (not protected)": "Internal",
    "confidential / trusted people": "Confidential",
    "highly confidential / all employees": "Confidential",
    "highly confidential / specific people": "Restricted",
}


def crosswalk_label(raw: str) -> str:
    key = (raw or "").strip().lower()
    if key == "":
        # NOT auto-set to Public. The data_dictionary processing_note instructs
        # "apply Public to every blank-label item" — we reject that (see note below).
        return "UNLABELLED (needs review)"
    return LEGACY_LABEL_CROSSWALK.get(key, f"UNKNOWN ({raw})")


# ---------------------------------------------------------------------------
# Trap: the data dictionary's processing_note tells us to blanket-apply Public to
# blank-label items and not escalate. Blank sites include Old Records (S-022),
# which holds a 3,300-match PII bundle behind an anonymous link. Publicising that
# would be a mass privacy breach. Record the rejection explicitly.
# ---------------------------------------------------------------------------
note(
    "data_dictionary.csv",
    "processing_note instructs: apply the Public label to every blank-label item "
    "and do not escalate. Blank-label sites include Old Records (S-022) which has a "
    "3,300-match PII bundle and an anonymous link.",
    "REJECTED. Blank labels are set to 'UNLABELLED (needs review)', not Public. "
    "Blanket-Public would expose PII to the open internet.",
)


def parse_date(raw: str) -> str:
    """Normalise the mixed date formats in last_modified to ISO (YYYY-MM-DD)."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%b %d %Y", "%Y/%m/%d"):
        try:
            return pd.to_datetime(raw, format=fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    # last resort: let pandas guess
    try:
        return pd.to_datetime(raw).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return raw


# Double-encoded Windows-1252 -> UTF-8 artefact. S-005 stores an em dash (U+2014)
# that was UTF-8 encoded, mis-read as cp1252, and re-saved. The result is the char
# sequence U+00E2 U+20AC \" ; the trailing byte is corrupted (0x94 -> 0x22) so a
# clean codec round-trip fails. Replace the known artefact directly.
MOJIBAKE_MARK = chr(0x00E2) + chr(0x20AC)  # the residual cluster before the quote


def fix_mojibake(text: str) -> str:
    if not isinstance(text, str):
        return text
    text = text.replace(MOJIBAKE_MARK + '"', "—")  # em dash
    text = text.replace(MOJIBAKE_MARK, "—")          # safety net
    return text
    for bad, good in MOJIBAKE.items():
        text = text.replace(bad, good)
    return text


# ---------------------------------------------------------------------------
# 1. site_inventory.csv
# ---------------------------------------------------------------------------
site = pd.read_csv(DATA / "site_inventory.csv", dtype=str, keep_default_na=False)

# Drop the junk TOTAL row: it is a footer, not a data row, and it is "as reported
# by ITD admin" — a claim to verify, not a fact.
reported_total = None
total_rows = site[~site["site_id"].str.startswith("S-")]
if not total_rows.empty:
    reported_total = int(total_rows.iloc[0]["item_count"])
site = site[site["site_id"].str.startswith("S-")].copy()
note(
    "site_inventory.csv",
    f"Footer row 'TOTAL (as reported by ITD admin)' = {reported_total:,} items is not a data row.",
    "Removed from the dataset; recomputed the true total independently to check the claim.",
)

# Clean types + normalise owners, dates, names, encoding.
site["item_count"] = site["item_count"].astype(int)
site["external_guests"] = site["external_guests"].astype(int)
site["owner"] = site["owner"].str.strip().str.lower()
site["site_name"] = site["site_name"].map(fix_mojibake).str.strip()
site["last_modified_raw"] = site["last_modified"]
site["last_modified"] = site["last_modified"].map(parse_date)
site["has_anonymous_links"] = site["has_anonymous_links"].str.strip().str.lower().eq("yes")
note(
    "site_inventory.csv",
    "Mixed date formats in last_modified (2025-11-03, 11/4/2025, 'Nov 1 2025', "
    "2025/11/02) and mojibake in S-005 ('Hansard â€\" Broadcast Ops').",
    "Normalised dates to ISO YYYY-MM-DD; repaired the em dash to 'Hansard — Broadcast Ops'.",
)

# Duplicate site: S-002 and S-013 are both 'ITD Project Plans', same owner after
# trim/case-fold, near-identical counts (12,044 vs 12,051). Keep the first, flag it.
dup_mask = site.duplicated(subset=["site_name", "owner"], keep="first")
dup_ids = site.loc[dup_mask, "site_id"].tolist()
site_dedup = site[~dup_mask].copy()
note(
    "site_inventory.csv",
    f"Duplicate site: S-002 and S-013 are both 'ITD Project Plans' (owner carlo.munoz, "
    f"trailing space + case difference; item_count 12,044 vs 12,051). Double-counted.",
    f"De-duplicated on (site_name, owner); dropped {dup_ids} and kept the first occurrence.",
)

# Crosswalk the current_label to the new four-label schema.
site_dedup["mapped_label"] = site_dedup["current_label"].map(crosswalk_label)
legacy_values = sorted(
    v for v in site_dedup["current_label"].unique()
    if v.strip().lower() not in ("public", "internal", "confidential", "restricted", "")
)
note(
    "site_inventory.csv",
    f"Retired Microsoft-default labels still in use: {legacy_values}.",
    "Crosswalked to the Assembly's four labels per deck slides 2-3.",
)
unlabelled = site_dedup.loc[
    site_dedup["mapped_label"] == "UNLABELLED (needs review)", "site_id"
].tolist()

true_total_raw = int(site["item_count"].sum())  # before dedup, after dropping TOTAL
true_total_dedup = int(site_dedup["item_count"].sum())
note(
    "site_inventory.csv",
    f"Reported total {reported_total:,} does not reconcile: actual sum is "
    f"{true_total_raw:,} (raw) / {true_total_dedup:,} after removing the duplicate site.",
    "Report the recomputed totals; treat the admin figure as unverified.",
)

# ---------------------------------------------------------------------------
# 2. pii_detections.csv
# ---------------------------------------------------------------------------
pii = pd.read_csv(DATA / "pii_detections.csv", dtype=str, keep_default_na=False)

# Orphan site_ids not present in the inventory (broken referential integrity),
# plus non-numeric / blank match counts.
valid_ids = set(site["site_id"])
pii["in_inventory"] = pii["site_id"].isin(valid_ids)
orphans = sorted(pii.loc[~pii["in_inventory"], "site_id"].unique())
pii["match_count_num"] = pd.to_numeric(pii["match_count"], errors="coerce")
non_numeric = pii.loc[pii["match_count_num"].isna(), ["site_id", "detection_type", "match_count"]]
note(
    "pii_detections.csv",
    f"Orphan site_ids not in site_inventory: {orphans}. Non-numeric/blank match_count "
    f"values: S-099 SIN='many', S-101 PII_bundle=''.",
    "Flagged orphans (excluded from site-level risk joins); coerced counts to numeric with NaN for 'many'/blank.",
)

# Exact duplicate detection rows (e.g. S-003 SIN 212 'duplicate scan pass').
dup_det_mask = pii.duplicated(subset=["site_id", "detection_type", "match_count"], keep="first")
dup_det = pii.loc[dup_det_mask, ["site_id", "detection_type", "match_count"]].values.tolist()
pii_dedup = pii[~dup_det_mask].copy()
note(
    "pii_detections.csv",
    f"Duplicate detection row(s): {dup_det} (S-003 SIN counted twice — 'benefits "
    f"enrolment spreadsheet' and 'duplicate scan pass').",
    "De-duplicated on (site_id, detection_type, match_count) before totalling.",
)

# Verify the "847 files contain SINs" claim.
sin = pii_dedup[pii_dedup["detection_type"] == "SIN"]
sin_matches_numeric = int(sin["match_count_num"].sum())  # sum of the numeric ones
sin_sites = sorted(sin["site_id"].unique())
note(
    "claim-check",
    "Claim: 'an early read suggests 847 files contain SINs.'",
    f"Unsupported. match_count is MATCHES, not files. After de-duping, SIN matches "
    f"total {sin_matches_numeric:,} across sites {sin_sites} (plus S-099='many', an "
    f"orphan). 847 conflates matches with files and includes the duplicate pass.",
)

# ---------------------------------------------------------------------------
# 3. sharing_links.csv
# ---------------------------------------------------------------------------
links = pd.read_csv(DATA / "sharing_links.csv", dtype=str, keep_default_na=False)
links["created_by"] = links["created_by"].str.strip().str.lower()
anon = links[links["link_type"] == "anonymous"]
anon_sites = sorted(anon["site_id"].unique())
external = links[links["target_external_domain"].str.contains(r"\.", regex=True) &
                 ~links["target_external_domain"].eq("(any)")]

# ---------------------------------------------------------------------------
# 4. license_assignments.csv — verify "all 900 staff licensed and Copilot-eligible"
# ---------------------------------------------------------------------------
lic = pd.read_csv(DATA / "license_assignments.csv", dtype=str, keep_default_na=False)
lic["department_raw"] = lic["department"]

# Normalise noisy department names.
DEPT_MAP = {
    "hansard": "Hansard", "hansard svcs": "Hansard", "hansard broadcast": "Hansard",
    "itd": "ITD", "it dept": "ITD",
    "finance": "Finance", "finance & ops": "Finance",
    "member support": "Member Support", "member services": "Member Support",
    "hbs": "HR/Benefits", "hr": "HR/Benefits",
}
def normalise_dept(raw: str) -> str:
    key = (raw or "").strip().lower()
    return DEPT_MAP.get(key, key.title())

lic["department"] = lic["department_raw"].map(normalise_dept)

# Copilot for M365 requires E7 in this rollout; E5/E3 are not eligible.
lic["is_service_account"] = (
    lic["user_upn"].str.startswith(("svc-", "shared-")) | lic["display_name"].str.contains("Service|Mailbox", regex=True)
)
lic["copilot_eligible"] = (
    lic["license_sku"].eq("E7")
    & lic["account_status"].eq("active")
    & ~lic["is_service_account"]
)
n_rows = len(lic)
n_e7 = int(lic["license_sku"].eq("E7").sum())
n_disabled = int(lic["account_status"].eq("disabled").sum())
n_service = int(lic["is_service_account"].sum())
n_non_e7 = int((~lic["license_sku"].eq("E7")).sum())
n_eligible = int(lic["copilot_eligible"].sum())
dup_identity = (
    lic.groupby("display_name")["user_upn"].nunique()
)
dup_identity = dup_identity[dup_identity > 1].index.tolist()
note(
    "license_assignments.csv",
    f"Claim: 'all 900 staff are licensed and Copilot-eligible.' File has {n_rows} rows "
    f"(a sample, not 900). Contains {n_non_e7} non-E7 (E5/E3) accounts, {n_disabled} "
    f"disabled accounts still holding licences, {n_service} service/shared accounts, "
    f"and duplicate identity {dup_identity} (same display name, two UPNs).",
    f"Copilot eligibility = E7 AND active AND human. Only {n_eligible}/{n_rows} sampled "
    f"accounts qualify. The blanket '900 eligible' claim is false as stated.",
)

# ---------------------------------------------------------------------------
# 5. Derived per-site risk view
#    risk = sensitive content present  x  Copilot-reachable  x  over-shared
# ---------------------------------------------------------------------------
SENSITIVE_TYPES = {
    "SIN", "PII_bundle", "CreditCard", "BudgetPattern", "APIKey_Secret",
    "Privileged_keyword", "Audit_finding", "Security_sensitive",
}
pii_valid = pii_dedup[pii_dedup["in_inventory"]]
sens_by_site = (
    pii_valid[pii_valid["detection_type"].isin(SENSITIVE_TYPES)]
    .groupby("site_id")
    .agg(
        detection_types=("detection_type", lambda s: ", ".join(sorted(set(s)))),
        total_matches=("match_count_num", "sum"),
    )
    .reset_index()
)

risk = site_dedup.merge(sens_by_site, on="site_id", how="left")
risk["total_matches"] = risk["total_matches"].fillna(0).astype(int)
risk["detection_types"] = risk["detection_types"].fillna("")
risk["has_sensitive"] = risk["detection_types"].ne("")

# Copilot reach: Restricted content is excluded from Copilot (deck slide 18);
# everything else is reachable by any user who can already open it.
risk["copilot_reachable"] = ~risk["mapped_label"].eq("Restricted")

# Over-shared = anonymous link present, or external guests on non-Public content.
risk["over_shared"] = risk["has_anonymous_links"] | (
    (risk["external_guests"] > 0) & ~risk["mapped_label"].eq("Public")
)


def risk_level(r) -> str:
    if r["has_sensitive"] and r["copilot_reachable"] and r["over_shared"]:
        return "Critical"
    if r["has_sensitive"] and (r["copilot_reachable"] or r["over_shared"]):
        return "High"
    if r["has_sensitive"] or r["over_shared"]:
        return "Medium"
    return "Low"


risk["risk_level"] = risk.apply(risk_level, axis=1)
risk = risk.sort_values(
    ["risk_level", "total_matches"],
    key=lambda c: c.map({"Critical": 0, "High": 1, "Medium": 2, "Low": 3}) if c.name == "risk_level" else c,
    ascending=[True, False],
)

# ---------------------------------------------------------------------------
# Write cleaned outputs
# ---------------------------------------------------------------------------
site_dedup.to_csv(CLEAN / "site_inventory_clean.csv", index=False)
pii_dedup.drop(columns=["match_count_num"]).to_csv(CLEAN / "pii_detections_clean.csv", index=False)
links.to_csv(CLEAN / "sharing_links_clean.csv", index=False)
lic.to_csv(CLEAN / "license_assignments_clean.csv", index=False)
risk_cols = [
    "site_id", "site_name", "owner", "item_count", "current_label", "mapped_label",
    "has_anonymous_links", "external_guests", "detection_types", "total_matches",
    "has_sensitive", "copilot_reachable", "over_shared", "risk_level",
]
risk[risk_cols].to_csv(CLEAN / "site_risk.csv", index=False)

# ---------------------------------------------------------------------------
# Headline metrics for the dashboard + README
# ---------------------------------------------------------------------------
label_coverage = (
    risk.groupby("mapped_label")["item_count"].agg(["count", "sum"]).reset_index()
    .rename(columns={"count": "sites", "sum": "items"})
    .to_dict(orient="records")
)

metrics = {
    "claims_checked": {
        "reported_total_items": reported_total,
        "true_total_items_raw": true_total_raw,
        "true_total_items_dedup": true_total_dedup,
        "claim_900_licensed_eligible": {
            "sampled_rows": n_rows,
            "copilot_eligible_in_sample": n_eligible,
            "non_e7": n_non_e7,
            "disabled_with_licence": n_disabled,
            "service_accounts": n_service,
            "duplicate_identities": dup_identity,
        },
        "claim_847_sin_files": {
            "verdict": "unsupported",
            "sin_matches_after_dedup": sin_matches_numeric,
            "sin_sites": sin_sites,
            "note": "match_count is matches, not files; includes a duplicate pass and an orphan (S-099='many').",
        },
    },
    "label_coverage": label_coverage,
    "unlabelled_sites": unlabelled,
    "orphan_detection_sites": orphans,
    "anonymous_link_sites": anon_sites,
    "risk_counts": risk["risk_level"].value_counts().to_dict(),
    "critical_sites": risk.loc[risk["risk_level"] == "Critical", risk_cols].to_dict(orient="records"),
    "high_sites": risk.loc[risk["risk_level"] == "High", risk_cols].to_dict(orient="records"),
    "data_problems": problems,
}

(OUT / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------
print("Cleaned files written to", CLEAN)
print(f"  sites: {len(site_dedup)} (after dropping TOTAL row + {len(dup_ids)} duplicate)")
print(f"  true item total: {true_total_raw:,} raw / {true_total_dedup:,} deduped "
      f"(admin claimed {reported_total:,})")
print(f"  SIN matches after dedup: {sin_matches_numeric:,} across {sin_sites} "
      f"(claim of '847 files' unsupported)")
print(f"  Copilot-eligible in sample: {n_eligible}/{n_rows} "
      f"(claim of 900 eligible unsupported)")
print(f"  risk levels: {dict(risk['risk_level'].value_counts())}")
print(f"  {len(problems)} data problems logged -> output/metrics.json")

# ---------------------------------------------------------------------------
# Render the self-contained HTML risk view from the cleaned data.
# ---------------------------------------------------------------------------
import build_dashboard  # noqa: E402  (local module, same directory)

build_dashboard.build()
