from django.test import TestCase
from django.urls import reverse

from .models import Profile


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
