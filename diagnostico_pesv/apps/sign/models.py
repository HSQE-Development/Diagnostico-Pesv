from django.db import models
from django.contrib.auth.models import AbstractUser
from timestamps.models import SoftDeletes, Timestampable
from django.contrib.auth.models import Group


# Create your models here.
class User(AbstractUser):
    licensia_sst = models.CharField(
        max_length=250, blank=False, null=True, default=None
    )
    cedula = models.CharField(max_length=10, blank=True, null=None, unique=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    change_password = models.BooleanField(default=False, null=False, blank=False)
    external_step = models.IntegerField(default=0)


class QueryLog(SoftDeletes, Timestampable):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    action = models.CharField(max_length=255)
    query_params = models.JSONField(null=True, default=None)
    http_method = models.CharField(max_length=10, null=True, default=None)
    user_agent = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"QueryLog by {self.user}"


class Menu(SoftDeletes, Timestampable):
    label = models.CharField(max_length=250)
    icon = models.CharField(max_length=250)
    path = models.CharField(max_length=250)
    groups = models.ManyToManyField(Group, related_name="menus")
