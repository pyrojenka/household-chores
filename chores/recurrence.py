from datetime import date

from .models import Task

WEEKDAY_CODES = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

RECURRING_TYPES = [Task.Recurrence.DAILY, Task.Recurrence.WEEKLY]


def generate_recurring_tasks(for_date=None):
    """Create today's Task instances from recurring templates, if not already created."""
    for_date = for_date or date.today()
    created = []

    for template in Task.objects.filter(recurrence__in=RECURRING_TYPES):
        if template.recurrence == Task.Recurrence.WEEKLY:
            codes = {code.strip().upper() for code in template.weekdays.split(",") if code.strip()}
            if WEEKDAY_CODES[for_date.weekday()] not in codes:
                continue

        if Task.objects.filter(template=template, scheduled_date=for_date).exists():
            continue

        instance = Task.objects.create(
            title=template.title,
            description=template.description,
            difficulty=template.difficulty,
            assignment_mode=template.assignment_mode,
            assigned_to=template.assigned_to if template.assignment_mode == Task.AssignmentMode.DIRECT else None,
            recurrence=Task.Recurrence.NONE,
            deadline=template.deadline,
            created_by=template.created_by,
            template=template,
            scheduled_date=for_date,
        )
        created.append(instance)

    return created
