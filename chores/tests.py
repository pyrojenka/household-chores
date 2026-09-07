from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from .models import Profile, Task
from .recurrence import WEEKDAY_CODES, generate_recurring_tasks


class ProfileModelTests(TestCase):
    def test_str_includes_name_and_role(self):
        profile = Profile.objects.create(name="Alice", role=Profile.Role.ADULT)
        self.assertEqual(str(profile), "Alice (Adult)")

    def test_is_adult_and_is_child(self):
        adult = Profile.objects.create(name="Alice", role=Profile.Role.ADULT)
        child = Profile.objects.create(name="Bob", role=Profile.Role.CHILD)

        self.assertTrue(adult.is_adult)
        self.assertFalse(adult.is_child)
        self.assertTrue(child.is_child)
        self.assertFalse(child.is_adult)


class SeedDataTests(TestCase):
    def test_seed_migration_creates_four_family_profiles(self):
        self.assertEqual(Profile.objects.count(), 4)
        self.assertEqual(Profile.objects.filter(role=Profile.Role.ADULT).count(), 2)
        self.assertEqual(Profile.objects.filter(role=Profile.Role.CHILD).count(), 2)


class ProfileSwitcherViewTests(TestCase):
    def test_lists_all_profiles(self):
        response = self.client.get(reverse("profile_switcher"))

        self.assertEqual(response.status_code, 200)
        for profile in Profile.objects.all():
            self.assertContains(response, profile.name)


class SelectProfileViewTests(TestCase):
    def test_selecting_profile_stores_it_in_session_and_redirects_home(self):
        profile = Profile.objects.first()

        response = self.client.get(reverse("select_profile", args=[profile.id]))

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(self.client.session["profile_id"], profile.id)


class HomeViewTests(TestCase):
    def test_redirects_to_profile_switcher_when_no_profile_selected(self):
        response = self.client.get(reverse("home"))

        self.assertRedirects(response, reverse("profile_switcher"))

    def test_shows_selected_profile(self):
        profile = Profile.objects.get(name="Emma")
        session = self.client.session
        session["profile_id"] = profile.id
        session.save()

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Emma")
        self.assertContains(response, "Child")


class SwitchProfileViewTests(TestCase):
    def test_clears_session_and_redirects_to_profile_switcher(self):
        profile = Profile.objects.first()
        session = self.client.session
        session["profile_id"] = profile.id
        session.save()

        response = self.client.get(reverse("switch_profile"))

        self.assertRedirects(response, reverse("profile_switcher"))
        self.assertNotIn("profile_id", self.client.session)


class RecurringTaskGenerationTests(TestCase):
    def setUp(self):
        self.adult = Profile.objects.get(name="Mom")
        self.emma = Profile.objects.get(name="Emma")

    def test_generates_daily_instance_for_today(self):
        template = Task.objects.create(
            title="Make bed",
            difficulty=Task.Difficulty.EASY,
            assignment_mode=Task.AssignmentMode.DIRECT,
            assigned_to=self.emma,
            recurrence=Task.Recurrence.DAILY,
            created_by=self.adult,
        )

        created = generate_recurring_tasks(for_date=date.today())

        self.assertEqual(len(created), 1)
        instance = created[0]
        self.assertEqual(instance.template, template)
        self.assertEqual(instance.scheduled_date, date.today())
        self.assertEqual(instance.assigned_to, self.emma)
        self.assertEqual(instance.recurrence, Task.Recurrence.NONE)
        self.assertEqual(instance.status, Task.Status.TODO)

    def test_running_twice_for_the_same_day_does_not_duplicate(self):
        Task.objects.create(
            title="Make bed",
            difficulty=Task.Difficulty.EASY,
            assignment_mode=Task.AssignmentMode.DIRECT,
            assigned_to=self.emma,
            recurrence=Task.Recurrence.DAILY,
            created_by=self.adult,
        )

        generate_recurring_tasks(for_date=date.today())
        second_run = generate_recurring_tasks(for_date=date.today())

        self.assertEqual(second_run, [])
        self.assertEqual(Task.objects.filter(recurrence=Task.Recurrence.NONE).count(), 1)

    def test_weekly_task_generated_only_on_matching_weekday(self):
        base_date = date(2024, 1, 1)
        matching_code = WEEKDAY_CODES[base_date.weekday()]
        non_matching_date = base_date + timedelta(days=1)

        Task.objects.create(
            title="Vacuum",
            difficulty=Task.Difficulty.MEDIUM,
            assignment_mode=Task.AssignmentMode.POOL,
            recurrence=Task.Recurrence.WEEKLY,
            weekdays=matching_code,
            created_by=self.adult,
        )

        self.assertEqual(generate_recurring_tasks(for_date=non_matching_date), [])

        created = generate_recurring_tasks(for_date=base_date)
        self.assertEqual(len(created), 1)
        self.assertIsNone(created[0].assigned_to)


class TaskListViewTests(TestCase):
    def setUp(self):
        self.adult = Profile.objects.get(name="Mom")
        self.emma = Profile.objects.get(name="Emma")

    def _select(self, profile):
        session = self.client.session
        session["profile_id"] = profile.id
        session.save()

    def test_recurring_template_is_not_shown_as_a_regular_task_to_the_child(self):
        Task.objects.create(
            title="Make bed",
            difficulty=Task.Difficulty.EASY,
            assignment_mode=Task.AssignmentMode.DIRECT,
            assigned_to=self.emma,
            recurrence=Task.Recurrence.DAILY,
            created_by=self.adult,
        )
        self._select(self.emma)

        response = self.client.get(reverse("task_list"))

        self.assertContains(response, "Make bed")
        self.assertEqual(Task.objects.filter(recurrence=Task.Recurrence.NONE).count(), 1)

    def test_adult_sees_template_separately_from_generated_instances(self):
        Task.objects.create(
            title="Make bed",
            difficulty=Task.Difficulty.EASY,
            assignment_mode=Task.AssignmentMode.DIRECT,
            assigned_to=self.emma,
            recurrence=Task.Recurrence.DAILY,
            created_by=self.adult,
        )
        self._select(self.adult)

        response = self.client.get(reverse("task_list"))

        self.assertEqual(list(response.context["templates"]), list(Task.objects.filter(recurrence=Task.Recurrence.DAILY)))
        self.assertEqual(response.context["tasks"].count(), 1)
