---
name: harden
description: "Convert repeatedly-violated rules into mechanical hooks — escalate from soft memory to hard enforcement"
---

You are helping the user convert a rule that Claude keeps violating (despite memories and CLAUDE.md instructions) into a mechanical hook that enforces it automatically.

This is the escalation ladder for behavioral rules:
1. **Memory** — soft, advisory. Claude reads it but may ignore it.
2. **CLAUDE.md** — stronger, loaded every session. Still advisory.
3. **Hook** — mechanical enforcement. Claude cannot bypass it.

This skill handles the 2→3 transition. Use it when `/diagnose` shows a rule that keeps being violated despite being in memory AND CLAUDE.md.

## Process

### Step 1: Identify the rule to harden

The user specifies which rule, or you can suggest based on `/diagnose` output. Good candidates:
- Rules violated 3+ times across recent sessions despite existing as a memory
- Rules where the violation causes data loss or irreversible damage (destructive actions)
- Rules that are pattern-matchable on tool input (command text, file paths, SQL)

Good candidates for **invariant definitions** (temporal properties — preferred over standalone hooks):
- "Read file before editing it" → `preceded_by` invariant
- "Verify config at runtime after changing it" → `followed_by` invariant
- "Consult graph before writing code" → `session_requires` invariant
- "Break autopilot every N tool calls" → checkpoint

Bad candidates for any mechanical enforcement:
- Behavioral/judgment rules ("trace root cause") — can't be mechanically checked
- Context-dependent rules ("don't over-engineer") — too subjective for a hook

### Step 2: Choose enforcement mechanism

**Prefer invariant definitions** over standalone hooks when the rule is a temporal property (X before Y, Y after X within N calls). Write the invariant to `.claude/pensieve-invariants.json` — the auditor hook handles enforcement, state tracking, cooldowns, and output formatting automatically. See `/enforce` for the invariant schema.

**Use standalone hooks** only when the rule is a simple pattern match on a single tool call (e.g., block `lsof -t | xargs kill`). These don't need trajectory state.

### Step 2b: Choose hook type (for standalone hooks)

| Hook Event | Use When |
|------------|----------|
| `PreToolUse` on `Bash` | Block specific command patterns (kill by port, unscoped DELETE, git checkout .) |
| `PreToolUse` on `Write`/`Edit` | Block writes to specific paths or with specific content |
| `PreToolUse` on any tool | Block tool invocations matching a pattern |
| `SessionStart` | Run checks at session start (structural integrity, environment) |
| `UserPromptSubmit` | Inject context or warnings based on the user's message |

### Step 3: Design the hook

For `PreToolUse` command hooks, design a pattern matcher:

```javascript
// Pattern: block `lsof -t ... | xargs kill` and `fuser -k`
const BLOCKED = [
  /lsof\s+-t.*\|\s*xargs\s+kill/,
  /fuser\s+-k/,
  /kill\s+.*\$\(lsof/,
];
```

The hook should:
1. Read the tool input from stdin (JSON with tool name, parameters)
2. Check if the input matches the blocked pattern
3. If blocked: output `{ "decision": "block", "reason": "..." }` with a helpful message explaining what to do instead
4. If allowed: exit silently (exit 0, no output)

### Step 4: Write the hook script

Write the hook as a `.mjs` file. Place it in:
- `~/.claude-shared/hooks/` for cross-account enforcement
- `.claude/hooks/` (project root) for project-specific enforcement

### Step 5: Register in settings.json

Add the hook to the appropriate settings file:
- `~/.claude/settings.json` (and account variants) for global hooks
- `.claude/settings.json` (project) for project-specific hooks

Format:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "node ~/.claude-shared/hooks/guard-name.mjs"
          }
        ]
      }
    ]
  }
}
```

### Step 6: Test the hook

1. Show the user the hook script and settings change
2. After approval, write the hook and update settings
3. Test by attempting the blocked action — verify it's caught
4. Test by attempting a similar but allowed action — verify it's not false-positive

### Step 7: Update the memory

After installing a hook, update the corresponding memory to note that it's now mechanically enforced. This prevents future `/optimize` runs from suggesting the memory is redundant — the memory documents the WHY, the hook enforces the WHAT.

## Rules

- **Always test before deploying.** A buggy hook blocks Claude on every action matching its event.
- **Prefer narrow patterns over broad ones.** A hook that blocks `DELETE FROM` without WHERE is good. A hook that blocks all SQL is too broad.
- **Include the "instead, do this" in the block message.** The hook should teach, not just block.
- **Register in ALL accounts** if this is a universal rule (check for multi-account setup).
