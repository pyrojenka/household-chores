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
