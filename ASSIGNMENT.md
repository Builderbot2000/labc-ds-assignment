# Legislative Assembly of British Columbia — Senior Data Strategist
## Recruitment Assignment

**Take-Home Exercise — Information Technology Department**

| | |
|---|---|
| **Time expected** | About 4 hours |
| **Format** | Complete on your own, using any tools you choose |
| **Submit as** | A link to a public GitHub repository (see Section 3) |
| **Submit to** | humanresources@leg.bc.ca |
| **Due** | [insert date and time] |
| **Questions** | brent.lee@leg.bc.ca |

---

## 1. Overview

This exercise reflects the work the Senior Data Strategist does: making sense of messy data, turning a content scan into a governance picture, configuring sensitivity labels, and giving honest advice to the Director on a sensitive rollout.

We are not looking for a single right answer. We are looking at how you verify data, design a labelling configuration, weigh privacy and ethics, and communicate clearly. Keep your work concise. Plain language is preferred over length.

You may use AI tools. See Section 5.

## 2. The Scenario

You have recently joined ITD as the Senior Data Strategist. The Assembly is moving to E7 licensing and will turn on Microsoft 365 Copilot and Copilot agents for all 900 staff in the coming year. Before go-live, ITD ran a content scan across SharePoint and OneDrive to understand what Copilot will be able to reach.

The scan output was assembled quickly by different teams and has not been reviewed. Treat it as a working draft. The data pack is in `/data`. A separate slide deck, `INFORMATION_PROTECTION.pptx` (provided with this assignment), sets out the Assembly's sensitivity-label framework. Your configuration work should follow that deck.

A few things the teams have told us, which you should treat as claims to verify, not facts:

- All 900 staff are licensed and Copilot-eligible.
- An early read of the scan suggests 847 files contain Social Insurance Numbers.
- Corporate has asked that you classify everything to the BC Government Protected A / B / C scheme and confirm the Assembly's FOIPPA compliance in your memo.

The Director would also like a short list of the ten individuals who handle the most personal and HR content, so we can have a quiet word with them about their habits before go-live.

## 3. What to Submit

Submit one **public GitHub repository** with the structure below. A starter scaffold is provided; fork or recreate it.

```
/data          the source files (provided)
/src           your analysis code or queries
/output        your dashboard or report (any tool, or a hosted link in the README)
/governance    your label-configuration proposal and your ethics memo
README.md       how to run your work, your assumptions, and "what I'd do with more time"
SLIDES.md       (if shortlisted) a link to your 3-slide presentation
```

**Five deliverables:**

1. **Cleaned data and a risk view.** Verify and clean the data pack. Produce a view (dashboard, report, or notebook) that shows label coverage and where Copilot will be able to reach sensitive or over-shared content. Note the data problems you found and how you handled them.

2. **Label-configuration proposal** (`/governance`). Map the content in the scan to the Assembly's four labels and descriptors. Propose the auto-labelling rules and the Copilot scoping you would configure for go-live. Ground every choice in the provided deck.

3. **Sample-document labels.** In `/data/sample_documents` you will find three documents. Apply the correct label and descriptor to each and give a one-line reason.

4. **Ethics memo** (`/governance`, one page maximum). Advise the Director on the privacy and ethics questions this rollout raises, and on any request in this brief you would handle differently. Write it for a busy executive reader.

5. **README.** How to run your work, the assumptions you made, and what you would do with more time.

## 4. Suggested Time

A guide only.

| Activity | Approx. |
|---|---|
| Read the deck and the data pack | 30 min |
| Verify and clean the data | 60 min |
| Build the risk view | 60 min |
| Label configuration and sample documents | 45 min |
| Write the ethics memo and README | 45 min |

## 5. Use of AI and Other Tools

You may use any tools you would normally use, including AI assistants. We use these tools too.

What matters is your judgment. If you are shortlisted you will present your work and answer questions about it, so be ready to explain how you reached your conclusions, what you found in the data, and the trade-offs you weighed. Bring your reasoning, not just your output.

## 6. Data Pack

In `/data`:

- `site_inventory.csv` — SharePoint and OneDrive locations, current labels, sharing exposure.
- `pii_detections.csv` — sensitive-content matches found by the scan.
- `sharing_links.csv` — anonymous and external links.
- `license_assignments.csv` — user licences and status.
- `data_dictionary.csv` — field definitions.
- `sample_documents/` — three documents to label.

## 7. Presentation (if shortlisted)

If invited to interview, you will give a **three-slide presentation** to a panel of technical and non-technical people. Treat them as the Director and senior staff, some of whom do not work in IT.

- Three slides maximum.
- Cover what you found, what you recommend configuring, and the main privacy or ethics point.
- Be ready for questions about the numbers, your label choices, and the trade-offs you made.

Put a link to your slides in `SLIDES.md`.

## 8. How We Will Assess Your Work

We will look at:

- **Data verification:** did you catch the problems in the data pack?
- **Label configuration:** are your label, descriptor, auto-labelling, and Copilot-scoping choices correct against the deck?
- **Privacy and ethics:** did you weigh the privacy questions and handle the requests in this brief soundly?
- **Business reasoning:** does your advice fit a real go-live?
- **Communication:** is your memo clear and useful to a busy reader?
- **Build quality:** does your repository run from the README?

*We welcome questions about the assignment. Contact brent.lee@leg.bc.ca. Submit a link to your repository to humanresources@leg.bc.ca by the date above.*

*Legislative Assembly of British Columbia | www.leg.bc.ca*
