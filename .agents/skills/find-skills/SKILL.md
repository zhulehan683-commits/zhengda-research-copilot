---
name: find-skills
description: Use when finding or installing additional skills for market research, survey statistics, citations, reports, or defense deliverables.
---

# Find Skills：按研究任务发现能力

Adapted from Vercel's MIT-licensed find-skills. These instructions are self-contained and use project-scope installation by default.

1. Identify the missing output and inspect the current session's available skills/tools. Use existing suitable capabilities before searching.
2. With network, check skills.sh and run `npx skills find "<specific task>"` when npm is available. Without npm, use available GitHub/web search. Offline, say that no remote query was made, list intended search terms and continue available local work. Never invent candidates or popularity counts.
3. Read candidate SKILL.md, dependencies and scripts. Verify the actual output format, statistical assumptions, data destination, license and pinned source commit. Stars/downloads are discovery hints, not quality thresholds.
4. Recommend the fewest suitable candidates with purpose, inputs/outputs, source, dependencies, installation command and unverified points.
5. Install only within the user's authorized scope. Project default: `npx skills add <owner/repo> --skill <name> -a <agent> -y`. Add `-g` only when the user wants global use. Do not bulk-update other skills or overwrite existing copies silently.
6. Verify files, native discovery, script execution and model results separately. Text-only work may have no command; record actual execution honestly.
7. External skills produce bounded artifacts. They do not change the research population, raw data or authoritative stage state. Obtain authorization and remove identifiers before external data processing. Reuse content in the repository only after checking distribution rights and preserving source/license.

The CLI flag `-y` only skips command-line prompts after installation is authorized; it does not grant authority. If npm, network or authorization is unavailable, mark an install as planned/not executed. Recalled offline candidates must be labeled unverified, never reported as search findings.

The complete parent package contains [the research guide](../../../references/find-skills.md), [original snapshot](../../../references/upstream-skills/find-skills/SKILL.md) and [MIT license](../../../licenses/vercel-labs-skills/LICENSE). Use this entry's project defaults over the original's global-install examples.
