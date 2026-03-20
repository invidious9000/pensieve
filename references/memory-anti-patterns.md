# Memory Anti-Patterns

Failure modes in Claude Code auto-memory that degrade performance over time.

## Structural

| # | Pattern | Signal | Fix |
|---|---------|--------|-----|
| 1 | **Broken symlinks** | Multi-account user, memory dir is regular dir not symlink | Move to shared, create symlinks for all accounts |
| 2 | **Divergent memories** | Same project has different memories in different accounts | Merge unique files into shared, replace with symlinks |
| 3 | **Orphaned memories** | Memory exists for project that's only used from one account | Migrate to shared if multi-account user, leave if single-account |
| 4 | **Missing MEMORY.md index** | Memory files exist but no MEMORY.md | Create index — without it, memories may not be loaded |
| 5 | **Index drift** | MEMORY.md references files that don't exist, or files exist without index entry | Reconcile: add missing entries, remove stale references |

## Content: Negativity Bias

| # | Pattern | Signal | Fix |
|---|---------|--------|-----|
| 6 | **All-negative ruleset** | >80% of feedback memories are "never/don't/stop" | Add positive counterweight memories ("what good looks like") |
| 7 | **Absolutist language** | "NEVER do X" when X has legitimate edge cases | Soften: "Don't do X when Y" — state the condition, not a blanket ban |
| 8 | **Fear-based paralysis** | Agent becomes overly cautious, asks permission for everything | Reduce "don't" density, add explicit "you SHOULD do X" rules |
| 9 | **Contradiction pairs** | Memory A says "never do X", Memory B implies doing X is fine | Resolve: either merge into one nuanced rule or delete the weaker one |

## Content: Staleness

| # | Pattern | Signal | Fix |
|---|---------|--------|-----|
| 10 | **Dead code references** | Memory names a function, file, or flag that no longer exists | Verify with grep/glob, update or delete |
| 11 | **Stale tool references** | Memory references tools, commands, or workflows that have been replaced | Check current .claude/commands/, skills, MCP tools |
| 12 | **Frozen project state** | Memory describes "current status" from weeks ago | Re-verify via git log / code inspection, update or delete |
| 13 | **Resolved incidents** | Memory describes a bug or incident that has been fixed | Delete if the fix is in the code; keep only if the lesson is broader |

## Content: Drift

| # | Pattern | Signal | Fix |
|---|---------|--------|-----|
| 14 | **Over-generalized rule** | User said "don't kill processes on port X" → memory says "never touch any processes" | Rewrite to match original intent with proper scope |
| 15 | **Lost context** | Memory states a rule but omits why, making edge cases unjudgeable | Add Why/How-to-apply structure |
| 16 | **Duplicate across projects** | Same rule written independently in 3+ projects | Promote to shared/global CLAUDE.md, delete per-project copies |
| 17 | **User profile gap** | No memory captures who the user is, their expertise, or preferences | Add user-type memory: role, technical depth, communication preferences |

## Content: Verbosity

| # | Pattern | Signal | Fix |
|---|---------|--------|-----|
| 18 | **War story memory** | 30+ lines retelling an incident blow-by-blow | Trim to rule + why + how-to-apply (10-15 lines max) |
| 19 | **Redundant overlap** | Two memories covering the same ground with different wording | Merge into one, delete the weaker |
| 20 | **Index bloat** | MEMORY.md approaching 200 lines (truncation threshold) | Reorganize by category, trim descriptions |
