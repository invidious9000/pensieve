# Instruction File Patterns

Principles for structuring CLAUDE.md and rules files for maximum effectiveness.

## Positional Ordering

LLMs exhibit positional attention bias — instructions at the beginning and end of long contexts receive more attention weight than those in the middle. Structure accordingly:

### Top third (primacy zone) — what Claude must internalize before writing code
- Identity: what the project is (1-3 sentences)
- Rules the agent violates most often (conventions, constraints, workflow protocol)
- Whatever the user most frequently has to correct

### Middle third — reference material
- Build/test commands, connection strings
- Architecture overview, solution structure
- Detailed catalogs (or lazy-load pointers to design docs)

### Bottom third (recency zone) — grounding in current reality
- Implementation status, known gaps
- Stubs table (prevents wasted effort on dead ends)
- Current state and remaining work

The specific section ordering depends on the project. The principle is: **put the things Claude gets wrong most often near the top.** If Claude keeps using the wrong build command, move build commands up. If Claude keeps violating a code convention, move conventions up. The ordering should be driven by observed failures, not by a fixed template.

## Lazy Loading

Large reference material (service catalogs, API docs, design docs) should NOT be inlined in CLAUDE.md. Instead:

**Good:** "For detailed service descriptions, see `design/architecture.md`."
**Bad:** 40 lines of per-service descriptions with line counts.

### When to lazy-load
- Content >20 lines that's only relevant for specific tasks
- Design documents, API references, schema descriptions
- Historical context or decision records

### When to keep inline
- Build/test commands (needed every session)
- Code conventions (needed before writing any code)
- Workflow protocol (needed before starting work)
- Known stubs/gaps (prevents wasted effort)

## Instruction Density

Every line in CLAUDE.md costs context tokens on every conversation. Ruthlessly trim:

| Instead of | Write |
|------------|-------|
| "UserService (~800 lines) — handles registration, login, password reset, session management, OAuth2 flow, rate limiting, audit logging, and profile CRUD" | "UserService — auth, sessions, profiles" (or lazy-load pointer) |
| A paragraph explaining why a convention exists | The convention as a bullet point |
| "See `docs/architecture.md` for the full service catalog." | Keep as-is — this is a pointer, not inlined content |

## Contradiction Prevention

CLAUDE.md and memory files are loaded together. They must not contradict:

- If CLAUDE.md says "use Result types for errors" and a memory says "throw exceptions" → agent gets confused
- If CLAUDE.md describes workflow X and a memory says "don't use workflow X" → which wins?

**Rule:** CLAUDE.md defines the current state. Memory captures lessons and preferences. If they conflict, CLAUDE.md is likely stale — update it.

## Common Missing Sections

CLAUDE.md files that cause agent confusion often lack:

1. **Code conventions** — without these, agents guess the style and guess wrong
2. **Workflow protocol** — without this, agents invent their own workflows
3. **Known stubs/gaps** — without this, agents waste time on dead ends
4. **Build commands** — without this, agents guess invocations
