#!/usr/bin/env python3
"""Pensieve Invariance Auditor — stateful behavioral hook.

Tracks tool call trajectories per session and checks invariants
(temporal properties that must hold) and checkpoints (periodic
reasoning prompts). Derived from empirically-observed frustration
patterns via pensieve:diagnose → pensieve:harden pipeline.

Events handled: PostToolUse, UserPromptSubmit, Stop
State persisted: /tmp/pensieve-auditor/{session_id}.json
"""

import json
import os
import re
import sys
import time
from pathlib import Path

STATE_DIR = Path("/tmp/pensieve-auditor")
PLUGIN_ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
COOLDOWN_CALLS = 20  # don't repeat same warning within N calls


# ── State management ──────────────────────────────────────────────

def state_path(session_id: str) -> Path:
    return STATE_DIR / f"{session_id}.json"


def load_state(session_id: str) -> dict:
    path = state_path(session_id)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "session_id": session_id,
        "trajectory": [],
        "calls_since_user": 0,
        "total_calls": 0,
        "pending": [],
        "fired": {},
        "files_read": [],
        "files_edited": [],
        "analysis_tools": [],
        "consecutive_edits": 0,
    }


def save_state(state: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path(state["session_id"]).write_text(json.dumps(state))


# ── Config loading ────────────────────────────────────────────────

def load_invariants() -> dict:
    """Load invariant definitions, merging default + project-specific."""
    config = {"invariants": [], "checkpoints": []}

    # Default from plugin
    default_path = Path(PLUGIN_ROOT) / "invariants" / "default.json"
    if default_path.exists():
        try:
            default = json.loads(default_path.read_text())
            config["invariants"].extend(default.get("invariants", []))
            config["checkpoints"].extend(default.get("checkpoints", []))
        except (json.JSONDecodeError, OSError):
            pass

    # Project-specific overrides
    cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    project_path = Path(cwd) / ".claude" / "pensieve-invariants.json"
    if project_path.exists():
        try:
            project = json.loads(project_path.read_text())
            config["invariants"].extend(project.get("invariants", []))
            config["checkpoints"].extend(project.get("checkpoints", []))
        except (json.JSONDecodeError, OSError):
            pass

    return config


# ── Helpers ───────────────────────────────────────────────────────

def extract_path(tool_name: str, tool_input: dict) -> str:
    if tool_name in ("Read", "Edit", "Write", "MultiEdit"):
        return tool_input.get("file_path", "")
    return ""


def extract_command(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Bash":
        return tool_input.get("command", "")
    return ""


def tool_matches(tool_name: str, pattern: str) -> bool:
    """Check if tool_name matches a pipe-separated pattern or regex."""
    for p in pattern.split("|"):
        p = p.strip()
        if p == tool_name:
            return True
        try:
            if re.fullmatch(p, tool_name):
                return True
        except re.error:
            pass
    return False


def path_matches(file_path: str, pattern: str) -> bool:
    if not file_path or not pattern:
        return False
    try:
        return bool(re.search(pattern, file_path))
    except re.error:
        return False


def input_matches(command: str, pattern: str) -> bool:
    if not pattern:
        return True
    try:
        return bool(re.search(pattern, command))
    except re.error:
        return False


def in_cooldown(state: dict, invariant_id: str) -> bool:
    last_fired = state["fired"].get(invariant_id, -999)
    return (state["total_calls"] - last_fired) < COOLDOWN_CALLS


def mark_fired(state: dict, invariant_id: str):
    state["fired"][invariant_id] = state["total_calls"]


# ── Invariant evaluation ─────────────────────────────────────────

def check_preceded_by(inv: dict, state: dict, tool_name: str,
                      file_path: str) -> str | None:
    """Check: before X, Y must have happened."""
    trigger = inv.get("trigger", {})
    requires = inv.get("requires", {})

    # Does this tool call match the trigger?
    if not tool_matches(tool_name, trigger.get("tool", "")):
        return None
    if trigger.get("path_pattern") and not path_matches(
            file_path, trigger["path_pattern"]):
        return None

    # Check if the required predecessor exists
    req_tool = requires.get("tool", "")
    must_match_path = requires.get("path_must_match_trigger", False)

    for entry in state["trajectory"]:
        if tool_matches(entry["tool"], req_tool):
            if must_match_path:
                if entry.get("path") == file_path:
                    return None
            else:
                return None

    # Predecessor not found
    msg = inv.get("message", f"Invariant {inv['id']} violated")
    return msg.replace(
        "{file}", os.path.basename(file_path) if file_path else "unknown")


def check_followed_by(inv: dict, state: dict, tool_name: str,
                      file_path: str, command: str) -> str | None:
    """Manage followed_by invariants: register pending, check deadlines,
    and satisfy pending when the required tool is called."""
    trigger = inv.get("trigger", {})
    requires = inv.get("requires", {})
    inv_id = inv.get("id", "")
    req_tool = requires.get("tool", "")
    req_input = requires.get("input_pattern", "")

    # Check if this tool call SATISFIES any pending invariant of this type
    if tool_matches(tool_name, req_tool):
        if not req_input or input_matches(command, req_input):
            state["pending"] = [
                p for p in state["pending"]
                if p["invariant_id"] != inv_id
            ]

    # Check if any pending invariant of this type has expired
    messages = []
    remaining = []
    for p in state["pending"]:
        if p["invariant_id"] != inv_id:
            remaining.append(p)
            continue
        if state["total_calls"] >= p["deadline_seq"]:
            msg = inv.get("message", f"Invariant {inv_id} violated")
            msg = msg.replace("{file}", p.get("file", "unknown"))
            messages.append(msg)
            mark_fired(state, inv_id)
        else:
            remaining.append(p)
    state["pending"] = remaining

    # Does this tool call match the trigger? Register new pending.
    if tool_matches(tool_name, trigger.get("tool", "")):
        trigger_match = True
        if trigger.get("path_pattern"):
            trigger_match = path_matches(file_path, trigger["path_pattern"])
        if trigger_match:
            within = requires.get("within", 15)
            state["pending"].append({
                "invariant_id": inv_id,
                "triggered_at_seq": state["total_calls"],
                "deadline_seq": state["total_calls"] + within,
                "file": os.path.basename(file_path) if file_path else "",
            })

    return messages[0] if messages else None


def check_session_requires(inv: dict, state: dict,
                           tool_name: str) -> str | None:
    """Check: before first edit in session, analysis tool must be called."""
    trigger = inv.get("trigger", {})
    requires = inv.get("requires", {})

    if trigger.get("event") != "first_edit_in_session":
        return None
    if tool_name not in ("Edit", "Write"):
        return None
    if state["files_edited"]:
        return None  # Not the first edit

    # Check if required analysis tools were called
    req_pattern = requires.get("tool_pattern", "")
    if req_pattern:
        for entry in state["trajectory"]:
            if tool_matches(entry["tool"], req_pattern):
                return None

    return inv.get("message", f"Invariant {inv['id']} violated")


def evaluate_invariants(config: dict, state: dict, tool_name: str,
                        tool_input: dict) -> list[dict]:
    """Evaluate all invariants against current state. Returns messages."""
    file_path = extract_path(tool_name, tool_input)
    command = extract_command(tool_name, tool_input)
    messages = []

    for inv in config.get("invariants", []):
        inv_id = inv.get("id", "")
        if in_cooldown(state, inv_id):
            continue

        inv_type = inv.get("type", "preceded_by")
        msg = None

        if inv_type == "preceded_by":
            msg = check_preceded_by(inv, state, tool_name, file_path)
        elif inv_type == "followed_by":
            msg = check_followed_by(
                inv, state, tool_name, file_path, command)
        elif inv_type == "session_requires":
            msg = check_session_requires(inv, state, tool_name)

        if msg:
            severity = inv.get("severity", "soft")
            mark_fired(state, inv_id)
            messages.append({"text": msg, "severity": severity})

    return messages


# ── Checkpoint evaluation ─────────────────────────────────────────

def evaluate_checkpoints(config: dict, state: dict) -> list[dict]:
    """Evaluate periodic checkpoint conditions."""
    messages = []

    for cp in config.get("checkpoints", []):
        cp_id = cp.get("id", "")
        if in_cooldown(state, cp_id):
            continue

        condition = cp.get("condition", "")
        repeat = cp.get("repeat_every", 25)
        triggered = False

        if "calls_since_user" in condition:
            try:
                threshold = int(re.search(r'\d+', condition).group())
                if (state["calls_since_user"] >= threshold
                        and state["calls_since_user"] % repeat == 0):
                    triggered = True
            except (AttributeError, ValueError):
                pass

        elif "consecutive_edits" in condition:
            try:
                threshold = int(re.search(r'\d+', condition).group())
                if state["consecutive_edits"] >= threshold:
                    triggered = True
            except (AttributeError, ValueError):
                pass

        if triggered:
            msg = cp.get("message", "Checkpoint")
            msg = msg.replace(
                "{calls_since_user}", str(state["calls_since_user"]))
            msg = msg.replace(
                "{consecutive_edits}", str(state["consecutive_edits"]))
            msg = msg.replace("{total_calls}", str(state["total_calls"]))
            mark_fired(state, cp_id)
            messages.append({"text": msg, "severity": "soft"})

    return messages


# ── Event handlers ────────────────────────────────────────────────

def handle_post_tool_use(input_data: dict) -> dict:
    session_id = input_data.get("session_id", "unknown")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    state = load_state(session_id)
    config = load_invariants()

    # Update trajectory
    file_path = extract_path(tool_name, tool_input)
    entry = {
        "tool": tool_name,
        "seq": state["total_calls"],
        "ts": time.time(),
    }
    if file_path:
        entry["path"] = file_path
    state["trajectory"].append(entry)

    # Update counters
    state["total_calls"] += 1
    state["calls_since_user"] += 1

    if tool_name in ("Edit", "Write", "MultiEdit"):
        state["consecutive_edits"] += 1
        if file_path and file_path not in state["files_edited"]:
            state["files_edited"].append(file_path)
    else:
        state["consecutive_edits"] = 0

    if tool_name == "Read" and file_path:
        if file_path not in state["files_read"]:
            state["files_read"].append(file_path)

    if tool_name.startswith("mcp__"):
        if tool_name not in state["analysis_tools"]:
            state["analysis_tools"].append(tool_name)

    # Evaluate
    all_messages = []
    all_messages.extend(
        evaluate_invariants(config, state, tool_name, tool_input))
    all_messages.extend(evaluate_checkpoints(config, state))

    # Keep trajectory bounded (last 200 entries)
    if len(state["trajectory"]) > 200:
        state["trajectory"] = state["trajectory"][-200:]

    save_state(state)
    return format_output(all_messages)


def handle_user_prompt(input_data: dict) -> dict:
    session_id = input_data.get("session_id", "unknown")
    state = load_state(session_id)
    state["calls_since_user"] = 0
    save_state(state)
    return {}


def handle_stop(input_data: dict) -> dict:
    session_id = input_data.get("session_id", "unknown")
    state = load_state(session_id)
    config = load_invariants()

    # Check all pending followed_by — they're about to expire
    messages = []
    inv_map = {inv["id"]: inv for inv in config.get("invariants", [])}

    for p in state["pending"]:
        inv = inv_map.get(p["invariant_id"], {})
        msg = inv.get("message", f"Pending: {p['invariant_id']}")
        msg = msg.replace("{file}", p.get("file", "unknown"))
        severity = inv.get("severity", "soft")
        messages.append({"text": msg, "severity": severity})

    state["pending"] = []
    save_state(state)

    if messages:
        hard = [m for m in messages if m["severity"] == "hard"]
        if hard:
            combined = "\n".join(f"- {m['text']}" for m in messages)
            print(json.dumps({
                "decision": "block",
                "reason": f"Unresolved verification requirements:\n{combined}"
            }), file=sys.stderr)
            sys.exit(2)
        else:
            return format_output(messages)

    return {}


# ── Output formatting ─────────────────────────────────────────────

def format_output(messages: list[dict]) -> dict:
    if not messages:
        return {}

    hard = [m for m in messages if m["severity"] == "hard"]
    soft = [m for m in messages if m["severity"] == "soft"]

    parts = []
    if hard:
        for m in hard:
            parts.append(f"[INVARIANT VIOLATION] {m['text']}")
    if soft:
        for m in soft:
            parts.append(f"[checkpoint] {m['text']}")

    combined = "\n".join(parts)

    if hard:
        print(combined, file=sys.stderr)
        sys.exit(2)

    return {"systemMessage": combined}


# ── Main ──────────────────────────────────────────────────────────

def main():
    event = sys.argv[1] if len(sys.argv) > 1 else "PostToolUse"

    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        input_data = {}

    try:
        if event == "PostToolUse":
            result = handle_post_tool_use(input_data)
        elif event == "UserPromptSubmit":
            result = handle_user_prompt(input_data)
        elif event == "Stop":
            result = handle_stop(input_data)
        else:
            result = {}

        if result:
            print(json.dumps(result), file=sys.stdout)

    except Exception as e:
        # Never block operations due to auditor errors
        err = {"systemMessage": f"Pensieve auditor error: {e}"}
        print(json.dumps(err), file=sys.stdout)

    sys.exit(0)


if __name__ == "__main__":
    main()
