---
name: audit
description: "Full diagnostic: memory health, CLAUDE.md quality, cross-project duplication — everything that might be degrading Claude's behavior"
---

You are performing a comprehensive audit of everything that shapes Claude Code's behavior for this project: memory files, instruction files, and cross-project rule duplication.

Read these references from the pensieve plugin directory:
- `references/memory-anti-patterns.md` — structural and content anti-patterns
- `references/claude-frustration-patterns.md` — behavioral failure modes that generate corrective memories
- `references/instruction-patterns.md` — CLAUDE.md structure and density patterns

---

# Part 1: Memory Audit

## Phase 1: Structural Integrity

1. **Identify the memory directory** for the current project. Check if it's a symlink or regular directory.
2. **Multi-account check:** Look for `~/.claude-shared/` and `~/.claude-account*/` directories. If multiple accounts exist:
   - Check if memory is symlinked to shared storage
   - Check if other accounts have divergent memory for this project
   - Check if any accounts are missing the symlink entirely
3. **Index health:** Read MEMORY.md. Verify every referenced file exists. Check for memory files not listed in the index.

## Phase 2: Content Analysis

Read ALL memory files. For each one, evaluate:

### Negativity ratio
Count memories that are primarily "don't/never/stop" rules vs "do/prefer/always" rules. Report the ratio. If >75% negative, flag as **negativity bias** — this makes Claude overly cautious.

### Contradiction detection
- Does Memory A say "never X" while Memory B implies X is acceptable?
- Does a feedback memory contradict a workflow described in CLAUDE.md?
- Do two memories give conflicting advice for the same situation?

### Staleness detection
For memories that reference specific code artifacts (files, functions, tools, commands):
- Verify the artifact still exists (use grep/glob)
- Check if the artifact has been renamed or replaced

### Absolutist language
Flag memories using "NEVER", "ALWAYS", "MUST" without stating the condition/context. Is there a legitimate edge case where this rule shouldn't apply?

### Drift detection
For feedback memories: does the rule match what the user likely intended?
- Rule is broader than the incident that caused it
- Rule lacks "Why" context, making it unjudgeable
- Rule contradicts the user's observed behavior in other memories

### Verbosity
Flag memories >20 lines. Can they be trimmed without losing the rule?

### Missing coverage
- Is there a user profile memory? (who is the user, what's their expertise?)
- Are there any positive pattern memories? (what good looks like)
- Is there project context? (what's the project, what phase is it in?)

### Frustration pattern clustering
Using the frustration patterns reference, check if multiple memories are reactions to the same underlying Claude failure mode. Examples:
- 3 memories about "don't defer/skip/WONTFIX" → all symptoms of **Work Avoidance**
- Memories about "don't kill my processes" + "don't stash my changes" + "don't DELETE without WHERE" → all symptoms of **Collateral Damage**

When clustering is found, recommend replacing the cluster with one well-scoped positive rule addressing the root behavior.

## Phase 3: Cross-Project Duplication

If `~/.claude-shared/project-memory/` exists, scan ALL projects for feedback rules that express the same concept. A match doesn't require identical wording — it requires the same behavioral instruction. Report any rule appearing in 2+ projects — these are candidates for promotion to shared CLAUDE.md.

For each duplicate group, classify:
- **Universal preference** — applies regardless of project → promote
- **Domain-specific** — applies to a technology (e.g., .NET-specific) → promote only if user works exclusively in that domain
- **Project-specific** — only makes sense in one project → leave as-is

---

# Part 2: Instruction Audit

## Scope
Analyze all instruction sources:
1. **Project CLAUDE.md** — the repo's `CLAUDE.md`
2. **User CLAUDE.md** — `~/.claude/CLAUDE.md` (or shared equivalent)
3. **Project rules** — `.claude/rules/` directory if it exists
4. **Project settings** — `.claude/settings.json`

## Analysis Dimensions

### Positional ordering
Map the section order of CLAUDE.md. Classify each section as Behavioral / Reference / Status. Flag behavioral sections in the bottom half of the file — they should be in the top third.

### Instruction density
Flag sections >30 lines that contain reference material. Could they be condensed or lazy-loaded?

### Lazy-load opportunities
Content that is only relevant for specific tasks, available in other files Claude can read on demand, or duplicated across multiple files.

### Stale references
- Files and directories (do they exist?)
- Commands and tools (still valid?)
- Status claims ("X is not implemented" — is it now?)
- Numbers ("~340 tests" — still accurate?)

### Contradiction with memory
For each behavioral rule in CLAUDE.md, check if any memory contradicts it and vice versa.

### Missing sections
Check for absence of: code conventions, build commands, workflow protocol, known stubs/gaps, architecture overview.

---

# Output Format

### Health Dashboard
| Dimension | Score | Details |
|-----------|-------|---------|
| Memory structural | OK / WARN / BROKEN | symlinks, index drift |
| Negativity ratio | X neg / Y pos | ratio, bias level |
| Contradictions | N found | list |
| Stale items | N found | memories + instructions |
| Over-generalized rules | N found | list |
| Cross-project duplicates | N found | promotion candidates |
| CLAUDE.md ordering | GOOD / FAIR / POOR | behavioral rules position |
| Instruction density | GOOD / FAIR / POOR | wasted lines estimate |
| Lazy-load opportunities | N sections, ~M lines | recoverable context |
| Missing coverage | list | gaps in memory + CLAUDE.md |

### Findings (by severity)
For each finding:
- **What:** the specific issue
- **Where:** which file(s) and line range
- **Recommendation:** specific fix
- **Category:** memory / instruction / cross-project

IMPORTANT: Do NOT delete or modify any files during audit. Present all findings and recommendations. The user decides what to act on. Use `/optimize` to apply approved fixes.
