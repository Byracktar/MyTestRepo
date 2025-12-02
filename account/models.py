from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
import datetime

# -----------------------------
# Custom User Manager
# -----------------------------
class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Kullanıcı bir e-posta adresi belirtmelidir.'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        # Proje rolleri
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_customer', False)
        extra_fields.setdefault('is_employee', False)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Süper kullanıcı is_staff=True olmalıdır.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Süper kullanıcı is_superuser=True olmalıdır.'))

        return self.create_user(email, password, **extra_fields)

# -----------------------------
# Custom User
# -----------------------------
class CustomUser(AbstractUser):
    
    username = None
    email = models.EmailField(_('email adresi'), unique=True)

    # Roller
    is_customer = models.BooleanField(default=True, verbose_name="Müşteri Rolü")
    is_employee = models.BooleanField(default=False, verbose_name="Çalışan Rolü")
    is_admin = models.BooleanField(default=False, verbose_name="Yönetici Rolü")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def get_role(self):
        if self.is_admin:
            return "Yönetici"
        if self.is_employee:
            return "Çalışan"
        return "Müşteri"

# -----------------------------
# Kategori / Service / WorkSample
# -----------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Kategori Adı")
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name="Üst Kategori")
    description_tr = models.TextField(blank=True, verbose_name="Açıklama (Türkçe)")
    description_de = models.TextField(blank=True, verbose_name="Açıklama (Almanca)")
    image = models.ImageField(upload_to='category_images/', blank=True, null=True, verbose_name="Kategori Görseli")

    class Meta:
        verbose_name = "Hizmet Kategorisi"
        verbose_name_plural = "Hizmet Kategorileri"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Service(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='services', verbose_name="Kategori")
    name = models.CharField(max_length=100, verbose_name="Hizmet Adı")
    description = models.TextField(verbose_name="Hizmet Detayları")
    price_info = models.CharField(max_length=255, blank=True, verbose_name="Fiyat Bilgisi/Aralığı")
    duration_minutes = models.IntegerField(default=60, verbose_name="Ortalama Süre (dk)")

    class Meta:
        verbose_name = "Hizmet Detayı"
        verbose_name_plural = "Hizmet Detayları"

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class WorkSample(models.Model):
    worker_profile = models.ForeignKey('Worker', on_delete=models.CASCADE, related_name='gallery', verbose_name="Çalışan Profili")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name='service_samples', verbose_name="İlgili Hizmet")
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='work_samples/')

    class Meta:
        verbose_name = "Yapılan İş Örneği"
        verbose_name_plural = "Yapılan İş Örnekleri"

# -----------------------------
# Worker / Customer Profilleri
# -----------------------------
class Worker(models.Model):
    # settings.AUTH_USER_MODEL kullanımı kesinlikle önerilir
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='worker_profile')
    experience_years = models.IntegerField(default=0)
    bio = models.TextField(blank=True)
    # Worker hangi kategorilerde çalışıyor? ManyToMany ekledim.
    categories = models.ManyToManyField(Category, blank=True, related_name='workers')

    def __str__(self):
        return f"Çalışan Profili: {self.user.email}"

class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        
    )
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Müşteri Profili: {self.user.email}"

# -----------------------------
# Employee Availability
# -----------------------------
class EmployeeAvailability(models.Model):
    DAY_CHOICES = [
        (0, 'Pazartesi'), (1, 'Salı'), (2, 'Çarşamba'), (3, 'Perşembe'),
        (4, 'Cuma'), (5, 'Cumartesi'), (6, 'Pazar')
    ]

    worker_profile = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='availabilities', verbose_name="Çalışan")
    day_of_week = models.IntegerField(choices=DAY_CHOICES, verbose_name="Haftanın Günü")
    start_time = models.TimeField(verbose_name="Başlangıç Saati")
    end_time = models.TimeField(verbose_name="Bitiş Saati")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Çalışan Müsaitliği"
        verbose_name_plural = "Çalışan Müsaitlikleri"
        unique_together = ('worker_profile', 'day_of_week', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.worker_profile.user.email} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Başlangıç saati bitiş saatinden önce olmalıdır.")

# -----------------------------
# Appointment (Randevu)
# -----------------------------
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Beklemede'),
        ('APPROVED', 'Onaylandı'),
        ('REJECTED', 'Reddedildi'),
        ('COMPLETED', 'Tamamlandı'),
        ('CANCELED', 'İptal Edildi'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='booked_appointments', verbose_name="Müşteri")
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='received_appointments', verbose_name="Çalışan")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='appointments', verbose_name="Hizmet")
    start_time = models.DateTimeField(verbose_name="Başlangıç Tarih/Saat")
    end_time = models.DateTimeField(verbose_name="Bitiş Tarih/Saat")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="Randevu Durumu")
    request_details = models.TextField(blank=True, verbose_name="Müşteri Notu")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Randevu"
        verbose_name_plural = "Randevular"
        ordering = ['start_time']

    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.service.name} ({self.get_status_display()})"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Başlangıç zamanı bitiş zamanından önce olmalıdır.")

        # Çakışma kontrolü (aynı çalışan için ONAYLI/PENDING randevu çakışmasını engelle)
        overlapping = Appointment.objects.filter(
            worker=self.worker,
            status__in=['PENDING', 'APPROVED']
        ).exclude(pk=self.pk).filter(
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exists()
        if overlapping:
            raise ValidationError("Bu zaman diliminde çalışanın başka bir randevusu bulunmaktadır.")

        # Çalışanın o gün ve saatte müsait olup olmadığını kontrol et
        # Haftanın günü ve saat kontrolü
        day = self.start_time.weekday()
        availabilities = EmployeeAvailability.objects.filter(
            worker_profile=self.worker,
            day_of_week=day,
            is_active=True
        )
        # start/end time saat değerlerini alın
        start_t = self.start_time.time()
        end_t = self.end_time.time()
        ok = False
        for a in availabilities:
            if a.start_time <= start_t and a.end_time >= end_t:
                ok = True
                break
        if not ok:
            raise ValidationError("Çalışan bu zaman diliminde müsait değil.")

class LegalText(models.Model):
    TYPE_CHOICES = [
        ('KVKK', 'KVKK / DSGVO'),
        ('PRIVACY', 'Gizlilik Politikası'),
        ('TERMS', 'Kullanıcı Sözleşmesi'),
        ('COOKIE', 'Çerez Politikası'),
    ]

    type = models.CharField(max_length=10, choices=TYPE_CHOICES, unique=True)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    require_consent = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_type_display()