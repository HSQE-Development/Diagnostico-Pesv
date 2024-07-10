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
    findAllVehicleQuestions,
    findAllDriverQuestions,
    findFleetsByCompanyId,
    findDriversByCompanyId,
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
    path(
        "findAllVehicleQuestions/",
        findAllVehicleQuestions,
        name="findAllVehicleQuestions",
    ),
    path(
        "findAllDriverQuestions/", findAllDriverQuestions, name="findAllDriverQuestions"
    ),
    path(
        "findFleetsByCompanyId/<int:companyId>",
        findFleetsByCompanyId,
        name="findFleetsByCompanyId",
    ),
    path(
        "findDriversByCompanyId/<int:companyId>",
        findDriversByCompanyId,
        name="findDriversByCompanyId",
    ),
]
