---
name: diagnose
description: "Mine session transcripts for actual frustration patterns — rejections, interruptions, corrections, retries — and compare with existing memories"
---

You are mining Claude Code session transcripts to find actual user frustration patterns empirically. This goes beyond `/audit` (which checks existing memories and instruction files) by looking at what actually happened in past sessions.

Read `references/claude-frustration-patterns.md` from the pensieve plugin directory for the pattern catalog.

## Data Sources

Session transcripts are JSONL files stored per-account, per-project. **Frustration patterns are about the user, not the project** — if a user is frustrated by Work Avoidance in one project, they'll be frustrated by it everywhere.

**CRITICAL: You MUST scan ALL projects across ALL accounts, not just the current project.**

Run this exact command first to discover all transcripts:
```bash
find ~/.claude/projects ~/.claude-account*/projects -name "*.jsonl" -type f 2>/dev/null | while read f; do dir=$(dirname "$f"); proj=$(basename "$dir"); echo "$(stat -c %Y "$f") $proj $f"; done | sort -rn | head -30
```

This gives you the 30 most recent session transcripts across every project and every account, sorted by modification time. The output format is `timestamp project-name filepath`.

Work through these transcripts in recency order. Tag each finding with its project name so the heatmap shows cross-project distribution (e.g., "Work Avoidance: 5 in daystrom-mk2, 2 in chooch, 0 in pensieve").

Each JSONL line is a JSON object. Key fields:
- `type`: "user", "assistant", "file-history-snapshot"
- `message.content`: the actual message text (string or array of content blocks)
- `toolUseResult`: "User rejected tool use" when user blocked an action
- `timestamp`: when it happened

## Analysis Protocol

### Phase 1: Collect frustration signals

Scan the most recent 10-20 session transcripts (by modification time). For each, extract:

**Hard signals (definitive frustration):**
- Lines containing `"User rejected tool use"` — count and note what tool was rejected
- Lines containing `"Request interrupted by user"` — user hit stop mid-action
- User messages immediately following a rejection (these contain the correction)

**Soft signals (likely frustration):**
- User messages starting with or containing: "no", "don't", "stop", "wrong", "that's not", "why did you", "I said", "not what I", "again?"
- Same tool called 3+ times in sequence with failures between
- Assistant messages followed by user messages <20 characters (terse responses suggest dissatisfaction)

**Memory-adjacent signals:**
- Sessions where a feedback memory was saved — what happened just before? (The preceding user message is the raw correction before Claude paraphrased it)

### Phase 2: Cluster by pattern

Group the extracted signals by the frustration patterns in the reference doc:
- Work Avoidance: rejections where Claude suggested deferring/skipping
- Shallow Fixes: corrections about root cause, null guards, symptom patches
- Clipboard Relay: user being asked to run/test/check things
- Collateral Damage: rejections of destructive git/delete/kill operations
- Ask-Then-Act: interruptions where Claude asked then acted anyway
- Over-Generalized Memory: corrections to memories Claude just wrote
- Narration Without Action: "just do it" style corrections
- Dismissing Test Failures: corrections about test ownership

Also look for patterns NOT in the catalog — novel frustration modes.

### Phase 3: Gap analysis

Compare findings with existing memories:
- **Captured and addressed**: frustration pattern exists in sessions AND has a memory → check if the memory is working (did the frustration stop after the memory was saved?)
- **Captured but recurring**: memory exists but the frustration keeps happening → memory isn't effective, needs rewriting or promotion to CLAUDE.md or hook
- **Never captured**: frustration pattern appears in sessions but NO memory exists → the user gave up correcting, or the correction was verbal and Claude never saved it
- **Over-captured**: memory exists but the frustration pattern doesn't appear in recent sessions → memory may be stale or from a long time ago

### Phase 4: Effectiveness measurement

For patterns that have an associated memory:
- Find the memory's creation date
- Check sessions before vs. after that date
- Did the frustration frequency decrease? If not, the memory isn't working.

### Phase 5: User persona inference

From the session transcripts, infer the user's profile by observing:

- **Technical level:** What vocabulary do they use? Do they reference specific APIs, algorithms, patterns by name? Do they write code in their messages? (senior vs. junior signal)
- **Communication style:** Are their messages terse (1-2 sentences) or detailed? Do they use technical shorthand? (direct vs. explanatory preference)
- **Autonomy preference:** How often do they approve vs. reject tool uses? Do they say "just do it" or "show me first"? (autonomous vs. supervised preference)
- **Frustration triggers:** What patterns from Phase 2 cluster most heavily? These are the user's specific pet peeves.
- **Work patterns:** Do transcripts show parallel sessions? Multiple projects? Late-night sessions? (context for understanding their workflow)

Draft a user persona summary. This will be used by `/seed` if run afterward, or by `/optimize` to generate a user profile memory. Present it to the user for confirmation — persona inference is a hypothesis, not a fact.

## Output Format

### Frustration Heatmap
| Pattern | Occurrences (last 20-30 sessions) | Projects affected | Memory exists? | Effective? |
|---------|-------------------------------------|-------------------|----------------|------------|
| ... | ... | ... | ... | ... |

### Uncaptured Frustrations
Patterns found in sessions with no corresponding memory. For each:
- **Pattern:** what's happening
- **Evidence:** specific session excerpts (with timestamps)
- **Recommendation:** memory to create, or rule to add to CLAUDE.md, or hook to install

### Ineffective Memories
Memories that exist but aren't preventing the frustration they were created for:
- **Memory:** file name and rule
- **Evidence:** frustration still recurring after memory creation
- **Recommendation:** rewrite, promote to CLAUDE.md, or convert to hook

### Novel Patterns
Frustrations that don't match any known pattern — potential additions to the catalog.

### Inferred User Persona
Present the inferred profile with evidence for each dimension:
- **Technical level:** [junior / mid / senior / expert] — evidence: [specific observations]
- **Communication preference:** [terse / balanced / detailed] — evidence: [message length patterns]
- **Autonomy preference:** [high / medium / low] — evidence: [approval/rejection ratio, "just do it" frequency]
- **Top frustration triggers:** [ranked list from Phase 2]
- **Work patterns:** [solo / parallel sessions / multi-project / etc.]

Ask: "Does this look right? Anything off?" The user's corrections here are the most valuable input for `/seed` and user profile memories.

## Execution Rules

- This skill is READ-ONLY. Do not modify any files.
- Session transcripts can be large (10MB+). Read selectively — scan for signal patterns, don't load entire files into context.
- Respect privacy: report patterns and anonymized excerpts, not full conversation dumps.
- When quoting user messages as evidence, quote the minimum needed to demonstrate the pattern.
- After diagnosis, suggest running `/optimize` or `/capture` to address findings, or `/seed` to proactively install rules.
