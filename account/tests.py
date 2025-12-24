# myapp/tests/test_models.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import unidecode
from datetime import datetime, timedelta, time
from django.utils import timezone
from .models import Category, Service, Worker, Customer, Appointment, EmployeeAvailability

User = get_user_model()

def slugify_tr(value):
    value = unidecode.unidecode(value)
    return slugify(value)

class CustomUserTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email="user@test.com",
            password="password123",
            first_name="John",
            last_name="Doe"
        )
        self.assertEqual(user.email, "user@test.com")
        self.assertTrue(user.is_customer)
        self.assertFalse(user.is_admin)
        self.assertEqual(user.get_role(), "customer")

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email="admin@test.com",
            password="admin123"
        )
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_admin)
        self.assertEqual(superuser.get_role(), "admin")

class CategoryServiceTest(TestCase):
    def test_category_slug_auto_generated(self):
        cat = Category.objects.create(name="Web Tasarım")
        self.assertEqual(cat.slug, "web-tasarm")

    def test_service_str(self):
        cat = Category.objects.create(name="Grafik Tasarım")
        service = Service.objects.create(
            category=cat,
            name="Logo Tasarımı",
            description="Logo tasarımı hizmeti",
            price=100
        )
        self.assertEqual(str(service), "Grafik Tasarım - Logo Tasarımı")

class AppointmentTest(TestCase):
    
    def setUp(self):
        self.user_worker = User.objects.create_user(email="worker@test.com", password="pass")
        self.worker = Worker.objects.create(user=self.user_worker)
        self.user_customer = User.objects.create_user(email="customer@test.com", password="pass")
        self.customer = Customer.objects.create(user=self.user_customer)
        self.category = Category.objects.create(name="Hizmet")
        self.service = Service.objects.create(category=self.category, name="Hizmet1", description="Deneme", price=100)
        # Çalışanın müsait olduğu zaman
        EmployeeAvailability.objects.create(
            worker_profile=self.worker,
            day_of_week=0,  # Pazartesi
            start_time=time(9,0),
            end_time=time(17,0)
        )

    def test_appointment_time_validation(self):
        today = timezone.now()
        next_monday = today + timedelta(days=(0 - today.weekday()) % 7)
        start = next_monday.replace(hour=10, minute=0, second=0, microsecond=0)
        end = next_monday.replace(hour=12, minute=0, second=0, microsecond=0)
        appointment = Appointment(
            customer=self.customer,
            worker=self.worker,
            service=self.service,
            start_time=start,
            end_time=end
        )
        try:
            appointment.clean()
        except ValidationError:
            self.fail("Valid appointment raised ValidationError unexpectedly!")

    def test_appointment_outside_availability(self):
        today = timezone.now()
        next_monday = today + timedelta(days=(0 - today.weekday()) % 7)
        start = next_monday.replace(hour=20, minute=0, second=0, microsecond=0)
        end = next_monday.replace(hour=21, minute=0, second=0, microsecond=0)
        appointment = Appointment(
            customer=self.customer,
            worker=self.worker,
            service=self.service,
            start_time=start,
            end_time=end
        )
        with self.assertRaises(ValidationError) as context:
            appointment.clean()
        self.assertIn("Çalışan bu zaman diliminde müsait değil.", str(context.exception))
