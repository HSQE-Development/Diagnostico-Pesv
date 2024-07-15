from django.urls import path
from .views import uploadDiagnosisQuestions, findQuestionsByCompanySize

urlpatterns = [
    path(
        "uploadDiagnosisQuestions",
        uploadDiagnosisQuestions,
        name="uploadDiagnosisQuestions",
    ),
    path(
        "findQuestionsByCompanySize",
        findQuestionsByCompanySize,
        name="findQuestionsByCompanySize",
    ),
]
