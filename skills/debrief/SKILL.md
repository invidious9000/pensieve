---
name: debrief
description: "End-of-session retrospective: extract corrections, decisions, and unfinished threads — route to memory, CLAUDE.md, or handoff doc"
---

You are conducting an end-of-session retrospective. Your job is to sweep the current session's transcript, extract everything worth preserving, classify each finding by destination, and write approved items — so nothing hard-won is lost when the session ends.

Read `references/claude-frustration-patterns.md` from the pensieve plugin directory to classify corrections against known patterns.

## When To Use

Run this at the end of a substantive session — one where real work was done, decisions were made, or corrections were given. Not useful after trivial sessions (quick checks, single-command tasks).

## Step 1: Find the Current Session Transcript

The current session's JSONL file is the most recently modified `.jsonl` for this project:

```bash
project_dir=$(echo "$PWD" | sed 's|/|-|g; s|^-||')
ls -t ~/.claude/projects/"$project_dir"/*.jsonl ~/.claude-account*/projects/"$project_dir"/*.jsonl 2>/dev/null | head -1
```

If this returns nothing or points to a tiny file, the project encoding may differ. Fall back to:
```bash
find ~/.claude/projects ~/.claude-account*/projects -name "*.jsonl" -type f -newer /tmp -mmin -120 2>/dev/null | grep -v subagents | xargs ls -t 2>/dev/null | head -5
```

Pick the file that matches the current project and session. If ambiguous, ask the user.

## Step 2: Extract Findings

Scan the transcript for five categories of preservable content. Read selectively — scan for signal patterns, don't load the entire transcript into context.

### 2a: User Corrections

**What to look for:**
- Lines containing `"User rejected tool use"` + the following user message (contains the correction)
- User messages with correction language: "no", "don't", "stop", "wrong", "actually", "I meant", "not what I", "that's not"
- User messages that redirect approach: "instead", "try X", "the real issue is", "let me clarify"
- Terse user responses (<20 chars) after long assistant output (note but don't over-weight — could be approval)

**For each correction, extract:**
- What Claude did wrong (the behavior)
- What the user wanted instead (the rule)
- How forceful the correction was (casual redirect vs. forceful stop — affects routing)

### 2b: Design Decisions

**What to look for:**
- Trade-off discussions: "we could do X or Y", "the reason for X over Y"
- Architecture choices: new patterns introduced, library selections, API design choices
- User statements of intent: "the goal is", "what we're building", "the approach should be"
- Constraints discovered through discussion: "turns out X can't do Y", "X requires Y"

**For each decision, extract:**
- What was decided
- Why (the rationale or constraint that drove it)
- What alternatives were considered and rejected

### 2c: Hard-Won Debugging Lessons

**What to look for:**
- Investigation chains: 3+ sequential Read/Grep/Bash calls exploring a problem before a fix
- Root cause discoveries: "the actual issue was", "found it", "the problem is that"
- Surprising behavior: things that worked differently than expected

**For each lesson, extract:**
- The symptom (what was observed)
- The root cause (what was actually wrong)
- Why it was non-obvious (what made this hard to find)

### 2d: Discovered Constraints

**What to look for:**
- Framework/library limitations encountered during implementation
- Platform-specific behaviors discovered
- Integration edge cases: API quirks, protocol specifics, tooling limitations

**For each constraint, extract:**
- The constraint itself
- How it was discovered (what broke or almost broke)
- The workaround or design accommodation made

### 2e: Unfinished Threads

**What to look for:**
- TODO/FIXME/HACK markers written during the session
- User mentions of follow-up work: "we'll need to", "later we should", "don't forget to", "next step is"
- Implementation shortcuts taken with acknowledged debt: "for now", "temporary", "placeholder", "hardcoded"
- Tests skipped or deferred
- User-requested features or fixes that were discussed but not started
- Work that was started but not completed (partially implemented features, incomplete refactors)

**For each thread, extract:**
- What needs to be done
- Why it wasn't done now
- Any context that would help a future session pick it up

### 2f: Validated Approaches

Sessions don't only produce problems — they also validate approaches worth repeating. Only capturing negatives mirrors the negativity bias the rest of Pensieve exists to fix.

**What to look for:**
- User explicitly confirming an approach: "yes exactly", "perfect", "that's the right call", "keep doing that"
- An approach that was non-obvious but worked well (Claude or the user chose something unconventional and it paid off)
- Patterns established during the session that should become convention: naming choices, file organization, testing strategies, API design patterns
- Workflow or process decisions the user validated: PR strategy, commit granularity, review approach

**For each validated approach, extract:**
- What was done
- Why it worked (or why the user preferred it)
- When to repeat it (scope: this project? this kind of task? always?)

**Don't over-capture here.** Only note approaches that are non-obvious or that future sessions might not naturally reproduce. "Writing tests" is not a finding. "Testing gRPC services by hitting the reflection endpoint instead of mocking the client" is.

## Step 3: Resolve Superseded Findings

Sessions are not linear — decisions get reversed, hypotheses get disproven, corrections get walked back. Before presenting findings, resolve the timeline:

**Design decisions:** If the session contains "let's use approach A" followed later by "A won't work, switching to B" — only B is a finding. A is context for *why* B was chosen (include it in B's rationale), not a separate finding. Look for reversal language: "actually", "instead", "that won't work", "scratch that", "let's go with", "changed my mind".

**Debugging lessons:** If investigation went "the issue is X" → [more work] → "wait, it's actually Y" — only Y is the root cause. X is a red herring. The lesson might be "X looked like the cause because Z, but the real issue was Y" — the misdiagnosis path can be valuable context if it was non-obvious, but the finding is Y, not X.

**Corrections:** If the user corrected Claude, Claude adjusted, and the user later said "actually the first way was fine" — the net correction is zero. Don't capture it. If the user refined a correction ("don't do X... well, don't do X *when* Y"), capture only the final, refined version.

**Constraints:** If a constraint was discovered and then a workaround was found that makes it irrelevant, the constraint may not be worth capturing. Only persist constraints that still affect the codebase or future decisions.

**General rule:** Read the transcript chronologically. When a later finding contradicts or supersedes an earlier one, keep only the final state. Include the journey as context in the "Why" field when the path to the final answer is itself informative.

## Step 4: Deduplicate and Detect Escalations

Before presenting findings, check what's already captured — and whether any of it failed.

### 4a: Memory dedup

1. List all memory files in the project's memory directory (not just today's)
2. Read their content
3. For findings that match an existing memory: mark as "already exists" and remove from the findings list

Also check memory files modified *today* — these were likely captured during this session (via `/capture` or auto-memory). Findings covered by today's memories are definite duplicates.

### 4b: CLAUDE.md dedup

Read the current project CLAUDE.md and global CLAUDE.md (`~/.claude-shared/CLAUDE.md` or `~/.claude/CLAUDE.md`). Check if any findings duplicate rules already present in either file. If a rule was added to CLAUDE.md during this session, it's a definite duplicate — skip it.

### 4c: Escalation detection

This is the most valuable part of dedup. While reading existing memories in 4a, check for a specific failure mode: **a correction from this session that an existing memory should have prevented.**

How to detect:
1. For each user correction extracted in Step 2a, identify the *behavior* Claude exhibited (e.g., "killed processes by port", "suggested deferring the work", "didn't run tests")
2. For each existing feedback memory, identify the *rule* it encodes (e.g., "use precise process killing", "do the work, don't suggest deferring", "run tests before committing")
3. If a correction's behavior matches what a memory's rule was supposed to prevent → **escalation candidate**

The match doesn't need to be exact. If the memory says "don't kill by port" and the correction was "stop doing `fuser -k`", that's the same behavior class. Use judgment.

For each escalation candidate, record:
- The existing memory file (name and path)
- The correction from this session that it failed to prevent
- Whether this is a routing failure (memory exists but wasn't loaded for this task) or an effectiveness failure (memory was likely loaded but Claude ignored it)

These will be highlighted prominently in Step 6.

## Step 5: Classify and Route

For each remaining finding, assign a destination:

### → Memory (feedback type)

**When:** User corrected Claude's behavior. The correction is specific and scoped. It doesn't apply universally to every session.

**Format:** Rule / Why / How to apply (same structure as `/capture`)

### → Memory (project type)

**When:** Design decision, discovered constraint, or debugging lesson specific to this project. Temporal — may become stale as the project evolves.

**Format:** Fact or decision / Why / How to apply

### → CLAUDE.md (project or global)

**When any of these apply:**
- Correction was forceful (rejection, interruption, explicit "stop doing X") — cost of missing it is too high for selective memory loading
- Correction matches a known frustration pattern from the catalog — these tend to be universal, not project-specific
- A memory for this behavior already existed but was violated this session — escalation signal: memory isn't working
- The finding is a hard constraint that affects every session in this project (build commands, code conventions, invariants)

**Routing within CLAUDE.md:**
- Applies to all projects → global (`~/.claude-shared/CLAUDE.md` or `~/.claude/CLAUDE.md`)
- Applies to this project only → project CLAUDE.md

### → Handoff doc

**When:** Unfinished threads, session state, open work items. Anything about "where we left off" rather than a permanent lesson.

**Location:** Memory file `handoff.md` in the project's memory directory, type `project`.

**Lifecycle:** Overwritten each time `/debrief` runs. Old handoff content is replaced, not accumulated. A handoff doc is consumed by the next session and has no long-term value — if something from a previous handoff is still relevant, it should have been acted on or promoted to a proper memory.

### → Skip

**When:** Already captured, trivial, obvious from the code or git history, or not worth the context cost of persisting.

### Cross-category tiebreaker

A single event can span categories. User corrects Claude because of a framework limitation Claude didn't know about — is that a correction (feedback) or a constraint (project)?

**Rule: route by what future sessions need.** If the lesson is "Claude shouldn't do X" (behavioral), it's feedback. If the lesson is "framework Y can't do Z" (factual), it's a constraint. If it's genuinely both, create two findings — one behavioral rule and one factual constraint. Don't force a single finding to serve two purposes.

For validated approaches (2f): route as feedback memory if it's about how Claude should work, or project memory if it's about how the codebase should be structured.

## Step 6: Present and Triage

Show findings grouped by destination. For each finding:

```
### [Category] Finding title
**Destination:** Memory (feedback) | Memory (project) | CLAUDE.md (project) | CLAUDE.md (global) | Handoff
**Content preview:**
> [Draft of what would be written]
**Why this destination:** [1-line justification for the routing decision]
```

Then ask: **"Which of these should I save? You can approve all, reject specific ones by number, or change the destination for any item."**

If there are escalation candidates (memory existed but was violated this session), highlight them prominently:

> **Escalation signal:** Finding #N matches existing memory `{filename}` which was violated this session. Recommending promotion to CLAUDE.md. If this keeps recurring, consider `/harden`.

## Step 7: Write Approved Items

Write in this order:

### 7a: Memory files

Follow `/capture` format exactly:

```markdown
---
name: {descriptive_name}
description: {one-line summary — specific enough to judge relevance}
type: {feedback|project}
---

{Rule or fact statement}

**Why:** {Incident, rationale, or motivation}

**How to apply:** {When/where this kicks in. Include exceptions.}
```

Add index entries to MEMORY.md.

### 7b: CLAUDE.md additions

Show the exact lines and proposed insertion point (respect positional ordering — behavioral rules in top third, build/architecture in middle, status/gaps in bottom). Write after user confirms placement.

### 7c: Handoff doc

Write or overwrite `handoff.md` in the project's memory directory:

```markdown
---
name: handoff
description: "{Content-specific description — e.g. 'Session handoff — auth middleware refactor incomplete, integration tests pending, rate limiter design decided'}"
type: project
---

# Session Handoff — {date}

## What was being worked on
{Task context — what the session set out to accomplish}

## Where it was left off
{Current state — what's done, what's partially done}

## Decisions made this session
{Key decisions with rationale — so next session doesn't re-litigate}

## Open threads
- {Bulleted list: what needs doing, why it wasn't done, context for picking it up}
```

Update MEMORY.md index to include the handoff entry if not already present.

**Making the handoff discoverable at next session start:**

The auto-memory system reads MEMORY.md every session and loads individual memory files based on relevance to the current task. For the handoff to be loaded, it needs to match what the user is likely to ask about.

- **The `description` field is critical.** Don't use a generic description like "Session handoff — unfinished work." Use content-specific keywords that match the topics a future session would involve — e.g., "Session handoff — auth middleware refactor incomplete, integration tests pending." This is what the auto-memory system uses to judge relevance.
- **The MEMORY.md index entry** should also be content-specific: `- [handoff.md](memory/handoff.md) — auth middleware refactor, incomplete integration tests` not just `- [handoff.md](memory/handoff.md) — session handoff`.
- **Update both** the description and the index entry every time the handoff is overwritten. Stale keywords from a previous session's handoff are worse than no keywords.

## Step 8: Summary

After writing, show:
- Count of items saved by destination (N memories, N CLAUDE.md additions, handoff doc updated/created)
- Any escalation signals noted (suggest `/harden` for follow-up)
- Any cross-project patterns noticed (suggest `/audit` for follow-up)

## Rules

- **Read the transcript selectively.** Session transcripts can be large. Scan for signal patterns using grep before reading sections. Don't load the entire file into context.
- **Never write without user approval.** Present all findings and get explicit go-ahead before writing anything.
- **Use the user's words for corrections.** Don't paraphrase — same principle as `/capture`. If you need to restructure for clarity, show the restructured version for confirmation.
- **Don't over-capture.** Five high-quality findings beat twenty marginal ones. If a finding is obvious from the code diff or git log, skip it — those are already persisted in version control.
- **Handoff replaces, doesn't accumulate.** Each debrief overwrites the previous handoff doc. Stale handoff notes are worse than no handoff notes.
- **Highlight escalation candidates.** A memory that existed but was violated this session is the most actionable finding — make it unmissable in the output.
- **Don't re-litigate corrections.** If the user corrected Claude and Claude adjusted, capture the correction faithfully. Don't evaluate whether the correction was "right."
- **Respect privacy in excerpts.** When quoting from the transcript, quote the minimum needed to identify the finding.
- **Scope the routing decision clearly.** For every finding routed to CLAUDE.md, state *why* memory isn't sufficient. For every finding routed to memory, state *why* it doesn't need to be in CLAUDE.md. The user should be able to override any routing decision with confidence.
