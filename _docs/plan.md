# Household Chores Manager — Spec

## Idea
A tool for managing shared household chores, used by one specific family: 2 adults and 2 children.

## Users & Accounts
- Single-family app — no support for multiple registered families (single tenant).
- One shared family account with profile switching (no passwords for children).
- 4 profiles: 2 adults, 2 children.

## Tasks (Chores)
- Created and assigned by an adult.
- Two assignment modes are both supported:
  - Assigned directly to a specific child.
  - Placed in a shared pool that any child can claim.
- Support both one-time tasks and recurring tasks (e.g., daily, specific days of the week).
- Each task has a fixed difficulty category (e.g., easy/medium/hard) with a preset point value — no manual point entry per task.
- Tasks can have a deadline/reminder, but there is no penalty for missing it (reminder only, no consequences).

## Completion Flow
1. Child marks a task as done.
2. Optionally, the child attaches a "before" and "after" photo as proof.
3. An adult reviews and confirms (approves) the completion.
4. On approval, points are awarded to the child.

## Rewards
- Adult maintains a catalog of rewards (name + point cost); adult can add new rewards at any time.
- Children redeem points from the catalog.
- Redemption is automatic — no adult approval needed to spend points.
- Adult can see the history of what was redeemed (visibility, not approval).

## History
- A log/history of completed tasks is kept and viewable.

## Tech Stack
- Django (web application).

## Out of Scope (for now)
- Multiple families / multi-tenancy.
- Per-child login credentials (passwords).
- Point penalties for missed deadlines.
- Leaderboard/competitive stats between children (history log is enough for MVP).
