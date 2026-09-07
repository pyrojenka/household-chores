from django.contrib import admin

from .models import Profile, Redemption, Reward, Task


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "color")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "difficulty", "assignment_mode", "assigned_to", "status", "created_by")
    list_filter = ("status", "difficulty", "assignment_mode")


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("name", "point_cost", "created_by")


@admin.register(Redemption)
class RedemptionAdmin(admin.ModelAdmin):
    list_display = ("profile", "reward_name", "points_spent", "redeemed_at")
