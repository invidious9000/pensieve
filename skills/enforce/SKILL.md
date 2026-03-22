---
name: enforce
description: "View, test, and manage the pensieve invariance auditor — the runtime enforcement layer that checks behavioral invariants and injects reasoning checkpoints"
---

Display the current state of the pensieve invariance auditor for this session.

## What the auditor does

The invariance auditor is a stateful PostToolUse/UserPromptSubmit/Stop hook that:
1. Tracks tool call trajectories per session (tool name, file path, sequence number)
2. Checks **invariants** — temporal properties that must hold (e.g., "read before edit", "verify config at runtime")
3. Fires **checkpoints** — periodic reasoning prompts that break autopilot (e.g., "30 tool calls without user input")

State is persisted at `/tmp/pensieve-auditor/{session_id}.json`.

## Invariant types

### `preceded_by`
Before tool X is called, tool Y must have been called. Checked at trigger time.
- Example: Read a file before editing it

### `followed_by`
After tool X is called, tool Y must be called within N subsequent tool calls. Registered as "pending" at trigger time, checked on each subsequent call, enforced at deadline or at Stop.
- Example: After editing appsettings.json, run the service within 20 calls

### `session_requires`
Before the first edit in a session, a specific analysis tool must have been called.
- Example: Call spec_context or graph_query before writing code

## Checkpoint conditions

- `calls_since_user >= N` — fires every N tool calls without a user message
- `consecutive_edits >= N` — fires when N consecutive edits happen without a Read

## Configuration

Invariant definitions are loaded from two locations (merged):

1. **Plugin defaults:** `${CLAUDE_PLUGIN_ROOT}/invariants/default.json`
2. **Project-specific:** `.claude/pensieve-invariants.json` (in project root)

Project invariants extend defaults. To override a default, use the same `id`.

### Adding project-specific invariants

Create `.claude/pensieve-invariants.json`:

```json
{
  "invariants": [
    {
      "id": "consult-graph-before-impl",
      "type": "session_requires",
      "trigger": { "event": "first_edit_in_session" },
      "requires": { "tool_pattern": "mcp__daystrom__.*" },
      "severity": "soft",
      "message": "You're about to write code without consulting Daystrom. Consider calling spec_context or graph_query first."
    }
  ],
  "checkpoints": []
}
```

## When invoked

When the user runs `/enforce`, read the current session's auditor state file and report:
- Total tool calls this session
- Current calls since last user turn
- Any pending followed_by invariants (and their deadlines)
- Which invariants have fired and when
- List of loaded invariants (default + project)

Also check that the hook is installed and functioning by verifying `/tmp/pensieve-auditor/` contains a state file for the current session.

## Generating invariants from diagnose

The `pensieve:harden` skill can generate invariant definitions from diagnosed frustration patterns. When a pattern is identified as a temporal property (X must happen before/after Y), harden should output an invariant definition for `.claude/pensieve-invariants.json` rather than (or in addition to) a standalone hook script.
