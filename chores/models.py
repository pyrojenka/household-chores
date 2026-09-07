from django.db import models


class Profile(models.Model):
    class Role(models.TextChoices):
        ADULT = "adult", "Adult"
        CHILD = "child", "Child"

    name = models.CharField(max_length=50)
    role = models.CharField(max_length=10, choices=Role.choices)
    color = models.CharField(max_length=7, default="#4a90d9", help_text="Hex color for the profile avatar")

    class Meta:
        ordering = ["role", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

    @property
    def is_adult(self):
        return self.role == self.Role.ADULT

    @property
    def is_child(self):
        return self.role == self.Role.CHILD


class Task(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    POINTS_BY_DIFFICULTY = {
        Difficulty.EASY: 10,
        Difficulty.MEDIUM: 20,
        Difficulty.HARD: 30,
    }

    class AssignmentMode(models.TextChoices):
        DIRECT = "direct", "Direct"
        POOL = "pool", "Shared pool"

    class Recurrence(models.TextChoices):
        NONE = "none", "One-time"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Specific weekdays"

    class Status(models.TextChoices):
        TODO = "todo", "To do"
        DONE = "done", "Done"
        APPROVED = "approved", "Approved"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.EASY)
    assignment_mode = models.CharField(max_length=10, choices=AssignmentMode.choices, default=AssignmentMode.DIRECT)
    assigned_to = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks",
        limit_choices_to={"role": Profile.Role.CHILD},
    )
    recurrence = models.CharField(max_length=10, choices=Recurrence.choices, default=Recurrence.NONE)
    weekdays = models.CharField(
        max_length=20,
        blank=True,
        help_text="Comma-separated weekday abbreviations, e.g. MON,WED,FRI (used when recurrence is weekly)",
    )
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.TODO)
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="created_tasks",
        limit_choices_to={"role": Profile.Role.ADULT},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def points(self):
        return self.POINTS_BY_DIFFICULTY[self.difficulty]
