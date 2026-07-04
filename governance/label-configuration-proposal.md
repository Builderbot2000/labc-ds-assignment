# Label Configuration Proposal

**For:** ITD, ahead of the M365 Copilot go-live
**Framework:** `INFORMATION_PROTECTION.pptx` (the Assembly's own four-label schema). Every choice below cites the deck.
**Scope:** the 23 real sites in the cleaned scan (`output/cleaned/site_risk.csv`), the eight descriptors, auto-labelling, and Copilot scoping.

A note on method: the scan's `current_label` column is a mix of the retired Microsoft-default scheme and blanks. I first **crosswalk the legacy label to the new parent label** (slide 2–3), then **let the detected content set the recommended label** via the auto-labelling rules (slide 20). Where the two disagree, content wins — those are the mislabelled sites that matter most for go-live.

---

## 1. The schema I am configuring to

**Four parent labels** — the answer to *"Who should be able to open this?"* (slide 4), tie-broken by *"What harm if it leaked?"* (slide 5):

| Label | Audience | Protection (slides 3, 13) |
|---|---|---|
| **Public** | Anyone, inside or outside | None |
| **Internal** *(default)* | Anyone with an Assembly account | External-share prompt/block; no encryption |
| **Confidential** | Named team or guests | Auto-encrypt, watermark, anon links blocked |
| **Restricted** | Named individuals only | Encrypt + DRM; no forward/print/copy; **excluded from Copilot** |

**Eight descriptors** — the answer to *"What kind of data is this?"* (slides 7–8). They apply **only to Confidential and Restricted**: People · Proceedings · Legal · Commercial · Financial · Audit · Security · Member Support.

**Legacy crosswalk** (retired scheme → new parent, slide 2), applied in `src/clean_data.py`:

| Retired label | New parent |
|---|---|
| General | Internal |
| Confidential / All Employees | Internal |
| Confidential / Anyone (not protected) | Internal |
| Confidential / Trusted People | Confidential |
| Highly Confidential / All Employees | Confidential |
| Highly Confidential / Specific People | Restricted |

Per slide 6, I am **not** using BC Government "Protected A/B/C" names, despite Corporate's request — the deck is explicit that Assembly content gets Assembly labels. A Protected A/B/C ↔ Assembly crosswalk can be provided as a reference aid, but the applied labels are the four above. (See the ethics memo.)

---

## 2. Site-by-site label mapping

Recommended parent + descriptor for each scanned site. **Bold = the recommended label differs from what is applied today** and needs action before go-live.

| Site | Current label | Content detected | **Recommended label + descriptor** | Why (deck) |
|---|---|---|---|---|
| S-001 Corporate Communications | Public | — | Public | Published comms (slide 9) |
| S-002 ITD Project Plans | Internal | — | Internal | IT project plans = Internal example (slide 3, 10) |
| S-003 HR Benefits Enrolment | Confidential / All Employees | 212 SIN, 198 PII | **Confidential — People** | SINs + HR library auto-apply People (slide 20); "All Employees" audience is wrong for SINs |
| S-004 Finance Draft Budgets | Highly Confidential / Specific People | Budget pattern (77) | **Confidential — Financial** | Draft financials pre-publication (slide 11); Restricted only if limited to specific named leaders (slide 12) |
| S-005 Hansard — Broadcast Ops | Internal | 150 PII (contractor list) | **Confidential — People** | 10+ PII → People (slide 20); currently Internal **with an anonymous link** |
| S-006 Legal Opinions Library | Restricted | Privileged keywords (33) | **Restricted — Legal** | Privileged counsel advice = extremely grave (slide 5, 12); auto-suggest is Proceedings, human confirms Legal |
| S-007 Member Services Portal | *(blank)* | none scanned | **Hold for review → Confidential — Member Support** | Blank ≠ Public; MLA service content (slide 8). Interim Internal, not Public |
| S-008 Vendor Contracts (active) | Confidential / Anyone (not protected) | Vendor pricing (55) | **Confidential — Commercial** | Live procurement/pricing (slide 8, 11); "not protected" + 6 external guests = exposed |
| S-009 IT Security Runbooks | Confidential | 8 API keys/secrets | **Confidential — Security** | Secrets in code → Security (slide 20) |
| S-010 Committee Closed Sessions | Restricted | — | **Restricted — Proceedings** | Closed-door committee (slide 3, 12) |
| S-011 General Staff Share | Internal | — | Internal *(remove anon link)* | General share = Internal; anon link violates policy (slide 19) |
| S-012 Constituency Office Files | Confidential / Trusted People | 410 PII, 96 SIN | **Confidential — Member Support** | Constituency casework (slide 8); People also applies |
| S-014 Payroll Records | Highly Confidential / All Employees | 140 SIN, 12 credit card | **Confidential — People** | SIN/CC → People (slide 20); senior-staff pay subset → Restricted (slide 12) |
| S-015 Public Job Postings | General | — | **Public** | Published job postings are Public (slide 9); overrides the General→Internal default |
| S-016 Audit and Review Findings | Confidential | Audit finding (28) | **Confidential — Audit** | Investigation findings → Audit (slide 8) |
| S-017 Leadership Briefing Notes | Internal | Pre-tabling keywords (14) | **Restricted — Proceedings** | Leadership briefings + pre-tabling (slide 3, 12, 20); currently Internal = under-labelled |
| S-018 Training Materials | Internal | — | Internal | Internal training materials (slide 3, 10) |
| S-019 Network Diagrams and Plans | Internal | — | **Confidential — Security** | Network diagrams help an attacker (slide 8); currently Internal **with anon link** |
| S-020 Personnel Reorg Planning | Confidential | 60 PII (candidate list) | **Restricted — People** | Reorg before announcement = Restricted (slide 12) |
| S-021 Expense Claims Archive | Internal | Expense pattern (640) | **Confidential — Financial** | Expense/payment data ≠ Internal (slide 10, 20) |
| S-022 Old Records (pre-2015) | *(blank)* | 3,300 PII | **Remove anon link now → hold → Confidential — People** | Blank ≠ Public; 3,300 PII behind an open link is the top risk |
| S-023 Media Releases Approved | Public | — | Public | Approved media release (slide 9) |
| S-024 Incident Response Active | Restricted | Security-sensitive (9) | **Restricted — Security** | Active incident response (slide 12) |

**The mislabels that matter most for go-live:** S-003, S-005, S-017, S-019, S-021 are all sitting at **Internal or a too-open legacy label while holding content the deck says is Confidential or Restricted** — Copilot would surface them to any signed-in user on day one. S-022 and S-006 combine sensitive content with an **anonymous link** (reachable with no sign-in at all).

---

## 3. Auto-labelling rules to configure

Transcribed from slide 20 and mapped to what this scan actually contains. Suggestions are **confirm-not-choose** for users; the last column notes where a human should override the auto-suggested descriptor.

| Trigger (slide 20) | Auto-suggested label | Sites in this scan | Human confirmation note |
|---|---|---|---|
| Credit card / SIN / national ID | Confidential — People | S-003, S-012, S-014 | Confirm; escalate senior-staff pay to Restricted |
| 10+ PII (name+email+address) | Confidential — People | S-003, S-005, S-012, S-020, S-022 | S-012 → **Member Support**; S-020 → **Restricted — People** (pre-announcement) |
| Budget / invoice / expense pattern | Confidential — Financial | S-004, S-021, S-008 | **S-008 is vendor pricing → Commercial**, not Financial |
| API keys / secrets / connection strings | Confidential — Security | S-009 | Confirm |
| "In camera" / privileged / pre-tabling | Restricted — Proceedings | S-006, S-017 | **S-006 → Legal** (counsel advice, not committee proceedings) |
| File saved in an HR site library | Confidential — People (auto-applied) | S-003 | Auto-applied, no prompt |

**Guardrails to set with the rules (slide 21):**
- Default label is **Internal**, not Confidential — don't over-classify routine work.
- **Downgrades require justification**; upgrades are free. Blank-label sites are **never** auto-set to Public (this directly rejects the `data_dictionary.csv` `processing_note`).
- Auto-labels are *suggestions to confirm*; the descriptor overrides above are the human-in-the-loop cases.

---

## 4. Copilot and agent scoping

**Access model (slide 18):** Copilot follows each user's existing access for Public / Internal / Confidential, and a Copilot answer inherits the **highest label of its sources**. **Restricted is excluded entirely** — Copilot will not read, summarise, or quote it. So Copilot's real risk is *not* Restricted content; it is **sensitive content mis-labelled down to Internal/Confidential and shared too widely**, which becomes instantly discoverable at scale.

**Configure before go-live, in order:**

1. **Remediate over-sharing first.** Remove the anonymous links on **S-005, S-006, S-011, S-019, S-022** (slide 19 says these are blocked for Internal/Confidential/Restricted anyway — their existence is legacy leakage). S-006 external counsel and S-022's 3,300-PII archive are the priorities.
2. **Fix the mislabels in §2** so auto-labelling and Copilot see the correct sensitivity — especially S-003, S-017, S-021, S-005, S-008, S-019.
3. **Apply the labels + descriptors** so encryption and DRM take effect (Confidential/Restricted); Restricted then drops out of Copilot automatically.
4. **Scope Copilot eligibility to E7 + active + human accounts.** In the 25-row licence sample only **16** qualify — exclude E5/E3 users (not Copilot-licensed in this rollout), the three disabled accounts still holding licences, and the service/shared accounts (`svc-backup`, `svc-scan`, `shared-mbox-co`). The "all 900 eligible" claim is not safe to configure against.
5. **Hold legacy/unreviewed content out of Copilot indexing** until reviewed — S-007 and S-022 especially. Review external-guest counts on S-011 (11), S-008 (6), S-005 (4).
6. **Copilot agents** use the same access model — point agent connectors only at reviewed sites, and confirm no agent can reach Restricted libraries.

**Go-live gate:** do not enable Copilot Assembly-wide until the five Critical sites (S-003, S-005, S-008, S-012, S-022) are relabelled and de-linked. Stage the rollout by remediated site, not by calendar date.

---

## 5. Sample-document labels

Three documents in `data/sample_documents/`, labelled per the deck:

| Document | Label | Descriptor | Reason |
|---|---|---|---|
| `leadership_pack_draft.txt` | **Restricted** | **Proceedings** | Five named leaders, unpublished Q4 financials, in-camera committee, unannounced staffing change — this is deck Scenario 3 (slide 17). |
| `procurement_card_review.txt` | **Confidential** | **Audit** | An internal review with findings, not yet final or shared — an audit/review finding (slide 8), team-level sensitivity, not named-individual. |
| `media_release_approved.txt` | **Public** | *(none)* | Approved by Communications and scheduled to post on the public website — Public content takes no descriptor (slides 8, 9). |
