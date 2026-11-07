---
name: grilling
description: Use when stress-testing a Zhengda Cup market research decision through dependency-aware rounds with recommended answers. Trigger before topic scoring, design freeze, analysis contract, report claims, or defense, and on phrases such as grill me, 拷问, 压力测试, 红队, or "这样应该可以吧".
---

# Grilling：分轮研究访谈

Adapted from Matt Pocock's MIT-licensed grilling. Apply these research-specific rules directly; do not require a native Skill tool or subagent.

- Start from the user-selected scope and existing decisions. A single research question does not require interviewing the entire competition workflow.
- Prefer a three-question quick pass at each freeze point; expand only when an answer creates a new dependency. Do not wait for the user to say "grill" if a high-cost decision is about to be frozen.
- Map decisions and dependencies. In each round ask all currently answerable questions, each with a recommended answer and reason; wait for the user before asking dependent questions. Follow the user's preferred question cadence.
- Read local evidence and consult available sources for facts yourself. Without subagents use your own tools; without network mark remote facts pending. Ask for private constraints you cannot access. Never invent searches, dispatches or answers.
- Establish research object, intended question and respondent access before sampling quotas, measurement and model choices. Distinguish plans from real survey results and observed samples from population claims.
- Finish with one plain paragraph explaining the complete study, then decisions, unknowns and remaining risks. A question needing real pilot evidence stays pending. Do not turn missing empirical evidence into endless interviews.
- Discussion is read-only for authoritative project state. After agreed decisions, follow the user's request to draft research artifacts; formal stage approval uses the existing evidence gates.

The complete parent package contains [the research guide](../../../references/grill-me.md), [the original snapshot](../../../references/upstream-skills/grilling/SKILL.md) and [MIT license](../../../licenses/mattpocock-skills/LICENSE). These are optional context when separately loaded; if absent, use the rules above without stalling or claiming the files were read.
