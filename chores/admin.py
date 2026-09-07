from django.contrib import admin

from .models import Profile, Task


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "color")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "difficulty", "assignment_mode", "assigned_to", "status", "created_by")
    list_filter = ("status", "difficulty", "assignment_mode")
