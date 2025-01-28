from django.urls import path
from . import views
from profiles import views as profile_views

app_name = "feed"

urlpatterns = [
    path("", views.HomePage.as_view(), name="index"),  # turns the class into a view function that can be used in the URLconf
    path("<int:pk>/", views.PostDetailView.as_view(), name="detail"),
    path("new/", views.CreateNewPost.as_view(), name="new_post"),
    path("edit-profile/", views.EditProfileView.as_view(), name="edit_profile"),
]
