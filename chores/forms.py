from django import forms

from .models import Profile, Reward, Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "difficulty",
            "assignment_mode",
            "assigned_to",
            "recurrence",
            "weekdays",
            "deadline",
        ]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = Profile.objects.filter(role=Profile.Role.CHILD)
        self.fields["assigned_to"].required = False


class CompletionForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["before_photo", "after_photo"]


class RewardForm(forms.ModelForm):
    class Meta:
        model = Reward
        fields = ["name", "point_cost"]
