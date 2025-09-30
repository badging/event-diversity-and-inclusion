# Reviewer Spotlight

## Overview

The CHAOSS Event DEI badging program depends on the dedication of reviewers who volunteer their time to assess applications. While their work is essential, it has not always been consistently visible or recognized in the repository.

The Reviewer Spotlight feature was created to address this gap by:

* Recognizing reviewers directly in the repository.
* Providing visibility that can be showcased on résumés, portfolios, or with potential collaborators.

This visibility helps encourage both sustained and returning contributions.

## Problem Statement

* Reviewer activity is invisible to new contributors and external stakeholders.
* Past reviewers (inactive reviewers) have no acknowledgment of their prior impact.
* Returning reviewers have no visible way to celebrate their renewed engagement.

---

## Design Principles

1. Stats are pulled directly from closed GitHub issues.
2. A 6-month window distinguishes active reviewers from past reviewers.
3. Badges reward cumulative contributions:

   * 🌱 **New Reviewer** → 1–4 reviews
   * 🥉 **Bronze Reviewer** → 5–9 reviews
   * 🥈 **Silver Reviewer** → 10–29 reviews
   * 🥇 **Gold Reviewer** → 30–49 reviews
   * 🏆 **Platinum Reviewer** → 50+ reviews
4. Recognition is maintained for reviewers who are no longer active.
5. Returning reviewers receive special acknowledgment when they re-engage.
6. The spotlight is automatically updated weekly via GitHub Actions.

---

## How It Works

* **Data source:** Closed issues in the repository, with reviewers identified from issue assignees.
* **Activity tracking:**

  * **Active reviewers:** closed reviews in the last 6 months.
  * **Past reviewers:** reviewers with no reviews in the last 6 months but with prior contributions.
  * **Welcome Back:** past reviewers who return after inactivity.
* **README integration:** The spotlight appears in `README.md` between markers:

  ```
  <!-- REVIEWER_SPOTLIGHT_START -->  
  … generated content …  
  <!-- REVIEWER_SPOTLIGHT_END -->  
  ```
* **Automation:** A GitHub Action runs a Python script weekly to refresh stats.

---

## Example Output

### 🙌 Reviewer Spotlight

#### Active Reviewers (last 6 months)

| Reviewer | Reviews (last 6 months) | Total Reviews | Last Review Date | Badge Level | Events Reviewed |
|----------|----------------------|---------------|------------------|-------------------|--------|
| [Anita-ihuman](https://github.com/Anita-ihuman) | 3 | 38 | 2025-09-08 | 🥇 Gold | [View](https://github.com/badging/event-diversity-and-inclusion/issues?q=is:issue+assignee:Anita-ihuman+is:closed) |
---

#### Past Reviewers

| [germonprez](https://github.com/germonprez) | 25 | 2024-03-18 | 🎖️ Honour | [View](https://github.com/badging/event-diversity-and-inclusion/issues?q=is:issue+assignee:germonprez+is:closed) |

#### Welcome Back Highlight

* @charlie returned in Sep 2025 after a break! 🎉

*Last Updated: 2025-09-30*

---

## How to Contribute or Extend

* **Local testing:** Clone your fork and run `scripts/update_reviewers.py` with your GitHub token.


---

## Impact

* Brings visibility to non-code contributions.
* Encourages reviewers to stay active.
* Maintains recognition for past contributors.
* Strengthens a culture of appreciation and inclusivity in the CHAOSS community.
