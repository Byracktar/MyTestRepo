# myapp/tests/test_api_endpoints.py
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from datetime import time
from .models import Category, Service, Worker, Customer, EmployeeAvailability, Appointment
from datetime import datetime, timedelta

User = get_user_model()


class AppointmentIntegrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Users
        self.admin = User.objects.create_superuser(email="admin@test.com", password="admin123")
        self.worker_user = User.objects.create_user(email="worker@test.com", password="pass")
        self.customer_user = User.objects.create_user(email="customer@test.com", password="pass")

        # Profiles
        self.worker = Worker.objects.create(user=self.worker_user)
        self.customer = Customer.objects.create(user=self.customer_user)

        # Category & Service
        self.category = Category.objects.create(name="Web Tasarım")
        self.service = Service.objects.create(category=self.category, name="Logo Tasarımı", description="Deneme", price=100)

        # Worker Availability (Pazartesi)
        EmployeeAvailability.objects.create(worker_profile=self.worker, day_of_week=0, start_time=time(9,0), end_time=time(17,0))

    def test_customer_creates_and_worker_approves_appointment(self):
        # 1️⃣ Customer login ve appointment oluşturma
        self.client.force_authenticate(user=self.customer_user)

        # next Monday
        today = datetime.utcnow()
        next_monday = today + timedelta(days=(0 - today.weekday()) % 7)
        start_time = next_monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat() + "Z"
        end_time = next_monday.replace(hour=12, minute=0, second=0, microsecond=0).isoformat() + "Z"

        response = self.client.post("/api/appointments/", {
            "worker": self.worker.id,
            "service": self.service.id,
            "start_time": start_time,
            "end_time": end_time
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        appointment_id = response.data['id']

        # 2️⃣ Worker login ve appointment approve
        self.client.force_authenticate(user=self.worker_user)
        response = self.client.post(f"/api/appointments/{appointment_id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], "APPROVED")

        # 3️⃣ Admin login ve tüm appointmentları görme
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/appointments/all-with-profiles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(a['id'] == appointment_id for a in response.data))
class APITestEndpoints(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Users
        self.admin = User.objects.create_superuser(email="admin@test.com", password="admin123")
        self.worker_user = User.objects.create_user(email="worker@test.com", password="pass")
        self.customer_user = User.objects.create_user(email="customer@test.com", password="pass")

        # Profiles
        self.worker = Worker.objects.create(user=self.worker_user)
        self.customer = Customer.objects.create(user=self.customer_user)

        # Category & Service
        self.category = Category.objects.create(name="Web Tasarım")
        self.service = Service.objects.create(category=self.category, name="Logo Tasarımı", description="Deneme", price=100)

        # Worker Availability
        EmployeeAvailability.objects.create(worker_profile=self.worker, day_of_week=0, start_time=time(9,0), end_time=time(17,0))

    def test_category_list_and_create(self):
        # List as anonymous
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Create as admin
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/categories/", {"name": "Grafik Tasarım"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Grafik Tasarım")

        # Create as regular user -> forbidden
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post("/api/categories/", {"name": "Test"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_service_work_samples_action(self):
        self.client.force_authenticate(user=self.customer_user)
        url = f"/api/services/{self.service.id}/work-samples/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_appointment_crud_and_approve_reject(self):
        # Customer creates appointment
        self.client.force_authenticate(user=self.customer_user)
        today = datetime.utcnow()
        next_monday = today + timedelta(days=(0 - today.weekday()) % 7)
        start_time = next_monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat() + "Z"
        end_time = next_monday.replace(hour=12, minute=0, second=0, microsecond=0).isoformat() + "Z"

        response = self.client.post("/api/appointments/", {
            "worker": self.worker.id,
            "service": self.service.id,
            "start_time": start_time,
            "end_time": end_time
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        appointment_id = response.data['id']

        # Worker approves appointment
        self.client.force_authenticate(user=self.worker_user)
        url = f"/api/appointments/{appointment_id}/approve/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], "APPROVED")

        # Worker rejects already approved -> 400
        response = self.client.post(f"/api/appointments/{appointment_id}/reject/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_employee_availability_bulk_update(self):
        self.client.force_authenticate(user=self.worker_user)
        self.worker_user.is_employee = True
        self.worker_user.save()

        data = [
            {"start_time": "09:00:00", "end_time": "12:00:00", "day_of_week": 0},
            {"start_time": "13:00:00", "end_time": "17:00:00", "day_of_week": 0}
        ]
        response = self.client.put("/api/availabilities/bulk-update/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['updated']), 2)

