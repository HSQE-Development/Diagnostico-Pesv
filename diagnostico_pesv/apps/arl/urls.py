from .views import *
from django.urls import path


urlpatterns = [
    path("", findAll, name="findAll"),
    path("<int:id>", findById, name="findById"),
    path("update", update, name="update"),
    path("delete/<int:id>", delete, name="delete"),
    path("save", save, name="save"),
]
