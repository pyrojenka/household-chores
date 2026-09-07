from django.shortcuts import get_object_or_404, redirect, render

from .models import Profile


def profile_switcher(request):
    profiles = Profile.objects.all()
    return render(request, "chores/profile_switcher.html", {"profiles": profiles})


def select_profile(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    request.session["profile_id"] = profile.id
    return redirect("home")


def home(request):
    profile_id = request.session.get("profile_id")
    if not profile_id:
        return redirect("profile_switcher")
    profile = get_object_or_404(Profile, id=profile_id)
    return render(request, "chores/home.html", {"profile": profile})


def switch_profile(request):
    request.session.pop("profile_id", None)
    return redirect("profile_switcher")
