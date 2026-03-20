# Pensieve

Claude Code plugin for memory and instruction optimization. No code — skills and reference material only.

## Structure

```
.claude-plugin/plugin.json    Plugin manifest (6 skills)
skills/                       Skill definitions (markdown with YAML frontmatter)
references/                   Lazy-loaded reference material for skills
```

## Skills

| Skill | Purpose | Modifies files? |
|-------|---------|-----------------|
| `/audit` | Diagnose memory + instruction issues | No — read-only |
| `/optimize` | Fix memory + instruction + cross-project issues | Yes — with preview |
| `/diagnose` | Mine session transcripts, infer persona | No — read-only |
| `/capture` | Structured feedback capture | Yes — with confirmation |
| `/seed` | Proactive anti-frustration rule installation | Yes — with confirmation |
| `/harden` | Convert rule → mechanical hook | Yes — with testing |

## Development

No build step. Edit markdown files directly. Test by installing the plugin locally and running skills.
