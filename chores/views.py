from django.shortcuts import get_object_or_404, redirect, render

from .forms import TaskForm
from .models import Profile, Task


def get_current_profile(request):
    profile_id = request.session.get("profile_id")
    if not profile_id:
        return None
    return Profile.objects.filter(id=profile_id).first()


def profile_switcher(request):
    profiles = Profile.objects.all()
    return render(request, "chores/profile_switcher.html", {"profiles": profiles})


def select_profile(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    request.session["profile_id"] = profile.id
    return redirect("home")


def home(request):
    profile = get_current_profile(request)
    if not profile:
        return redirect("profile_switcher")
    return render(request, "chores/home.html", {"profile": profile})


def switch_profile(request):
    request.session.pop("profile_id", None)
    return redirect("profile_switcher")


def create_task(request):
    profile = get_current_profile(request)
    if not profile:
        return redirect("profile_switcher")
    if not profile.is_adult:
        return redirect("task_list")

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = profile
            if task.assignment_mode == Task.AssignmentMode.POOL:
                task.assigned_to = None
            task.save()
            return redirect("task_list")
    else:
        form = TaskForm()

    return render(request, "chores/create_task.html", {"form": form, "profile": profile})


def task_list(request):
    profile = get_current_profile(request)
    if not profile:
        return redirect("profile_switcher")

    if profile.is_adult:
        tasks = Task.objects.all()
        return render(request, "chores/task_list_adult.html", {"profile": profile, "tasks": tasks})

    my_tasks = Task.objects.filter(assigned_to=profile, status=Task.Status.TODO)
    pool_tasks = Task.objects.filter(
        assignment_mode=Task.AssignmentMode.POOL,
        assigned_to__isnull=True,
        status=Task.Status.TODO,
    )
    return render(
        request,
        "chores/task_list_child.html",
        {"profile": profile, "my_tasks": my_tasks, "pool_tasks": pool_tasks},
    )


def claim_task(request, task_id):
    profile = get_current_profile(request)
    if not profile or not profile.is_child:
        return redirect("home")

    task = get_object_or_404(
        Task,
        id=task_id,
        assignment_mode=Task.AssignmentMode.POOL,
        assigned_to__isnull=True,
    )
    task.assigned_to = profile
    task.save()
    return redirect("task_list")
