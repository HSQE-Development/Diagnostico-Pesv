from django.test import TestCase
from rest_framework.test import APIClient
from .models import Company, Segments
from apps.sign.models import User
from rest_framework import status
from django.urls import reverse


# Create your tests here.
class CompanyTests(TestCase):
    def setUp(self):
        # Configurar cliente API y autenticación
        self.client = APIClient()
        
        # Crear un usuario para las pruebas
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        
        # Crear un token JWT para el usuario de prueba
        self.client.force_authenticate(user=self.user)
        
        # Crear segmentos de prueba
        self.segment = Segments.objects.create(name="Test Segment")
        
        # Crear una compañía de prueba
        self.company = Company.objects.create(
            name="Test Company",
            nit="123456",
            size=1,
            segment=self.segment,
            dependant="John Doe",
            dependant_phone="123456789",
            activities_ciiu="1234",
            email="test@company.com",
            acquired_certification=True,
            diagnosis="Test Diagnosis"
        )
        
    def test_find_all_companies(self):
        url = reverse('findAll')  # Asegúrate de que la URL 'findAll' esté configurada en tus urls.py
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Verifica que hay una compañía en la respuesta

    def test_find_company_by_id(self):
        url = reverse('findById', args=[self.company.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.company.name)

    def test_update_company(self):
        url = reverse('update')
        data = {
            "id": self.company.id,
            "name": "Updated Company"
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.company.refresh_from_db()
        self.assertEqual(self.company.name, "Updated Company")

    def test_delete_company(self):
        url = reverse('delete', args=[self.company.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.company.refresh_from_db()
        self.assertIsNotNone(self.company.deleted_at)  # Asumiendo que tienes un campo deleted_at para soft deletes