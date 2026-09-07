# Backlog

Based on [`_docs/plan.md`](_docs/plan.md).

## 1. Profiles & profile switcher
Create a `Profile` model (name, role: adult/child, avatar/color). Seed the 4 family
profiles (2 adults, 2 children). Build a simple "who's using this?" landing page to
pick a profile (no password), stored in the session.

## 2. Task model
Create a `Task` model: title, description, difficulty (easy/medium/hard, each with a
fixed point value), assignment mode (direct vs. pool), assigned child (nullable for
pool tasks), recurrence rule (none/daily/specific weekdays), optional deadline.

## 3. Adult: create & assign tasks
View for an adult profile to create a task, set its difficulty, choose direct
assignment (pick a child) or pool, and set recurrence/deadline.

## 4. Child: task list (assigned + pool)
View for a child profile showing their assigned tasks and the shared pool. Allow
claiming a pool task (assigns it to that child).

## 5. Recurring task generation
Logic (e.g. a management command or on-demand generation) that creates task
instances from a recurring task's schedule so children see the right tasks each day.

## 6. Completion flow with photos
Child marks a task as done, optionally uploading "before" and "after" photos
(`ImageField`). Task status becomes "pending approval".

## 7. Adult: review & approve completions
View listing tasks pending approval with their photos. Adult approves (awards the
task's points to the child) or sends back.

## 8. Points balance
Track each child's point balance (derived from approved completions minus
redemptions, or a running total updated on approval/redemption).

## 9. Reward catalog & redemption
`Reward` model (name, point cost) manageable by adults. Child-facing view listing
rewards they can afford; redeeming immediately deducts points (no approval needed)
and records a `Redemption`.

## 10. History views
- Completed-tasks log (who, what, when, approved by whom).
- Redemption history, visible to adults.

## 11. Deadline reminders
Simple on-page indicator (e.g. "due today", "overdue") for tasks with a deadline —
no penalties, just visibility.

## 12. Tests
Cover: task creation/assignment, pool claiming, completion + approval awarding
correct points, reward redemption deducting points correctly, recurring task
generation.
