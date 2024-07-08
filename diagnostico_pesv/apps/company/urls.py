from django.urls import path
from .views import findAll, findById, update, delete

urlpatterns = [
    path('', findAll, name='findAll'),
    path('<int:id>', findById, name='findById'),
    path('update', update, name='update'),
    path('delete/<int:id>', delete, name='delete'),
]