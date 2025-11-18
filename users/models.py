from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Extend the default Django user model to include additional fields.
    """
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    # You can add more fields like profile picture if needed
    profile_image = models.ImageField(upload_to='users/', blank=True, null=True)

    def __str__(self):
        return self.username
