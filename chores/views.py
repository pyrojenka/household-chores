from datetime import date

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CompletionForm, RewardForm, TaskForm
from .models import Profile, Redemption, Reward, Task
from .recurrence import generate_recurring_tasks


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

    generate_recurring_tasks()

    if profile.is_adult:
        templates = Task.objects.filter(recurrence__in=["daily", "weekly"])
        tasks = Task.objects.filter(recurrence=Task.Recurrence.NONE)
        return render(
            request,
            "chores/task_list_adult.html",
            {"profile": profile, "tasks": tasks, "templates": templates},
        )

    due = Q(scheduled_date__isnull=True) | Q(scheduled_date__lte=date.today())
    my_tasks = Task.objects.filter(
        assigned_to=profile, status=Task.Status.TODO, recurrence=Task.Recurrence.NONE
    ).filter(due)
    pending_tasks = Task.objects.filter(assigned_to=profile, status=Task.Status.DONE)
    pool_tasks = Task.objects.filter(
        assignment_mode=Task.AssignmentMode.POOL,
        assigned_to__isnull=True,
        status=Task.Status.TODO,
        recurrence=Task.Recurrence.NONE,
    ).filter(due)
    return render(
        request,
        "chores/task_list_child.html",
        {"profile": profile, "my_tasks": my_tasks, "pending_tasks": pending_tasks, "pool_tasks": pool_tasks},
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


def mark_done(request, task_id):
    profile = get_current_profile(request)
    if not profile or not profile.is_child:
        return redirect("home")

    task = get_object_or_404(Task, id=task_id, assigned_to=profile, status=Task.Status.TODO)

    if request.method == "POST":
        form = CompletionForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            task.status = Task.Status.DONE
            task.completed_at = timezone.now()
            task.save()
            return redirect("task_list")
    else:
        form = CompletionForm(instance=task)

    return render(request, "chores/mark_done.html", {"form": form, "task": task, "profile": profile})


def pending_approvals(request):
    profile = get_current_profile(request)
    if not profile:
        return redirect("profile_switcher")
    if not profile.is_adult:
        return redirect("task_list")

    tasks = Task.objects.filter(status=Task.Status.DONE)
    return render(request, "chores/pending_approvals.html", {"profile": profile, "tasks": tasks})


def approve_task(request, task_id):
    profile = get_current_profile(request)
    if not profile or not profile.is_adult:
        return redirect("home")

    task = get_object_or_404(Task, id=task_id, status=Task.Status.DONE)
    task.status = Task.Status.APPROVED
    task.approved_by = profile
    task.approved_at = timezone.now()
    task.save()
    return redirect("pending_approvals")


def reject_task(request, task_id):
    profile = get_current_profile(request)
    if not profile or not profile.is_adult:
        return redirect("home")

    task = get_object_or_404(Task, id=task_id, status=Task.Status.DONE)
    task.status = Task.Status.TODO
    task.completed_at = None
    task.save()
    return redirect("pending_approvals")


def reward_catalog(request):
    profile = get_current_profile(request)
    if not profile:
        return redirect("profile_switcher")

    rewards = Reward.objects.all()

    if profile.is_adult:
        return render(request, "chores/reward_catalog_adult.html", {"profile": profile, "rewards": rewards})

    return render(
        request,
        "chores/reward_catalog_child.html",
        {"profile": profile, "rewards": rewards},
    )


def create_reward(request):
    profile = get_current_profile(request)
    if not profile:
        return redirect("profile_switcher")
    if not profile.is_adult:
        return redirect("reward_catalog")

    if request.method == "POST":
        form = RewardForm(request.POST)
        if form.is_valid():
            reward = form.save(commit=False)
            reward.created_by = profile
            reward.save()
            return redirect("reward_catalog")
    else:
        form = RewardForm()

    return render(request, "chores/create_reward.html", {"form": form, "profile": profile})


def redeem_reward(request, reward_id):
    profile = get_current_profile(request)
    if not profile or not profile.is_child:
        return redirect("home")

    reward = get_object_or_404(Reward, id=reward_id)
    if profile.points_balance >= reward.point_cost:
        Redemption.objects.create(
            profile=profile,
            reward=reward,
            reward_name=reward.name,
            points_spent=reward.point_cost,
        )
    return redirect("reward_catalog")


def redemption_history(request):
    profile = get_current_profile(request)
    if not profile:
        return redirect("profile_switcher")
    if not profile.is_adult:
        return redirect("home")

    redemptions = Redemption.objects.all()
    return render(request, "chores/redemption_history.html", {"profile": profile, "redemptions": redemptions})
