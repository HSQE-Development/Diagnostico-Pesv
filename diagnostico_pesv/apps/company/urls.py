from django.urls import path
from .views import (
    findAll,
    findById,
    update,
    delete,
    save,
    findAllSegments,
    findAllDedications,
    findcompanySizeByDedicactionId,
)

urlpatterns = [
    path("", findAll, name="findAll"),
    path("<int:id>", findById, name="findById"),
    path("update", update, name="update"),
    path("delete/<int:id>", delete, name="delete"),
    path("save/", save, name="save"),
    path("segments/", findAllSegments, name="findAllSegments"),
    path("findAllDedications/", findAllDedications, name="findAllDedications"),
    path(
        "findcompanySizeByDedicactionId/<int:id>",
        findcompanySizeByDedicactionId,
        name="findcompanySizeByDedicactionId",
    ),
]
