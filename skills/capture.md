---
name: capture
description: "Structured feedback capture: prevents memory drift by asking What/Why/When/Exceptions before writing"
---

The user wants to capture a lesson, preference, or rule as a memory. Your job is to ensure it's captured accurately — not over-generalized, not under-specified, and structured for future usefulness.

## Why This Exists

Memories written by Claude often drift from the user's actual intent:
- User says "don't kill processes on port 5000 because it takes down my browser" → Claude writes "never touch any processes"
- User says "run tests before committing" → Claude writes "always run the full test suite before every commit" (when they meant: run relevant tests)

This skill prevents that drift through structured extraction.

## Capture Protocol

### Step 1: Extract the rule
Ask the user (if not already clear from context):

> **What's the rule?** State it as a single sentence. What should Claude do or not do?

### Step 2: Extract the reason
Ask:

> **Why?** What happened that made this important? (The incident helps future Claude judge edge cases.)

### Step 3: Extract the scope
Ask:

> **When does this apply?** Always? Only in this project? Only with certain tools? Only in certain situations?

### Step 4: Extract exceptions
Ask:

> **Are there exceptions?** When is it OK to break this rule? (If "never", say so — but most rules have edge cases.)

### Step 5: Classify
Based on the answers, determine:
- **Type:** feedback (behavioral rule), user (personal preference), project (project-specific context), reference (pointer to external info)
- **Scope:** this project only, or all projects (→ shared CLAUDE.md candidate)

### Step 6: Draft and confirm
Write the memory file content and show it to the user BEFORE saving:

```markdown
---
name: {descriptive_name}
description: {one-line summary — specific enough to judge relevance}
type: {feedback|user|project|reference}
---

{Rule statement}

**Why:** {Incident or motivation}

**How to apply:** {When/where this kicks in. Include exceptions.}
```

Ask: "Does this capture what you meant? Anything to adjust?"

### Step 7: Save
Only after user confirms:
1. Write the memory file
2. Add entry to MEMORY.md index
3. If user indicated this is universal (all projects): suggest running `/optimize` to promote to shared CLAUDE.md

## Rules

- **Never paraphrase the user's rule.** Use their words. If you need to restructure for clarity, show them the restructured version.
- **Never broaden the scope.** If the user said "don't do X with tool Y", don't write "never do X".
- **Always include Why.** A rule without context is unjudgeable in edge cases.
- **Keep it under 15 lines.** If the memory needs more, the rule is too complex — split it.
- If the user says "just remember X" without wanting a structured process, still write it with the three-part structure — but skip the interrogation. Infer What/Why/When from context and confirm once.
- Read `references/claude-frustration-patterns.md` from the pensieve plugin directory. If the feedback the user is giving matches a known frustration pattern (work avoidance, shallow fixes, collateral damage, etc.), note this in the memory's "Why" section. This helps future audits cluster related corrections.
- When you recognize the user is correcting a known frustration pattern, suggest promoting the rule to shared/global CLAUDE.md instead of per-project memory — these patterns are not project-specific.
