---
name: optimize
description: "Apply all fixes: memory consolidation, CLAUDE.md restructuring, cross-project rule promotion — the treatment pass"
---

You are applying fixes to Claude Code's memory, instruction files, and cross-project rules. This skill should be run AFTER `/audit` has identified issues, or the user has described specific problems.

If no prior audit exists in this conversation, run `/audit` first.

Read these references from the pensieve plugin directory:
- `references/claude-frustration-patterns.md` — behavioral failure modes and their correct behaviors
- `references/instruction-patterns.md` — CLAUDE.md structure patterns

---

# Part 1: Memory Fixes

Apply in this order (least destructive first):

### 1. Structural fixes
- Create missing symlinks for multi-account setups
- Reconcile MEMORY.md index with actual files
- Merge divergent memories from different accounts

### 2. Staleness fixes
- Verify code references still exist (grep/glob)
- Update memories referencing renamed/moved artifacts
- If referenced artifact is gone AND lesson is generic: rewrite without the specific reference
- If referenced artifact is gone AND lesson is artifact-specific: recommend deletion to user

### 3. Content consolidation
- Merge memories covering the same topic into one (keep stronger wording and best "Why")
- When multiple memories react to the same frustration pattern, consolidate into one positive rule addressing the root cause

### 4. Language fixes
- Soften absolutist rules that have edge cases: "NEVER do X" → "Don't do X when Y — the exception is Z"
- Ensure every feedback memory has: Rule → Why → How to apply
- Trim war-story memories to ≤15 lines

### 5. Balance fixes
- If negativity ratio >75%: draft a positive-patterns memory derived from the user's actual confirmed behavior (not a generic template). Ask to confirm before saving.
- If no user profile memory exists: draft one from observable signals. Ask to verify.
- If no project context memory exists and the project has non-obvious context: draft one

### 6. Index reorganization
- Group MEMORY.md entries by category
- Ensure descriptions are concise (one line each)
- Keep index well under 200 lines

---

# Part 2: Instruction Fixes

### 1. Positional reordering
Move sections to respect positional attention bias:
- **Top third:** Project identity, code conventions, workflow protocol, hard constraints
- **Middle third:** Build/test commands, solution structure, architecture (condensed + lazy-load pointers)
- **Bottom third:** Implementation status, known gaps, remaining work

The specific ordering should be driven by observed failures — put what Claude gets wrong most often near the top.

### 2. Density reduction
- Replace per-item detail with grouped summaries + lazy-load pointers
- Remove frequently-changing metrics (line counts, exact numbers)
- Condense multi-sentence descriptions to single-line summaries
- Preserve ALL information — move detail to referenced files, don't delete

### 3. Lazy-load extraction
- If a design doc already exists covering inlined content, replace with pointer
- Do NOT create new files just to lazy-load — only extract to existing files
- Pointers should be specific: "See `design/architecture.md` for full service catalog"

### 4. Stale reference updates
- Update stale counts by checking actual numbers
- Remove references to files/tools that no longer exist
- Update "not implemented" items that have been implemented

### 5. Contradiction resolution
- CLAUDE.md stale (code changed): update CLAUDE.md
- Memory stale (lesson no longer applies): update or recommend deletion
- Genuine disagreement: flag for user decision

---

# Part 3: Cross-Project Promotion

For rules identified as duplicated across 2+ projects:

1. Write a generalized version for shared CLAUDE.md (strip project-specific incidents, keep the principle)
2. Frame positively ("Do X" not "Don't Y")
3. Show the proposed addition and which per-project memories become redundant
4. After user approves: add to shared CLAUDE.md, retire redundant per-project memories

---

# Execution Rules

- **Preview every change** before writing. Show the user what will change and why.
- **Never delete a memory without explicit user confirmation.**
- **When merging memories,** show both originals and proposed merged version side by side.
- **Show a complete diff** of proposed CLAUDE.md changes before writing.
- **Never remove information** — move it to a referenced file or condense it.
- **Preserve the user's voice** — reorder and trim, don't rewrite their phrasing.
- **After all fixes,** show a before/after summary: files changed, new negativity ratio, new MEMORY.md, CLAUDE.md line savings.
