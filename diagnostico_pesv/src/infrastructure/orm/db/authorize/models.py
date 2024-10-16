from django.db import models
from django.contrib.auth.models import AbstractUser
from src.domain.user import UserEntity

# Create your models here.


class User(AbstractUser):
    licensia_sst = models.CharField(
        max_length=200, blank=False, null=True, default=None
    )
    cedula = models.CharField(max_length=10, blank=True, null=None, unique=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    class Meta:
        verbose_name = "sign"
        verbose_name_plural = "signs"
        ordering = ("id",)

    def __str__(self) -> str:
        return UserEntity.get_full_name(self)
