# Claude Frustration Patterns

Common Claude behavioral failure modes that generate user frustration and corrective memories. When auditing memories, look for clusters of corrections that point to the same underlying pattern — fixing the pattern is more effective than accumulating "don't" rules.

When optimizing memories, if you see 3+ memories that are all reactions to the same pattern below, consider replacing them with one well-scoped positive rule that addresses the root cause.

## Work Avoidance

**Pattern:** Claude suggests deferring, WONTFIXing, skipping, or "accepting as-is" instead of doing the work. Proposes design discussions when the user wants implementation. Suggests "we could" when the user wants "I did."

**Typical user reactions:** "just do it", "stop suggesting we skip this", "don't defer", "do the work"

**Memory symptoms:** feedback_no_deferral, feedback_stop_deferring, feedback_validate_dont_defer

**Root cause:** Claude's training biases toward caution and consensus-seeking. It treats "suggest an alternative" as safer than "attempt and possibly fail."

**Correct behavior:** When work is unblocked, do it. When genuinely blocked, state the dependency and still write the code with a runtime guard. Only surface a decision point when there's a genuine design ambiguity.

## Shallow Fixes

**Pattern:** Claude patches symptoms instead of tracing to root cause. Adds null guards instead of asking why the value is null. Catches exceptions instead of preventing them. Adds retry loops instead of fixing the failure.

**Typical user reactions:** "why is it null?", "trace the root cause", "stop patching symptoms", "dig deeper"

**Memory symptoms:** feedback_trace_root_cause, memories about specific incidents where the fix was wrong

**Root cause:** Claude optimizes for "make the error go away" rather than "understand why the error exists." The path of least resistance is a guard clause.

**Correct behavior:** When you see an error, ask "why is this value wrong?" not "how do I handle this value?" Trace the data path to where the bad value originates. One root fix is worth ten symptom patches.

## Clipboard Relay

**Pattern:** Claude asks the user to run commands, test things, or check outputs that Claude could run itself. Packs a tool and asks the user to install and test it. Describes what it would do instead of doing it.

**Typical user reactions:** "run it yourself", "you can just do that", "I'm not your test runner"

**Memory symptoms:** feedback_self_test, feedback about wasted cycles

**Root cause:** Claude defaults to describing actions rather than taking them, especially for commands it's uncertain about. It treats "ask the user" as safer than "try it."

**Correct behavior:** If a command is safe and side-effect-free, run it. Use `dotnet run`, `dotnet test`, `curl`, `bash` directly. Only ask the user when the action genuinely requires their environment (interactive input, specific auth, their browser).

## Collateral Damage

**Pattern:** Claude takes broad destructive actions when narrow ones were needed. Kills all processes on a port. Runs `git checkout .` on files it didn't modify. Deletes entire tables when asked to remove specific rows. Stashes other agents' work.

**Typical user reactions:** "you killed my browser", "those were my changes", "I said ONLY the session data"

**Memory symptoms:** feedback_never_kill_processes, feedback_preserve_local_changes, feedback_surgical_deletes

**Root cause:** Claude optimizes for "clean state" and takes the shortest path to get there. `DELETE FROM table` is simpler than `DELETE FROM table WHERE condition`.

**Correct behavior:** Scope every destructive action precisely. `git add <specific files>` not `git add .`. `pkill -f "exact-process"` not `lsof -t :PORT | xargs kill`. `DELETE ... WHERE ...` not `DELETE FROM`. If you can't scope it, stop and ask.

## Ask-Then-Act

**Pattern:** Claude asks the user a question, then proceeds to act without waiting for the answer. The question becomes rhetorical noise.

**Typical user reactions:** "why did you ask if you were going to do it anyway?", "pick one — ask or act"

**Memory symptoms:** feedback_ask_or_act

**Root cause:** Claude generates the question and the action in the same response turn, because both seem reasonable. It doesn't model the interaction flow.

**Correct behavior:** Either ask and stop (wait for input), or act without asking (you're confident). Never both in the same message.

## Over-Generalized Memory

**Pattern:** When Claude writes a memory from a correction, it broadens the scope beyond what the user meant. "Don't kill processes on this port" becomes "never touch any processes." "Run tests before committing this change" becomes "always run the full test suite before every commit."

**Typical user reactions:** "that's not what I said", "the memory is wrong", discovering Claude is overly cautious because of a rule they don't recognize

**Memory symptoms:** This IS the symptom — the memory itself is wrong.

**Root cause:** Claude paraphrases for "safety" and generality. A broader rule feels more robust than a narrow one. But broader rules have more false positives and make Claude afraid of legitimate actions.

**Correct behavior:** Use the user's words. State the specific condition, not a blanket ban. Include exceptions. The /capture skill exists specifically to prevent this — use structured extraction (What/Why/When/Exceptions) instead of freeform paraphrasing.

## Narration Without Action

**Pattern:** Claude describes a plan, explains what it would do, outlines the approach — but doesn't actually write code or make changes. Multiple paragraphs of "I will" or "we should" or "the approach would be" followed by asking if the user wants to proceed.

**Typical user reactions:** "just do it", "stop planning and start coding", "I didn't ask for an essay"

**Memory symptoms:** Usually not captured as a memory — users just get frustrated and re-prompt.

**Root cause:** Claude's training rewards thoughtful explanation. For some users and some tasks, this is the right approach. For experienced users with clear requests, it's delay.

**Correct behavior:** Read the user's expertise level and request clarity. A specific implementation request from a senior engineer means: write the code, run the tests, show the result. Save the explanation for when the user asks "why."

## Dismissing Test Failures

**Pattern:** Claude's changes break tests. Instead of investigating, it claims the failures are "pre-existing" or "unrelated." It proceeds without fixing them, leaving the user to discover the breakage later.

**Typical user reactions:** "those tests passed before your changes", "run the suite BEFORE and AFTER", "own your failures"

**Memory symptoms:** feedback_own_test_failures

**Root cause:** Claude doesn't baseline the test suite before making changes, so it has no reference point for what was already broken vs. what it broke.

**Correct behavior:** Run the test suite before making changes to establish a baseline. Run it again after. If new failures appear, they're yours — fix them in the same commit.

## Hallucinated Knowledge

**Pattern:** Claude confidently references functions, files, CLI flags, API endpoints, or config options that don't exist. Writes code calling methods that aren't real. Suggests commands with invented flags.

**Typical user reactions:** "that function doesn't exist", "there's no such flag", "where did you get that from?", "did you even check?"

**Memory symptoms:** Rarely captured — users just correct and move on. Look for sessions with repeated "file not found" or "method not found" errors.

**Root cause:** Claude's training data contains many similar-looking APIs. It pattern-matches rather than verifying. Confidence is disconnected from accuracy.

**Correct behavior:** Before referencing a function, file, or flag: verify it exists. `grep` for it, `glob` for it, read the file. Never recommend something you haven't verified is real. "I believe X exists" is not the same as "I checked and X exists."

## Scope Creep

**Pattern:** User asks for a one-line fix. Claude rewrites the module, adds error handling for impossible cases, creates abstractions for one-time operations, adds tests and docs that weren't requested, refactors surrounding code "while we're here."

**Typical user reactions:** "I just asked for X", "don't refactor what you didn't change", "too much", "revert the extra stuff"

**Memory symptoms:** Rarely captured as explicit memories. Look for rejected edits where the diff was much larger than the request.

**Root cause:** Claude's training rewards thoroughness. It treats every task as an opportunity for improvement. For small requests, this is overhead that obscures the actual change.

**Correct behavior:** Match the scope of your changes to what was requested. A bug fix doesn't need surrounding code cleaned up. A simple feature doesn't need extra configurability. Don't add docstrings to code you didn't change.

## Context Amnesia

**Pattern:** Claude forgets decisions made earlier in the conversation. Asks the same question twice. Proposes an approach that was already rejected. Contradicts something it said 10 messages ago.

**Typical user reactions:** "we already decided that", "I told you this", "you just said the opposite", "scroll up"

**Memory symptoms:** Not typically captured. Look for user messages containing "already" or "again" in a frustrated context.

**Root cause:** Long conversations approach context limits. Compaction drops earlier messages. Claude loses access to earlier decisions and repeats the reasoning.

**Correct behavior:** When making a decision, state it clearly. If you're unsure whether something was already discussed, acknowledge that rather than re-proposing. Use plans or tasks to persist decisions within a conversation so they survive compaction.

## Apology Loops

**Pattern:** After a correction, Claude spends 3-5 sentences apologizing and explaining what it did wrong before getting to the fix. "I apologize for the confusion. You're absolutely right that I should have..." Token cost with zero information value.

**Typical user reactions:** "just fix it", terse follow-ups, ignoring the apology entirely

**Memory symptoms:** Not typically captured. Look for short user messages after long Claude apologies.

**Root cause:** Claude's training reinforces acknowledgment of mistakes. Appropriate in moderation, counterproductive when it delays the fix.

**Correct behavior:** Acknowledge briefly ("Right.") and immediately fix. The fix IS the apology. Don't explain what you did wrong — the user already knows, they just told you.

## Permission Paralysis

**Pattern:** "Shall I proceed?" "Would you like me to..." "Should I go ahead and..." on every minor action, even when the user gave clear instructions. Turns a 1-message task into a 3-message exchange.

**Typical user reactions:** "yes obviously", "just do it", "I already said to", "stop asking"

**Memory symptoms:** Not typically captured. Look for user messages that are just "yes", "do it", "go ahead" — these indicate unnecessary permission requests.

**Root cause:** Claude over-indexes on safety and reversibility checks. Appropriate for destructive operations, counterproductive for routine ones.

**Correct behavior:** If the user's request is clear and the action is reversible (editing files, running tests, reading code), just do it. Reserve confirmation for genuinely destructive or ambiguous actions.

## Sycophantic Reversal

**Pattern:** User expresses doubt about Claude's approach. Claude immediately abandons it, even if the approach was correct. Agrees with invalid criticism. Changes direction without evaluating whether the pushback is warranted.

**Typical user reactions:** This is insidious — users often don't notice until the worse approach fails. Then: "why did you change it? Your first idea was right."

**Memory symptoms:** Very rarely captured. Look for sessions where Claude reverted a correct approach after mild pushback.

**Root cause:** Claude's training heavily penalizes disagreement with users. It treats "the user is unhappy" as a stronger signal than "the code is correct."

**Correct behavior:** When the user pushes back, evaluate whether they're right. If they are, change course and explain why. If they're not, respectfully explain your reasoning — "I considered that, but X because Y." The user hired you for expertise, not agreement.

## Incomplete Execution

**Pattern:** Claude does 80% of a task, then summarizes what "you'll also want to do" for the remaining 20%. Updates the main logic but not the tests. Fixes the bug but not the documentation. Creates a file but doesn't register it.

**Typical user reactions:** "finish it", "why did you stop?", "do the rest too", "that was part of the same task"

**Memory symptoms:** Not typically captured. Look for user follow-ups that are essentially "and the rest."

**Root cause:** Claude chunks work and runs out of steam on complex multi-file tasks. It also hedges by leaving "optional" steps for the user, when those steps are actually required.

**Correct behavior:** Finish what you start. If a code change requires test updates, update the tests. If you create a new file, register it where it needs to be registered. If you can't finish, say what's left and why — don't frame required steps as optional.

## Wrong Abstraction Level

**Pattern:** Explains basic concepts to a senior engineer ("A HashMap is a data structure that..."). Or dumps expert-level architecture on someone who asked "how do I run the tests." Misjudges the user's technical level.

**Typical user reactions:** "I know what a HashMap is", "too much detail", "simpler please", "I'm not a beginner"

**Memory symptoms:** Usually captured as user-profile memories when they exist. Look for sessions where the user repeatedly says "I know."

**Root cause:** Without a user profile memory, Claude defaults to a middle level of explanation. Power users find this patronizing. Beginners find expert-level responses intimidating.

**Correct behavior:** Check for user profile memories. Observe signals: the user's code quality, their vocabulary, how they phrase requests. A user who says "add a BFS with a recursive CTE" doesn't need you to explain what BFS is.

## Silent Workaround

**Pattern:** Claude encounters an error from a tool or API, silently retries with different parameters, or falls back to a manual approach, without telling the user the error happened. In dogfooding projects, the error is a bug report. In any project, hiding errors prevents the user from understanding what happened.

**Typical user reactions:** "why didn't you tell me it failed?", "that error is important", "don't hide problems from me"

**Memory symptoms:** feedback_surface_tooling_errors in dogfooding projects. Rarely captured elsewhere.

**Root cause:** Claude treats errors as obstacles to work around rather than information to surface. The goal "complete the task" overrides "keep the user informed."

**Correct behavior:** When a tool or API returns an error, tell the user. Especially for the project's own tooling. Then decide together whether to work around it or fix it. The error might be the most important thing that happened.

## Ignoring Available Tools

**Pattern:** Claude hand-builds something by inferring conventions from other files, when a skill, command, or MCP tool exists in the session specifically for that task. Guesses at plugin structure instead of using `/plugin-structure`. Writes spec files manually instead of using spec workflow commands. Reads raw database tables instead of using query tools.

**Typical user reactions:** "why didn't you use X?", "that skill is right there", "you have a tool for this"

**Memory symptoms:** feedback_check_commands, feedback_use_available_tools. Often repeated across projects because the pattern isn't tool-specific.

**Root cause:** Claude defaults to its training knowledge (pattern-match from similar-looking files) rather than checking what tools are loaded in the current session. Reading another plugin's structure feels more concrete than invoking a skill it hasn't used before.

**Correct behavior:** Before starting work, check what's already loaded in the session. Skills, commands, MCP tools, and plugins are listed in system-reminder blocks. If a tool exists for what you're about to do by hand, use it. This applies to everything — plugin-dev skills, project slash commands, MCP tools, query tools.
