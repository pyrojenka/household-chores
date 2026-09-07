from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Profile, Redemption, Reward, Task
from .recurrence import WEEKDAY_CODES, generate_recurring_tasks

TINY_GIF = (
    b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xff\xff\xff\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00"
    b"\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
)


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


class MarkDoneViewTests(TestCase):
    def setUp(self):
        self.adult = Profile.objects.get(name="Mom")
        self.emma = Profile.objects.get(name="Emma")
        self.max = Profile.objects.get(name="Max")
        self.task = Task.objects.create(
            title="Wash dishes",
            difficulty=Task.Difficulty.EASY,
            assignment_mode=Task.AssignmentMode.DIRECT,
            assigned_to=self.emma,
            created_by=self.adult,
        )

    def _select(self, profile):
        session = self.client.session
        session["profile_id"] = profile.id
        session.save()

    def test_marking_done_without_photos_moves_task_to_pending_approval(self):
        self._select(self.emma)

        response = self.client.post(reverse("mark_done", args=[self.task.id]), {})

        self.assertRedirects(response, reverse("task_list"))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.DONE)
        self.assertIsNotNone(self.task.completed_at)

    def test_marking_done_with_before_and_after_photos_saves_them(self):
        self._select(self.emma)
        before = SimpleUploadedFile("before.gif", TINY_GIF, content_type="image/gif")
        after = SimpleUploadedFile("after.gif", TINY_GIF, content_type="image/gif")

        self.client.post(
            reverse("mark_done", args=[self.task.id]),
            {"before_photo": before, "after_photo": after},
        )

        self.task.refresh_from_db()
        self.assertTrue(self.task.before_photo.name)
        self.assertTrue(self.task.after_photo.name)
        self.task.before_photo.delete(save=False)
        self.task.after_photo.delete(save=False)

    def test_other_childs_task_cannot_be_marked_done(self):
        self._select(self.max)

        response = self.client.post(reverse("mark_done", args=[self.task.id]), {})

        self.assertEqual(response.status_code, 404)

    def test_pending_task_is_excluded_from_todo_list_and_shown_as_pending(self):
        self.task.status = Task.Status.DONE
        self.task.save()
        self._select(self.emma)

        response = self.client.get(reverse("task_list"))

        self.assertNotIn(self.task, response.context["my_tasks"])
        self.assertIn(self.task, response.context["pending_tasks"])


class ApprovalViewTests(TestCase):
    def setUp(self):
        self.adult = Profile.objects.get(name="Mom")
        self.emma = Profile.objects.get(name="Emma")
        self.task = Task.objects.create(
            title="Wash dishes",
            difficulty=Task.Difficulty.MEDIUM,
            assignment_mode=Task.AssignmentMode.DIRECT,
            assigned_to=self.emma,
            created_by=self.adult,
            status=Task.Status.DONE,
        )

    def _select(self, profile):
        session = self.client.session
        session["profile_id"] = profile.id
        session.save()

    def test_pending_approvals_lists_done_tasks(self):
        self._select(self.adult)

        response = self.client.get(reverse("pending_approvals"))

        self.assertContains(response, "Wash dishes")

    def test_approving_awards_points_to_the_child(self):
        self._select(self.adult)
        self.assertEqual(self.emma.points_balance, 0)

        response = self.client.post(reverse("approve_task", args=[self.task.id]))

        self.assertRedirects(response, reverse("pending_approvals"))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.APPROVED)
        self.assertEqual(self.task.approved_by, self.adult)
        self.assertIsNotNone(self.task.approved_at)
        self.assertEqual(self.emma.points_balance, 20)

    def test_rejecting_sends_task_back_to_todo(self):
        self._select(self.adult)

        response = self.client.post(reverse("reject_task", args=[self.task.id]))

        self.assertRedirects(response, reverse("pending_approvals"))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.TODO)
        self.assertEqual(self.emma.points_balance, 0)

    def test_child_cannot_access_pending_approvals(self):
        self._select(self.emma)

        response = self.client.get(reverse("pending_approvals"))

        self.assertRedirects(response, reverse("task_list"))

    def test_child_cannot_approve_a_task(self):
        self._select(self.emma)

        response = self.client.post(reverse("approve_task", args=[self.task.id]))

        self.assertRedirects(response, reverse("home"))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.DONE)


class RewardRedemptionTests(TestCase):
    def setUp(self):
        self.adult = Profile.objects.get(name="Mom")
        self.emma = Profile.objects.get(name="Emma")
        self.approved_task = Task.objects.create(
            title="Wash dishes",
            difficulty=Task.Difficulty.HARD,
            assignment_mode=Task.AssignmentMode.DIRECT,
            assigned_to=self.emma,
            created_by=self.adult,
            status=Task.Status.APPROVED,
        )
        self.reward = Reward.objects.create(name="Movie night", point_cost=30, created_by=self.adult)

    def _select(self, profile):
        session = self.client.session
        session["profile_id"] = profile.id
        session.save()

    def test_redeeming_deducts_points_and_records_redemption(self):
        self._select(self.emma)
        self.assertEqual(self.emma.points_balance, 30)

        response = self.client.post(reverse("redeem_reward", args=[self.reward.id]))

        self.assertRedirects(response, reverse("reward_catalog"))
        self.assertEqual(self.emma.points_balance, 0)
        redemption = Redemption.objects.get(profile=self.emma)
        self.assertEqual(redemption.reward_name, "Movie night")
        self.assertEqual(redemption.points_spent, 30)

    def test_cannot_redeem_without_enough_points(self):
        expensive_reward = Reward.objects.create(name="New bike", point_cost=1000, created_by=self.adult)
        self._select(self.emma)

        self.client.post(reverse("redeem_reward", args=[expensive_reward.id]))

        self.assertEqual(self.emma.points_balance, 30)
        self.assertFalse(Redemption.objects.filter(reward=expensive_reward).exists())

    def test_redemption_history_visible_to_adult(self):
        Redemption.objects.create(
            profile=self.emma, reward=self.reward, reward_name=self.reward.name, points_spent=30
        )
        self._select(self.adult)

        response = self.client.get(reverse("redemption_history"))

        self.assertContains(response, "Movie night")
        self.assertContains(response, "Emma")

    def test_child_cannot_access_redemption_history(self):
        self._select(self.emma)

        response = self.client.get(reverse("redemption_history"))

        self.assertRedirects(response, reverse("home"))

    def test_child_cannot_create_reward(self):
        self._select(self.emma)

        response = self.client.post(reverse("create_reward"), {"name": "Hack", "point_cost": 1})

        self.assertRedirects(response, reverse("reward_catalog"))
        self.assertFalse(Reward.objects.filter(name="Hack").exists())


class TaskHistoryViewTests(TestCase):
    def setUp(self):
        self.adult = Profile.objects.get(name="Mom")
        self.emma = Profile.objects.get(name="Emma")
        self.max = Profile.objects.get(name="Max")
        self.emma_task = Task.objects.create(
            title="Wash dishes",
            difficulty=Task.Difficulty.EASY,
            assignment_mode=Task.AssignmentMode.DIRECT,
            assigned_to=self.emma,
            created_by=self.adult,
            status=Task.Status.APPROVED,
        )
        self.max_task = Task.objects.create(
            title="Take out trash",
            difficulty=Task.Difficulty.EASY,
            assignment_mode=Task.AssignmentMode.DIRECT,
            assigned_to=self.max,
            created_by=self.adult,
            status=Task.Status.APPROVED,
        )
        self.pending_task = Task.objects.create(
            title="Still pending",
            difficulty=Task.Difficulty.EASY,
            assignment_mode=Task.AssignmentMode.DIRECT,
            assigned_to=self.emma,
            created_by=self.adult,
            status=Task.Status.DONE,
        )

    def _select(self, profile):
        session = self.client.session
        session["profile_id"] = profile.id
        session.save()

    def test_adult_sees_all_completed_tasks(self):
        self._select(self.adult)

        response = self.client.get(reverse("task_history"))

        self.assertIn(self.emma_task, response.context["tasks"])
        self.assertIn(self.max_task, response.context["tasks"])
        self.assertNotIn(self.pending_task, response.context["tasks"])

    def test_child_sees_only_their_own_completed_tasks(self):
        self._select(self.emma)

        response = self.client.get(reverse("task_history"))

        self.assertIn(self.emma_task, response.context["tasks"])
        self.assertNotIn(self.max_task, response.context["tasks"])
