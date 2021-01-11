from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile',
                                on_delete=models.CASCADE)

    # Personal info
    birth_date = models.DateField(null=True)
    phone_number = models.CharField(max_length=32, null=True)

    # Academic info
    university = models.CharField(max_length=256)