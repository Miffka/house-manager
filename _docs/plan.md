# Chore Manager — Project Scope

## Problem
Solving for **forgetting** (tasks slip through the cracks) and **visibility** (no shared view of what needs doing).

## Users
- 2 people: you + partner

## Task Model
- **Flexible pool** — no fixed schedule, no rotation
- Populated two ways:
  - **Recurring templates** (e.g. "vacuum every 5 days" auto-reappears)
  - **Manual ad-hoc adds** (either person adds tasks as they come up)

## Assignment
- **Auto-assigned** by the app, balanced based on recent completion activity (fairness layer)

## Reminders
- **Escalating**: gentle nudge when due → stronger nudge if still undone

## History / Tracking
- **Recent-only log** (e.g. last 7–14 days)
- No long-term stats or full history — just enough data to drive auto-assignment fairness

## Platform
- **Telegram bot**
  - Shared group chat, both people interact with the same bot
  - Chosen for: meets you where you already chat, free API, good library support, easiest of the considered options to build

## Core Loop
1. Task enters the pool (via template or manual add)
2. Bot auto-assigns it to whoever's "behind" based on recent activity
3. Bot reminds — escalating if ignored
4. Person marks task done in chat
5. Completion logged to recent history → feeds next auto-assignment decision

## Open Next Steps (not yet decided)
- Exact auto-assign fairness algorithm (e.g. how "behind" is calculated, weighting by task effort/type)
- Telegram bot commands / UX flow (e.g. `/done`, `/add`, `/pool`)
- Escalation timing (how long before nudge #2, who else gets notified)
- Recurring template config (interval, task list, skip/snooze rules)