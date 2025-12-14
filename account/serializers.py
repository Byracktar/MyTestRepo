from rest_framework import serializers
from .models import (
    CustomUser, Customer, Worker, Category, Service, Appointment,
    EmployeeAvailability, WorkSample, LegalText
)
from django.utils import timezone
class CustomUserMeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'email', 'role']

    def get_role(self, obj):
        return obj.get_role()
class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "description_tr",
            "description_de",
            "image",
            "icon",
            "children",
        ]
    def get_children(self, obj):
        qs = obj.children.all()
        return CategorySerializer(qs, many=True, context=self.context).data

class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "category",
            "category_name",
            "description",
            "price_info",
            "duration_minutes",
            "rating",
            "image",
            "price",
        ]

class WorkerSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    class Meta:
        model = Worker
        fields = ('id','user','user_email','experience_years','bio','categories')

class CustomerSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = Customer
        fields = ('id','user','user_email','phone_number','address')
class WorkerMeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    role = serializers.SerializerMethodField()

    name = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()
    working_hours = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    completed_jobs = serializers.SerializerMethodField()
    appointments = serializers.SerializerMethodField()  # 👈 NEW

    class Meta:
        model = Worker
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "role",
            "experience_years",
            "bio",
            "phone",
            "status",
            "apply_date",
            "name",
            "category",
            "region",
            "working_hours",
            "rating",
            "completed_jobs",
            "appointments",   # 👈 include
        ]

    # =========================
    # BASIC FIELDS
    # =========================

    def get_role(self, obj):
        return obj.user.get_role()

    def get_completed_jobs(self, obj):
        return obj.gallery.count()

    def get_name(self, obj):
        first_name = obj.user.first_name or ""
        return f"Usta {first_name.capitalize()}".strip()

    def get_category(self, obj):
        return str(obj.category) if obj.category else "Tesisatçı"

    def get_region(self, obj):
        return "Berlin"

    def get_working_hours(self, obj):
        return "09:00 - 18:00"

    def get_rating(self, obj):
        return 4.5
    def get_appointments(self, obj):
        from .models import Appointment
        qs = Appointment.objects.filter(worker=obj).order_by("-start_time")
        return AppointmentSerializer(qs, many=True, context=self.context).data


class EmployeeAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAvailability
        fields = '__all__'
        read_only_fields = ('worker_profile',)

class AppointmentSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(read_only=True)
    worker = serializers.PrimaryKeyRelatedField(queryset=Worker.objects.all())
    service_name = serializers.CharField(source='service.name', read_only=True)
    customer_email = serializers.EmailField(source='customer.user.email', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ('status','created_at','customer')

    def validate(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        worker = data.get('worker')

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("Başlangıç zamanı bitiş zamanından önce olmalıdır.")

        # çakışma kontrolü (aynı logic model.clean() ile paralel)
        qs = Appointment.objects.filter(worker=worker, status__in=['PENDING','APPROVED'])
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.filter(start_time__lt=end_time, end_time__gt=start_time).exists():
            raise serializers.ValidationError("Bu zaman diliminde çalışanın başka bir randevusu bulunmaktadır.")

        # çalışan availability kontrolü
        day = start_time.weekday()
        from .models import EmployeeAvailability
        availabilities = EmployeeAvailability.objects.filter(worker_profile=worker, day_of_week=day, is_active=True)
        ok = False
        for a in availabilities:
            if a.start_time <= start_time.time() and a.end_time >= end_time.time():
                ok = True
                break
        if not ok:
            raise serializers.ValidationError("Çalışan bu zaman diliminde müsait değil.")
        return data

    def create(self, validated_data):
        # customer'ı request.user.customer_profile olarak otomatik ata
        request = self.context.get('request')
        if request and hasattr(request.user, 'customer_profile'):
            validated_data['customer'] = request.user.customer_profile
        return super().create(validated_data)
    

class WorkSampleSerializer(serializers.ModelSerializer):
    worker_email = serializers.EmailField(source='worker_profile.user.email', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = WorkSample
        fields = ('id', 'worker_profile', 'worker_email', 'service', 'service_name', 'title', 'image')
        read_only_fields = ('worker_profile',) # Çalışan profilini otomatik atayacağız.

class LegalTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalText
        fields = '__all__'
        read_only_fields = ('last_updated',)        