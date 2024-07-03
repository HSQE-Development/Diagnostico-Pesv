from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    """
    Modelo de roles de usuario
    """
    name = models.CharField(max_length=200, blank=False, unique=True) 
    permissions = models.ManyToManyField('auth.Permission', blank=True)
    def __str__(self):
        return self.name

# Create your models here.
class User(AbstractUser):
    """
    Clase donde traemos el modelo ABstracto del usuario que proporciona djnago por defecto
    """
    role = models.ForeignKey(Role, related_name='users_role')