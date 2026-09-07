from django.urls import path

from . import views

urlpatterns = [
    path("", views.profile_switcher, name="profile_switcher"),
    path("select-profile/<int:profile_id>/", views.select_profile, name="select_profile"),
    path("home/", views.home, name="home"),
    path("switch-profile/", views.switch_profile, name="switch_profile"),
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/new/", views.create_task, name="create_task"),
    path("tasks/<int:task_id>/claim/", views.claim_task, name="claim_task"),
    path("tasks/<int:task_id>/done/", views.mark_done, name="mark_done"),
    path("tasks/pending-approvals/", views.pending_approvals, name="pending_approvals"),
    path("tasks/<int:task_id>/approve/", views.approve_task, name="approve_task"),
    path("tasks/<int:task_id>/reject/", views.reject_task, name="reject_task"),
]
