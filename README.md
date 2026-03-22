# Pensieve

Memory and instruction optimizer for [Claude Code](https://claude.ai/code).

## Why this exists

Claude Code has built-in memory (`auto-memory`), instruction files (`CLAUDE.md`), and `/insights` for session analysis. These are good primitives. What's missing is the maintenance layer — nothing checks whether your memories contradict each other, whether your CLAUDE.md buries important rules where they get less attention, whether the same correction you've made 5 times has actually been captured, or whether the captured version even matches what you meant.

The result is predictable degradation: memories accumulate "don't" rules that make Claude overly cautious, CLAUDE.md grows organically with behavioral rules buried in the bottom half, corrections drift from the user's actual intent (you said "don't kill by port" and Claude remembered "never touch processes"), and the same frustrations repeat across projects.

**Pensieve fills the gap between Claude Code's persistence primitives and actual behavioral reliability.**

### How it differs from existing tools

| Tool | What it does | What it doesn't do |
|------|-------------|-------------------|
| **auto-memory** | Saves memories when Claude thinks something is worth remembering | Doesn't audit quality, detect drift, find contradictions, or check if memories are working |
| **`/insights`** | Shows usage stats and general tips from session history | Doesn't analyze frustration patterns, doesn't touch memory or CLAUDE.md, doesn't produce actionable fixes |
| **Pensieve** | Audits memory + instruction health, mines sessions for empirical frustration data, fixes what's broken, proactively seeds correct behaviors, escalates to hooks | Doesn't replace the primitives — builds on them |

### Privacy: session transcript analysis

The `/diagnose` and `/debrief` skills read your local session transcripts (JSONL files in `~/.claude/projects/`) to find frustration patterns and extract session lessons. **This data never leaves your machine.** Pensieve is a set of markdown skill files with no code, no network calls, no telemetry. The analysis happens entirely within your Claude Code session, using the same file-reading tools Claude already has access to. Nothing is collected, transmitted, or stored beyond the memories and CLAUDE.md changes you explicitly approve.

## Install

Add the marketplace to your settings.json (`~/.claude/settings.json`):

```json
{
  "extraKnownMarketplaces": {
    "pensieve": {
      "source": {
        "source": "github",
        "repo": "invidious9000/pensieve"
      }
    }
  }
}
```

Then enable the plugin:

```
/plugins
```

Select `pensieve@pensieve` and enable it.

## The Escalation Ladder

Pensieve models behavioral rules as having three enforcement levels:

```
Memory (soft, advisory) → CLAUDE.md (stronger, every session) → Hook (mechanical, unbypassable)
```

Rules should start as memories and escalate only when softer enforcement fails. The skills support this full lifecycle.

## Invariance Auditor (v0.11.0)

The escalation ladder assumes instructions work if you put them in the right place. Empirical evidence says otherwise — rules in CLAUDE.md, in memory, AND as explicit verbal corrections still get violated because task momentum outcompetes static instructions for attention weight. The invariance auditor works at a different layer: instead of asking the model to remember a rule, it checks the rule externally against the tool call trajectory and injects a correction at the moment of violation.

### How it works

A stateful `PostToolUse` / `UserPromptSubmit` / `Stop` hook tracks every tool call in a session, maintaining a trajectory log at `/tmp/pensieve-auditor/{session_id}.json`. On each tool call, it evaluates two kinds of rules:

**Invariants** — temporal properties that must hold over the trajectory:

| Type | What it checks | Example |
|------|---------------|---------|
| `preceded_by` | Tool Y must have been called before tool X | Read a file before editing it |
| `followed_by` | After tool X, tool Y must happen within N calls | After editing config, run the service within 20 calls |
| `session_requires` | Before the first Edit, an analysis tool must have been called | Call `spec_context` before writing code |

**Checkpoints** — periodic reasoning prompts that break autopilot:

| Condition | What it does |
|-----------|-------------|
| `calls_since_user >= 30` | "State what you're doing and why before continuing" |
| `consecutive_edits >= 6` | "Pause and verify your changes" |

Invariant violations come in two severities: **soft** (advisory systemMessage) and **hard** (forces attention, blocks Stop if unresolved).

### Default invariants

Out of the box, the auditor ships with:
- `read-before-edit` (soft) — must Read a file before Edit-ing it
- `runtime-verify-config` (hard) — after editing appsettings/Program.cs/csproj, must run the service within 20 calls; blocks session completion if pending

### Project-specific invariants

Create `.claude/pensieve-invariants.json` in your project root:

```json
{
  "invariants": [
    {
      "id": "consult-graph",
      "type": "session_requires",
      "trigger": { "event": "first_edit_in_session" },
      "requires": { "tool_pattern": "mcp__daystrom__.*" },
      "severity": "soft",
      "message": "You're writing code without consulting the graph."
    }
  ],
  "checkpoints": []
}
```

### The pipeline

The auditor closes the feedback loop between diagnosis and enforcement:

```
/diagnose → find frustration patterns in transcripts
/harden   → generate invariant definitions from patterns
auditor   → enforce invariants at runtime
/diagnose → measure whether violations decreased
```

## Skills

### Prevention

**`/seed`** — Proactively install anti-frustration rules based on user profile. If `/diagnose` has been run first, uses the empirically inferred persona. Otherwise profiles the user through questions. Generates positive-framing rules targeting the 19 known Claude frustration patterns. Vaccination instead of treatment.

**`/capture`** — Structured feedback capture with drift prevention. When you want Claude to remember something, asks What/Why/When/Exceptions before writing — preventing the common failure where Claude paraphrases your rule incorrectly.

**`/debrief`** — End-of-session retrospective. Sweeps the current session's transcript to extract user corrections, design decisions, hard-won debugging lessons, discovered constraints, and unfinished threads. Classifies each finding by destination (memory, CLAUDE.md, or handoff doc) based on severity, scope, and whether existing memories were violated. Produces a handoff note so the next session can pick up where this one left off.

### Diagnosis

**`/audit`** — Full diagnostic of everything shaping Claude's behavior. Checks memory structural integrity, content quality (contradictions, staleness, negativity bias, absolutist language, drift), CLAUDE.md positional ordering and density, and cross-project rule duplication. Produces a health dashboard with actionable findings.

**`/diagnose`** — Empirical analysis from session transcripts. Finds tool rejections, interruptions, correction language, and retry patterns. Clusters them by the 19 frustration patterns. Compares what memories exist vs. what frustrations actually occur. Infers user persona from behavioral signals. Measures whether existing memories are actually working.

### Treatment

**`/optimize`** — Apply all fixes from audit findings: consolidate memory clusters into positive rules, soften absolutist language, trim verbosity, reorder CLAUDE.md for attention bias, extract reference material to lazy-load pointers, promote cross-project duplicates to shared CLAUDE.md.

**`/harden`** — Convert repeatedly-violated rules into mechanical hooks. When a rule keeps being ignored despite being in memory AND CLAUDE.md, make it unbypassable. Prefers generating invariant definitions for the auditor (temporal properties) over standalone hooks (simple pattern matches). Includes testing and multi-account registration.

**`/enforce`** — View the current state of the invariance auditor: loaded invariants, pending verifications, fire history, trajectory stats. Use to verify the auditor is running and to inspect what it's tracking.

## Recommended Workflow

```
First time:    /diagnose → /seed         (understand user, install proactive rules)
Periodic:      /audit → /optimize        (catch degradation, fix it)
After issues:  /diagnose → /optimize     (find what's not working, fix root cause)
In-the-moment: /capture                  (save a correction without drift)
End of session: /debrief                 (extract lessons, decisions, handoff state)
Last resort:   /harden                   (mechanically enforce what Claude won't learn)
```

## The 19 Frustration Patterns

Pensieve catalogs 19 behavioral failure modes that generate user frustration:

| # | Pattern | Core Issue |
|---|---------|-----------|
| 1 | Work Avoidance | Suggests deferring instead of doing |
| 2 | Shallow Fixes | Patches symptoms instead of tracing root cause |
| 3 | Clipboard Relay | Asks user to run things Claude could run itself |
| 4 | Collateral Damage | Broad destructive actions when narrow ones needed |
| 5 | Ask-Then-Act | Asks a question then acts without waiting |
| 6 | Over-Generalized Memory | Broadens correction scope beyond what user meant |
| 7 | Narration Without Action | Describes plans instead of executing them |
| 8 | Dismissing Test Failures | Claims broken tests are "pre-existing" |
| 9 | Hallucinated Knowledge | References things that don't exist without checking |
| 10 | Scope Creep | One-line request becomes module rewrite |
| 11 | Context Amnesia | Forgets decisions from earlier in conversation |
| 12 | Apology Loops | Paragraphs of contrition instead of fixing |
| 13 | Permission Paralysis | "Shall I proceed?" on every minor action |
| 14 | Sycophantic Reversal | Abandons correct approach when user pushes back |
| 15 | Incomplete Execution | Does 80%, lists the rest as "you'll want to..." |
| 16 | Wrong Abstraction Level | Explains basics to experts or vice versa |
| 17 | Stale Context | Assumes files haven't changed since last read |
| 18 | Silent Workaround | Hides errors instead of reporting them |
| 19 | Ignoring Available Tools | Hand-builds things when skills/commands exist for the task |

Each pattern includes: typical user reactions, memory symptoms, root cause, and correct positive behavior. See `references/claude-frustration-patterns.md`.

## License

MIT
