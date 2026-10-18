---
name: grill-me
description: Use when the user explicitly asks to grill or pressure-test a Zhengda Cup market survey idea, sampling plan, questionnaire, or analysis decision.
---

# Grill Me：正大杯研究决策

Adapted from Matt Pocock's MIT-licensed grill-me / grilling. This entry includes the interview behavior so a native Skill tool is optional. The original snapshots and license are in the complete parent package.

For an already specified execution task (such as CSV preflight), perform the task without starting an interview unless the user also requests one.

1. Limit the interview to the user's current decision. Read available materials first. Discussion alone does not initialize a project or change stage state.
2. Build a decision tree. Ask the current frontier together: only questions whose prerequisites are settled. Give each a recommendation and reason, then wait for answers. Honor a request for one question at a time.
3. Look up available facts yourself. Ask only for unavailable private facts or user choices. Without subagents, do the lookup yourself; without network, mark remote facts pending.
4. For market surveys, clarify the research question and reachable respondents before sample allocation, questionnaire details or models. Keep convenience-sample claims within the observed sample. Never fabricate survey results.
5. End within the agreed scope with a coherent paragraph explaining how the study will work, decisions made, unresolved facts and risks. Seek confirmation only for unresolved decisions; existing user instructions remain authoritative. Matters requiring a pilot remain pending rather than prolonging the interview.
6. After agreement, connect decisions to the research brief, sampling plan or analysis contract. Stage approval still requires evidence and review.

When the complete parent package is present, [the research guide](../../../references/grill-me.md) has examples; [the original](../../../references/upstream-skills/grill-me/SKILL.md) delegates to [grilling](../../../references/upstream-skills/grilling/SKILL.md). This adapted entry runs the steps above directly even if those paths or a Skill tool are unavailable.
