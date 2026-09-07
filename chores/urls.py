from django.urls import path

from . import views

urlpatterns = [
    path("", views.profile_switcher, name="profile_switcher"),
    path("select-profile/<int:profile_id>/", views.select_profile, name="select_profile"),
    path("home/", views.home, name="home"),
    path("switch-profile/", views.switch_profile, name="switch_profile"),
]
