from django.contrib.auth.models import User
from django.views.generic import DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from feed.models import Post
from followers.models import Follower
from profiles.models import Profile


class ProfileDetailView(DetailView):
    # Specify allowed HTTP methods (this view will only respond to GET requests)
    http_method_names = ["get"]

    # Define the template to be used for rendering the page
    template_name = "profiles/detail.html"

    # Specify the model associated with this view (User model in this case)
    model = User

    # Name to be used for the object in the template context (instead of the default 'object')
    context_object_name = "user"

    # Define the field in the model to be used as the 'slug' for filtering the user
    slug_field = "username"

    # Specify the name of the URL parameter that will be used to get the 'slug' value (username)
    slug_url_kwarg = "username"

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user = self.get_object()    # self refers to the user we entered to - i.e. in url /profile/self.username/"
        # Call the parent class's method to get the default context
        context = super().get_context_data(**kwargs)

        # Add additional data to the context: the total number of posts authored by the user
        context['total_post'] = Post.objects.filter(author=user).count()
        context['total_followers'] = Follower.objects.filter(following=user).count()

        # Retrieve the profile of the user being viewed
        profile = Profile.objects.filter(user=user).first()
        if profile:
            full_name = f"{profile.first_name} {profile.last_name}"
        else:
            full_name = "No Name Available"
        context['full_name'] = full_name

        # Return the updated context dictionary with the new data (user and total_post)
        if self.request.user.is_authenticated:
            context['you_follow'] = Follower.objects.filter(following=user, followed_by=self.request.user).exists()
        return context


class FollowView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        data = request.POST.dict()

        if "action" not in data or "username" not in data:
            return HttpResponseBadRequest("Missing data")

        try:
            other_user = User.objects.get(username=data['username'])
        except User.DoesNotExist:
            return HttpResponseBadRequest("Missing user")

        if data['action'] == "follow":
            # Follow
            follower, created = Follower.objects.get_or_create(
                followed_by=request.user,
                following=other_user
            )
        else:
            # Unfollow
            try:
                follower = Follower.objects.get(
                    followed_by=request.user,
                    following=other_user,
                )
            except Follower.DoesNotExist:
                follower = None

            if follower:
                follower.delete()

        return JsonResponse({
            'success': True,
            'wording': "Unfollow" if data['action'] == "follow" else "Follow"
        })
