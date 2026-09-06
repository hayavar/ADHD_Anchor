#!/usr/bin/env python3
"""
Anchor — Stage 2
================

What this does:

1. Asks the user what they're working on.
2. Saves the declared task to ~/.anchor/task.json.
3. Starts a watched terminal shell.
4. Logs terminal activity to ~/.anchor/activity.log.
5. Starts a 30-second timer.
6. Every 30 seconds:
      - reads task.json using `cat`
      - reads activity.log using `cat`
      - sends the collected activity to task.py
7. task.py determines whether the activity points to the declared task.

This stage does NOT make decisions itself.
task.py is responsible for determining whether activity is
related to the declared task.
"""

import pty
import os
import sys
import json
import datetime
import pathlib
import subprocess
import threading
import time

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SESSION_DIR = pathlib.Path.home() / ".anchor"

TASK_FILE = SESSION_DIR / "task.json"
LOG_FILE = SESSION_DIR / "activity.log"

# Your task.py location
TASK_SCRIPT = pathlib.Path(__file__).parent / "task.py"

CHECK_INTERVAL = 30


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

monitoring = True
monitor_thread = None


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


def ask_task() -> dict:
    """Ask the user what they're doing and save it as this session's task."""

    print("=" * 56)
    print("  ANCHOR — starting a focus session")
    print("=" * 56)

    task = input("\nWhat are you working on right now?\n> ").strip()

    while not task:
        task = input("(Can't be empty) What are you working on?\n> ").strip()

    session = {
        "task": task,
        "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }

    TASK_FILE.write_text(json.dumps(session, indent=2))

    # Start a fresh activity log for this session
    LOG_FILE.write_text("")

    print(f'\nGot it: "{task}"')
    print("Anchor is now watching this terminal session.")
    print(f"Session info: {TASK_FILE}")
    print(f"Activity log: {LOG_FILE}")
    print(f"Task checker: {TASK_SCRIPT}")
    print(f"Drift check interval: {CHECK_INTERVAL} seconds")
    print("(Ctrl+D or `exit` ends the session)\n")

    return session


# ---------------------------------------------------------------------------
# Activity logging
# ---------------------------------------------------------------------------


def append_log(raw: bytes) -> None:
    """Timestamp and append a chunk of terminal I/O to activity.log."""

    if not raw:
        return

    text = raw.decode("utf-8", errors="ignore")

    if not text.strip():
        return

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", encoding="utf-8") as f:

        for line in text.splitlines():

            if line.strip():
                f.write(f"[{ts}] {line}\n")


# ---------------------------------------------------------------------------
# Read files using terminal `cat`
# ---------------------------------------------------------------------------
def get_safari_tab_title() -> str:
    """Return the title of the currently active Safari tab."""

    script = """
    tell application "System Events"
        if exists process "Safari" then
            tell application "Safari"
                if (count of windows) > 0 then
                    return name of current tab of front window
                end if
            end tell
        end if
    end tell
    return ""
    """

    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=5
        )

        if result.returncode != 0:
            return ""

        return result.stdout.strip()

    except Exception:
        return ""


def log_safari_activity() -> str:
    """Check Safari, log the active tab title, and return the title."""

    title = get_safari_tab_title()

    if not title:
        return ""

    ts = datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(
            f"[{ts}] [Safari] Active tab: {title}\n"
        )

    return title

def cat_file(path: pathlib.Path) -> str:
    """
    Read a file by executing the terminal `cat` command.

    This intentionally uses the same mechanism you requested:
        cat ~/.anchor/activity.log
        cat ~/.anchor/task.json
    """

    try:

        result = subprocess.run(
            ["cat", str(path)], capture_output=True, text=True, timeout=5
        )

        if result.returncode != 0:
            print(f"\n[Anchor] Failed to cat {path}: " f"{result.stderr.strip()}")
            return ""

        return result.stdout

    except Exception as e:

        print(f"\n[Anchor] Error reading {path}: {e}")

        return ""


# ---------------------------------------------------------------------------
# Task analysis
# ---------------------------------------------------------------------------


def show_drift_popup(safari_title=""):
    """Show a macOS notification when Anchor detects drift."""

    if safari_title:
        message = (
            "You may be drifting from your task. "
            f"Safari: {safari_title}"
        )
    else:
        message = "You may be drifting from your declared task."

    message = (
        message
        .replace("\\", "\\\\")
        .replace('"', '\\"')
    )

    try:
        result = subprocess.run(
            [
                "osascript",
                "-e",
                f'display notification "{message}" '
                'with title "Anchor" '
                'subtitle "Focus check"'
            ],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Log notification errors instead of hiding them
        if result.returncode != 0:
            with open(
                SESSION_DIR / "anchor_error.log",
                "a",
                encoding="utf-8"
            ) as f:
                f.write(
                    f"\nNotification error: {result.stderr}\n"
                )

    except Exception as e:
        with open(
            SESSION_DIR / "anchor_error.log",
            "a",
            encoding="utf-8"
        ) as f:
            f.write(
                f"\nNotification exception: {e}\n"
            )


def run_task_checker(
    task_data: str,
    activity_data: str,
    safari_title: str = ""
) -> None:

    if not TASK_SCRIPT.exists():
        return

    try:
        task_json = json.loads(task_data)
        declared_task = task_json["task"]

        result = subprocess.run(
            [
                sys.executable,
                str(TASK_SCRIPT),
                declared_task,
                activity_data
            ],
            capture_output=True,
            text=True,
            timeout=25
        )

        output = result.stdout.strip().upper()
        error = result.stderr.strip()

        # Save checker diagnostics to a file, NOT the terminal
        debug_file = SESSION_DIR / "checker_debug.log"

        with open(debug_file, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 60 + "\n")
            f.write(f"Task: {declared_task}\n")
            f.write(f"Safari: {safari_title}\n")
            f.write(f"Return code: {result.returncode}\n")
            f.write(f"Output: {output}\n")
            f.write(f"Error: {error}\n")

        # Trigger popup
        if "OFF_TASK" in output:
            show_drift_popup(safari_title)

    except subprocess.TimeoutExpired:
        with open(
            SESSION_DIR / "checker_debug.log",
            "a",
            encoding="utf-8"
        ) as f:
            f.write("\nGemini/task.py TIMEOUT\n")

    except Exception as e:
        with open(
            SESSION_DIR / "checker_debug.log",
            "a",
            encoding="utf-8"
        ) as f:
            f.write(f"\nAnchor exception: {repr(e)}\n")


# ---------------------------------------------------------------------------
# 30-second monitoring loop
# ---------------------------------------------------------------------------


def monitoring_loop() -> None:
    """
    Every 30 seconds:

        1. cat task.json
        2. cat activity.log
        3. send both to task.py
    """

    print(f"[Anchor] Activity monitor started " f"(checking every {CHECK_INTERVAL}s)")

    while monitoring:

        # Wait first so the initial shell activity has time to accumulate.
        for _ in range(CHECK_INTERVAL):

            if not monitoring:
                return

            time.sleep(1)

        if not monitoring:
            return

               # ---------------------------------------------------------------
        # Check Safari and get active tab title
        # ---------------------------------------------------------------

        safari_title = log_safari_activity()

        # ---------------------------------------------------------------
        # Read task.json through terminal
        # ---------------------------------------------------------------

        task_data = cat_file(TASK_FILE)

        if not task_data:
            continue

        # ---------------------------------------------------------------
        # Read activity.log through terminal
        # ---------------------------------------------------------------

        activity_data = cat_file(LOG_FILE)

        if not activity_data:
            continue

        # ---------------------------------------------------------------
        # Send data to task.py
        # ---------------------------------------------------------------

        run_task_checker(
            task_data,
            activity_data,
            safari_title
        )


# ---------------------------------------------------------------------------
# Watched shell
# ---------------------------------------------------------------------------


def watch_shell() -> None:
    """
    Spawn the user's normal shell inside a pseudo-terminal.

    Terminal output is simultaneously:
        terminal -> user
                  -> activity.log
    """

    global monitoring

    shell = os.environ.get("SHELL", "/bin/zsh")

    env = os.environ.copy()

    env["ANCHOR_ACTIVE"] = "1"

    prev_prompt = env.get("PROMPT", "")

    env["PROMPT"] = f"%F{{yellow}}[anchor]%f " f"{prev_prompt or '%n@%m %1~ %# '}"

    def master_read(fd):

        data = os.read(fd, 1024)

        append_log(data)

        return data

    old_environ = os.environ.copy()

    os.environ.update(env)

    print(
        "Starting the watched shell now — "
        "look for the yellow [anchor] tag in your prompt below."
    )

    print(
        "(If your .zshrc overrides PROMPT, the tag may not show — "
        "logging still works.)"
    )

    print("Run `echo $ANCHOR_ACTIVE` to confirm: it should print 1.\n")

    try:

        pty.spawn([shell], master_read)

    except Exception as e:

        print(f"\n[Anchor] Failed to start watched shell: {e}")

        print("[Anchor] Falling back to a plain shell.")

        os.system(shell)

    finally:

        monitoring = False

        os.environ.clear()
        os.environ.update(old_environ)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():

    global monitoring
    global monitor_thread

    ask_task()

    monitoring = True

    # Start the 30-second monitor in the background.
    monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)

    monitor_thread.start()

    # Start watched shell in the main thread.
    watch_shell()

    # Stop monitoring when shell exits.
    monitoring = False

    if monitor_thread.is_alive():

        monitor_thread.join(timeout=2)

    print("\nSession ended. Anchor stopped watching.")


if __name__ == "__main__":
    main()
