---
name: audit
description: "Full diagnostic: memory health, CLAUDE.md quality, cross-project duplication — everything that might be degrading Claude's behavior"
---

You are performing a comprehensive audit of everything that shapes Claude Code's behavior: memory files across ALL projects, instruction files, and cross-project patterns.

Read these references from the pensieve plugin directory:
- `references/memory-anti-patterns.md` — structural and content anti-patterns
- `references/claude-frustration-patterns.md` — behavioral failure modes that generate corrective memories
- `references/instruction-patterns.md` — CLAUDE.md structure and density patterns

---

# Part 1: Memory Audit (ALL projects)

This audit covers ALL projects with memory, not just the current one. Scan `~/.claude-shared/project-memory/*/` (or `~/.claude/projects/*/memory/` for single-account users) to find every project that has memory files.

## Phase 1: Structural Integrity (all projects)

For EACH project with a memory directory:

1. **Symlink check:** Is memory a symlink to shared storage, or a regular directory? Regular dirs in a multi-account setup are broken.
2. **Multi-account coverage:** Do all accounts have the symlink? Are any accounts missing it?
3. **Divergent memories:** Do any accounts have a regular dir with different content than shared?
4. **Index health:** Read MEMORY.md. Verify every referenced file exists. Check for memory files not listed in the index.
5. **MEMORY.md format:** Is MEMORY.md being used as a thin index (correct) or does it have content inlined directly (incorrect)?
   - Correct: MEMORY.md contains only links to separate files with brief descriptions
   - Incorrect: MEMORY.md contains full memory content (project status, architecture, bug reports, etc.) inlined directly
   - This matters because: inlined content lacks YAML frontmatter (type/name/description) that helps the system judge relevance, and MEMORY.md truncates after ~200 lines — silently dropping content
   - Report each project's MEMORY.md line count and whether content is inlined vs. indexed
   - Flag any MEMORY.md over 100 lines as a truncation risk

## Phase 2: Content Analysis (all projects, all memory types)

Memory files have a `type` field in their YAML frontmatter: `feedback`, `user`, `project`, or `reference`. Each type has different quality criteria and failure modes.

For EACH project that has memory files, read ALL memory files. Classify by type and evaluate:

### Type-specific checks

**feedback memories** (behavioral rules from corrections):
- Has three-part structure? (Rule → Why → How to apply)
- Is it a reaction to a known frustration pattern? (cluster with others)
- Is the rule scoped correctly? (not over-generalized from the incident)
- Does the rule still apply? (was the underlying issue fixed in code?)
- Is it redundant with a rule in CLAUDE.md? (already promoted)

**user memories** (user profile, preferences, expertise):
- Is it still accurate? (roles and preferences change)
- Does it exist at all? (missing user profile is a common gap — only needs to exist once across all projects or in user-level CLAUDE.md)
- Is it consistent across projects? (different projects shouldn't describe the user differently)

**project memories** (ongoing work, goals, status):
- Is the status current? (project memories with dates — check if they're stale)
- Does it reference work that's been completed? (convert relative dates to check)
- Is it duplicating what's in CLAUDE.md or the code? (project state derivable from code shouldn't be in memory)

**reference memories** (pointers to external systems):
- Does the external resource still exist / is the URL still valid?
- Is the pointer still relevant to current work?

**untyped memories** (missing frontmatter or type field):
- Flag as malformed — these can't be filtered by relevance and may confuse the system
- Recommend adding proper frontmatter

### Negativity ratio (per project)
Count feedback memories that are primarily "don't/never/stop" rules vs "do/prefer/always" rules. Report the ratio per project. If >75% negative, flag as **negativity bias**. Only count feedback-type memories for this ratio — user/project/reference types are naturally neutral.

### Contradiction detection (per project AND cross-project)
- Within a project: Does Memory A say "never X" while Memory B implies X is acceptable?
- Cross-project: Do two projects have memories giving contradictory advice for the same situation?
- Memory vs CLAUDE.md: Does a memory contradict a rule in any CLAUDE.md (project or user-level)?

### Staleness detection (per project)
For memories referencing specific code artifacts (files, functions, tools, commands):
- Verify the artifact still exists (grep/glob — only for the current project's codebase, skip for other projects where you can't access the code)
- Check if the artifact has been renamed or replaced
- For other projects: flag memories that reference specific code paths as "unverifiable from here — check when working in that project"

### Absolutist language (per project)
Flag memories using "NEVER", "ALWAYS", "MUST" without stating the condition/context. Is there a legitimate edge case?

### Drift detection (per project)
For feedback memories: does the rule match what the user likely intended?
- Rule is broader than the incident that caused it
- Rule lacks "Why" context, making it unjudgeable
- Rule contradicts the user's observed behavior in other memories

### Verbosity (per project)
Flag memories >20 lines. Can they be trimmed?

### Missing coverage (per project)
- Is there a user profile memory? (Only needs to exist in one project OR user-level CLAUDE.md — check if it exists anywhere)
- Are there any positive pattern memories?
- Is there project context where the project has non-obvious context?

### Frustration pattern clustering (across all projects)
Using the frustration patterns reference, check if memories across ANY projects are reactions to the same underlying Claude failure mode. This is the most important cross-project analysis — it reveals which behavioral patterns the user struggles with most.

When clustering is found, recommend replacing the cluster with one well-scoped positive rule in the shared CLAUDE.md.

## Phase 3: Cross-Project Duplication

Scan ALL projects for feedback rules expressing the same concept. A match doesn't require identical wording — it requires the same behavioral instruction.

For each duplicate group, classify:
- **Universal preference** — applies regardless of project → promote to shared CLAUDE.md
- **Domain-specific** — applies to a technology → promote only if user works exclusively in that domain
- **Project-specific** — only makes sense in one project → leave as-is
- **Already promoted** — rule already exists in shared/user CLAUDE.md → per-project copy is redundant

---

# Part 2: Instruction Audit

## Scope
Analyze all instruction sources:
1. **User CLAUDE.md** — `~/.claude/CLAUDE.md` (or `~/.claude-shared/CLAUDE.md`)
2. **Project CLAUDE.md** — the current repo's `CLAUDE.md`
3. **Project rules** — `.claude/rules/` directory if it exists
4. **Project settings** — `.claude/settings.json`

## Analysis Dimensions

### Positional ordering
Map the section order of each CLAUDE.md. Classify each section as Behavioral / Reference / Status. Flag behavioral sections in the bottom half — they should be in the top third.

### Instruction density
Flag sections >30 lines that contain reference material. Could they be condensed or lazy-loaded?

### Lazy-load opportunities
Content only relevant for specific tasks, available in other files, or duplicated across files.

### Stale references
- Files and directories (do they exist?)
- Commands and tools (still valid?)
- Status claims ("X is not implemented" — is it now?)
- Numbers ("~340 tests" — still accurate?)

### Contradiction with memory
For each behavioral rule in CLAUDE.md, check if any memory (in any project) contradicts it and vice versa.

### Missing sections
Check for absence of: code conventions, build commands, workflow protocol, known stubs/gaps, architecture overview.

---

# Output Format

### Health Dashboard
| Dimension | Score | Details |
|-----------|-------|---------|
| Memory structural | OK / WARN / BROKEN | per-project breakdown |
| MEMORY.md format | N correct / M inlined | truncation risks |
| Negativity ratio | per-project ratios | worst offenders |
| Contradictions | N found | within-project + cross-project |
| Stale items | N found | memories + instructions |
| Over-generalized rules | N found | list |
| Cross-project duplicates | N found | promotion candidates |
| Frustration clusters | N patterns | top clusters across all projects |
| CLAUDE.md ordering | GOOD / FAIR / POOR | per-file |
| Instruction density | GOOD / FAIR / POOR | wasted lines estimate |
| Lazy-load opportunities | N sections, ~M lines | recoverable context |
| Missing coverage | list | user profile, positive patterns, project context |

### Per-Project Summary
For each project with memory, one-line summary: file count, negativity ratio, key issues.

### Findings (by severity)
For each finding:
- **What:** the specific issue
- **Where:** which project, file(s), and line range
- **Recommendation:** specific fix
- **Category:** structural / content / cross-project / instruction

IMPORTANT: Do NOT delete or modify any files during audit. Present all findings and recommendations. The user decides what to act on. Use `/optimize` to apply approved fixes.
