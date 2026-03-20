# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Claude Code plugin (no code — markdown skills and reference material only) that audits, fixes, and prevents behavioral degradation in Claude Code's memory and instruction systems. Distributed as a marketplace plugin via `invidious9000/pensieve`.

## Plugin Convention

This is a Claude Code plugin. Follow these conventions exactly:

- **Plugin manifest:** `.claude-plugin/plugin.json` — uses `"skills": "./skills/"` (directory auto-discovery, NOT an array of objects)
- **Marketplace manifest:** `.claude-plugin/marketplace.json` — version must match plugin.json
- **Skills:** Each skill is a directory under `skills/` containing a `SKILL.md` with YAML frontmatter (`name`, `description`)
- **References:** Lazy-loaded by skills via `Read` tool. Skills reference them as `references/filename.md` relative to the plugin root
- **No code, no build step, no dependencies.** Everything is markdown.

When adding a new skill: create `skills/{name}/SKILL.md` with frontmatter. When adding reference material: add to `references/`. Bump version in BOTH plugin.json and marketplace.json.

## Architecture

### Skill lifecycle model
```
/seed → /capture → /audit → /diagnose → /optimize → /harden
 (prevent)  (capture)  (static)  (empirical)  (fix)     (enforce)
```

Skills are designed to compose: `/diagnose` output feeds into `/seed` (persona inference). `/audit` findings feed into `/optimize` (fix application). `/harden` is the escalation endpoint when softer enforcement fails.

### Reference documents (lazy-loaded)
- `claude-frustration-patterns.md` — 19 behavioral failure modes. Loaded by: audit, optimize, diagnose, capture, seed
- `instruction-patterns.md` — CLAUDE.md positional ordering, density, lazy-loading principles. Loaded by: audit, optimize
- `memory-anti-patterns.md` — 20 structural/content failure modes. Loaded by: audit

Skills instruct Claude to `Read` these only when needed, not all at once. This is intentional — the reference docs total ~330 lines and loading all of them wastes context on tasks that only need one.

### Scope of analysis
- `/audit` and `/optimize` operate across ALL projects' memories, not just the current project. They scan `~/.claude-shared/project-memory/*/` (multi-account) or `~/.claude/projects/*/memory/` (single-account).
- `/diagnose` reads session transcripts from `~/.claude/projects/{encoded}//*.jsonl`
- `/seed` and `/harden` write to `~/.claude/CLAUDE.md` or `~/.claude-shared/CLAUDE.md` (global) and project-level files
- `/capture` writes to the current project's memory directory

### Version management
Version lives in two places that MUST stay in sync:
- `.claude-plugin/plugin.json` → `version`
- `.claude-plugin/marketplace.json` → `plugins[0].version`

Bump both on every change. The marketplace caches by version — stale cache causes skills not to load.
