from django.shortcuts import render
from django.contrib.auth import login
from django.urls import reverse
from django.views.generic import TemplateView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Post
from followers.models import Follower
from profiles.models import Profile
from django.contrib.auth.hashers import make_password
from itertools import chain


class HomePage(TemplateView):
    http_method_names = ["get"]  # we use "get" method when enters homepage
    template_name = "feed/homepage.html"  # this is the html file that shows up

    # Override the dispatch method to set the request as an instance attribute
    # This ensures `self.request` is available in other methods
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.is_authenticated:
            posts = Post.objects.filter(author=self.request.user).order_by('-id')[:30]
            following = list(Follower.objects.filter(followed_by=self.request.user).values_list('following', flat=True))
            if following:
                following_posts = Post.objects.filter(author__in=following).order_by('-id')[:30]
                posts = list(chain(following_posts, posts))
            posts = sorted(posts, key=lambda x: x.date, reverse=True)
        else:
            posts = Post.objects.all().order_by('-id')[:30]
        context['posts'] = posts
        return context


class PostDetailView(DetailView):
    http_method_names = ["get"]
    template_name = "feed/detail.html"
    model = Post
    context_object_name = "post"


class CreateNewPost(LoginRequiredMixin, CreateView):
    template_name = "feed/create.html"
    model = Post
    # Fields in the form that users can fill out to create a post
    fields = ['text']
    success_url = "/"
    # Override the dispatch method to set the request as an instance attribute
    # This ensures `self.request` is available in other methods
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super().dispatch(request, *args, **kwargs)

    # Override the form_valid method to add additional logic when the form is valid
    def form_valid(self, form):
        # Save the form without committing to the database yet
        obj = form.save(commit=False)
        # Assign the currently logged-in user as the author of the post
        obj.author = self.request.user
        # Save the object to the database
        obj.save()
        # Call the parent class's form_valid method, which will handle redirection
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):

        post = Post.objects.create(
            text=request.POST.get("text"),
            author=request.user,
        )

        return render(
            request,
            "includes/post.html",
            {
                "post": post,
                "show_detail_link": True,
            },
            content_type="application/html"
        )


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = Profile  # The model to update
    template_name = "feed/edit.html"  # Template for the edit form
    context_object_name = "profile"
    fields = ["first_name", "last_name", "image"]  # Fields to edit

    def get_object(self, queryset=None):
        # Return the current user's profile object
        return self.request.user.profile

    def form_valid(self, form):
        # Save the form, handling the password separately if provided
        profile = form.instance  # Access the Profile object
        user = profile.user  # Access the related User object

        # Update the username
        new_username = self.request.POST.get("username")
        if new_username:
            user.username = new_username

        # Update the password if provided
        password = self.request.POST.get("password")
        if password:
            user.password = make_password(password)  # Hash and set the new password

        # Save the User and Profile objects
        user.save()
        profile.save()

        # Log the user back in after updating the profile (if password was changed)
        # Specify the backend to avoid the ValueError
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')

        return super().form_valid(form)

    def get_success_url(self):
        # Redirect to the user's profile after successful update
        return reverse("profiles:detail", kwargs={"username": self.request.user.username})