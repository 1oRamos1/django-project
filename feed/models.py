from django.db import models
from django.contrib.auth.models import User

# databases for views requests


class Post(models.Model):  # post request
    text = models.CharField(max_length=240)   # add text using models app
    date = models.DateTimeField(auto_now=True)  # show date
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    def __str__(self):            # the post name it`s his data
        return self.text[0:100]
