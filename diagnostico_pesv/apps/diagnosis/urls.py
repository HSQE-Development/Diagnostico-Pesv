from django.urls import path
from .views import (
    uploadDiagnosisQuestions,
    findQuestionsByCompanySize,
    saveDiagnosis,
    generateReport,
)

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
    path(
        "saveDiagnosis",
        saveDiagnosis,
        name="saveDiagnosis",
    ),
    path(
        "generateReport",
        generateReport,
        name="generateReport",
    ),
]
