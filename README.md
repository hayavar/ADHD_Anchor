# Anchor

> **An externalized focus co-pilot for neurodivergent deep work.**

Anchor helps users stay aligned with the task they intentionally chose to work on. Instead of blocking websites or policing behavior, Anchor observes lightweight activity signals, uses AI to understand whether the activity is related to the declared task, and gently surfaces a reminder when sustained drift is detected.

## 🚀 What Anchor Does

At the start of a focus session, the user declares:

```text
Build a Flask application
```

Anchor then:

1. Saves the declared task locally.
2. Launches a watched terminal session.
3. Logs terminal activity to `~/.anchor/activity.log`.
4. Checks whether Safari is open.
5. Captures the active Safari tab title.
6. Adds the Safari title to the activity log.
7. Every 30 seconds, reads the task and activity data.
8. Sends the context to `task.py`.
9. Uses Gemini to classify the activity as:
   - `ON_TASK`
   - `OFF_TASK`
   - `UNCLEAR`
10. When `OFF_TASK` is detected, Anchor can show a macOS notification containing the Safari tab title.

Example:

```text
Anchor
Focus check

You may be drifting from your task.
Safari: YouTube
```

The goal is not to punish distraction. The goal is to make the user's own intention visible at the moment attention starts moving away from it.

---

## 🧠 Why Anchor?

Traditional productivity tools often use:

- Website blocking
- App restrictions
- Timers
- To-do lists
- Generic reminders

Anchor takes a different approach:

```text
Intent
  ↓
Observe
  ↓
Understand
  ↓
Detect sustained drift
  ↓
Gentle nudge
```

The user remains in control.

---

## 🏗️ Current Architecture

```text
                    ┌──────────────────────┐
                    │   Declared Task      │
                    │  ~/.anchor/task.json │
                    └──────────┬───────────┘
                               │
                               │
              ┌────────────────▼────────────────┐
              │         Anchor Service          │
              │        app_service.py           │
              └───────────────┬─────────────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
      Watched Terminal     Safari Tab       30-sec Timer
             │                │                │
             ▼                ▼                │
      activity.log      Active tab title       │
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                         task.py
                              │
                              ▼
                           Gemini
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
              ON_TASK      OFF_TASK     UNCLEAR
                               │
                               ▼
                        macOS notification
```

---

## 📁 Project Structure

```text
ADHD/
├── app_service.py       # Anchor session + terminal monitoring
├── task.py              # Gemini-based task relevance classifier
├── .env                 # Local API key (do not commit)
├── .gitignore
└── README.md
```

Anchor also creates local session data:

```text
~/.anchor/
├── task.json
├── activity.log
└── checker_debug.log    # optional debugging output
```

---

## ⚙️ Requirements

- macOS
- Python 3.10+
- Safari
- A Gemini API key
- Python packages:
  - `python-dotenv`
  - `google-genai`

Install dependencies:

```bash
pip3 install -U google-genai python-dotenv
```

---

## 🔐 Gemini API Key

Create a `.env` file in the project folder:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Never commit `.env` to GitHub.

Recommended `.gitignore`:

```gitignore
.env
__pycache__/
*.pyc
.DS_Store
```

---

## ▶️ Run Anchor

From the project directory:

```bash
python3 app_service.py
```

Anchor will ask:

```text
========================================================
  ANCHOR — starting a focus session
========================================================

What are you working on right now?
>
```

Enter your intended task and continue using the terminal normally.

Example:

```text
Build a Flask application
```

Anchor starts a watched shell and monitors activity in the background.

---

## 🌐 Safari Monitoring

When Safari is running, Anchor retrieves the title of the active tab.

For example:

```text
[2026-09-06 16:33:07] [Safari] Active tab: Flask Documentation
```

or:

```text
[2026-09-06 16:33:07] [Safari] Active tab: YouTube
```

The Safari title is included as context when task relevance is evaluated.

### macOS Permissions

The first time Anchor accesses Safari, macOS may ask for permission to control Safari.

Allow Terminal/Python to automate Safari.

You can review this under:

```text
System Settings
→ Privacy & Security
→ Automation
```

---

## 🤖 AI Classification

`task.py` sends the declared task and recent activity to Gemini.

The classifier returns one of:

### `ON_TASK`

The activity appears directly related to the declared task or is a reasonable supporting activity.

### `OFF_TASK`

The activity appears clearly unrelated to the declared task.

### `UNCLEAR`

There is not enough evidence to confidently classify the activity.

Anchor intentionally avoids judging individual commands in isolation.

For example, if the task is:

```text
Build a Flask application
```

then these can all be valid supporting activities:

```text
pip install flask
python app.py
git status
reading Flask documentation
debugging an error
```

---

## 🔔 Drift Notification

When an activity check returns `OFF_TASK`, Anchor can show a native macOS notification.

Example:

```text
Anchor
Focus check

You may be drifting from your task.
Safari: YouTube
```

The terminal itself remains clean; the AI classification is not printed into the working shell.

---

## 🧪 Testing the Notification

Before testing the full Anchor workflow, verify macOS notifications:

```bash
osascript -e 'display notification "Anchor popup test" with title "Anchor" subtitle "Focus check"'
```

If macOS displays the notification, the notification mechanism is working.

---

## 📊 Example Activity Log

A session may look like:

```text
[2026-09-06 16:32:38] python app.py
[2026-09-06 16:32:39] Running Flask application
[2026-09-06 16:33:07] [Safari] Active tab: Flask Documentation
[2026-09-06 16:33:09] python test.py
```

The same log can contain unrelated activity:

```text
[2026-09-06 16:34:07] [Safari] Active tab: YouTube
```

Gemini uses the declared task plus activity context to determine relevance.

---

## 🛡️ Design Principles

### Intention-first

Anchor starts from what the user says they want to accomplish.

### Context-aware

A command is not automatically considered distracting just because it looks unrelated at first glance.

### Gentle intervention

Anchor is designed to nudge rather than block.

### User-controlled

The user can work however they choose. Anchor provides feedback rather than enforcing restrictions.

### Local session data

Session task/activity data is stored locally under:

```text
~/.anchor/
```

---

## 🚧 Current Prototype Status

This repository represents an early hackathon prototype.

### Implemented

- Declared task capture
- Local session storage
- Watched terminal session
- Terminal activity logging
- 30-second monitoring cycle
- Safari active tab detection
- Gemini task relevance classification
- Native macOS notification support

### Next Improvements

- Analyze only new activity since the previous check
- Add persistent drift scoring instead of reacting to one `OFF_TASK`
- Improve prompt quality and classification consistency
- Add a small visual dashboard
- Add session timeline and focus analytics
- Support additional applications beyond Safari
- Add configurable notification behavior
- Reduce noisy terminal capture such as individual keystrokes
- Add tests and stronger error handling

---

## ⚠️ Prototype Limitations

Anchor currently works best as a local macOS prototype.

The current terminal logger captures pseudo-terminal output, which can include individual characters while a command is being typed. This is visible in the activity log and is an area for improvement.

Safari monitoring currently focuses on the active tab title rather than page contents.

The AI classification depends on the quality and availability of the Gemini API.

---
