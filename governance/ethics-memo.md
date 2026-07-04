# Ethics Memo — to the Director

**From:** Senior Data Strategist, ITD
**Re:** Privacy and ethics of the Copilot go-live — and four requests I would handle differently
**Bottom line:** The technology is ready; the *content* is not. Copilot doesn't create new access — it makes whatever is already over-shared instantly findable at scale. We should remediate first, then go live. I also want to flag four things in the brief before we act on them.

### The core privacy risk
Our scan found sensitive content sitting at the wrong sensitivity: HR benefits data with SINs and constituency casework labelled for broad internal access, a 3,300-record personal-data archive and a privileged legal library reachable through **anonymous links** (no sign-in required). Today that exposure is latent — someone has to go looking. After go-live, a staff member can simply ask Copilot. Turning on Copilot over this content, unremediated, converts a set of quiet misconfigurations into a search engine for our most sensitive material. The fix is not to slow Copilot down; it's to relabel and de-link the ~10 sites identified in the risk view before we enable it.

### Four requests I would handle differently

**1. The "ten individuals to have a quiet word with." I recommend we not do this.** It asks us to build a watchlist of named employees from the content they touch, before anyone has done anything wrong. Three problems: the scan is **site-level**, so we cannot actually attribute it to individuals (the "owners" are shared mailboxes and team accounts like `hr.team@` and `allstaff@`); handling personal and HR data **is the job** of the HR and Member Support teams, so a "most personal content" ranking simply re-lists them for doing their work; and profiling staff for pre-emptive scrutiny is exactly the kind of employee-surveillance use that draws FOIPPA and labour scrutiny. **Better:** target the *sites*, not the people. Fix the labels, brief the teams that own the high-risk libraries as a group, and let audit logging (which runs on every label) surface genuine misuse after go-live.

**2. "Classify everything to Protected A/B/C." I would not.** Our own deck (slide 6) is explicit: apply the Assembly's labels — Public / Internal / Confidential / Restricted — to Assembly content, and *don't* carry over BC Government names. Mixing schemes would confuse staff and break auto-labelling. I'm happy to provide a Protected A/B/C ↔ Assembly crosswalk as a reference for people coming from ministry work, but the applied labels stay ours.

**3. "Confirm our FOIPPA compliance in the memo." I can't sign that off, and neither should ITD alone.** Compliance is a legal determination, and this scan actively surfaces likely problems: personal information exposed via anonymous links (a reasonable-security concern under FOIPPA s.30) and a pre-2015 archive we appear to be retaining with no classification or purpose. What I can do is flag these for the privacy office and Legal and track remediation — but a clean bill of health here would be a rubber stamp, not a finding.

**4. The data dictionary told us to blanket-label every blank item "Public" to clear the backlog. We rejected it.** Two of those blank sites are the Member Services portal and the Old Records archive — the latter holds 3,300 personal-data matches. Publishing them to clear a queue would have been a mass privacy breach. Blank labels are held for review, not defaulted to Public.

### What I recommend
Stage the rollout by remediated site, not by date. Remove the anonymous links this week, relabel the Critical sites, scope Copilot to genuine E7 users (only 16 of 25 sampled accounts qualify — the "900 eligible" figure is wrong), and refer the FOIPPA exposures to the privacy office. Then go live with confidence.
