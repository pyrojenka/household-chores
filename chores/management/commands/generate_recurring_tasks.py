from django.core.management.base import BaseCommand

from chores.recurrence import generate_recurring_tasks


class Command(BaseCommand):
    help = "Create today's task instances from recurring (daily/weekly) task templates."

    def handle(self, *args, **options):
        created = generate_recurring_tasks()
        self.stdout.write(self.style.SUCCESS(f"Created {len(created)} task instance(s)."))
