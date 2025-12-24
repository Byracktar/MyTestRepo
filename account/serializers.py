from rest_framework import serializers
from .models import (
    CustomUser, Customer, Worker, Category, Service, Appointment,
    EmployeeAvailability, WorkSample, LegalText
)
from django.utils import timezone
# serializers.py
class CustomUserMeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    phone_number = serializers.CharField(
        source='customer_profile.phone_number', required=False, allow_blank=True
    )
    register_date = serializers.DateTimeField(source='created_at', read_only=True)
    appointments_count = serializers.SerializerMethodField()  # 👈 added

    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'email', 'role', 'phone_number', 'register_date', 'appointments_count']

    def get_role(self, obj):
        return obj.get_role()

    def get_appointments_count(self, obj):
        # obj is a CustomUser instance
        if hasattr(obj, 'customer_profile'):
            return obj.customer_profile.booked_appointments.count()
        elif hasattr(obj, 'worker_profile'):
            return obj.worker_profile.received_appointments.count()
        return 0

    def update(self, instance, validated_data):
        phone_data = validated_data.pop('customer_profile', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if phone_data and hasattr(instance, 'customer_profile'):
            instance.customer_profile.phone_number = phone_data.get(
                'phone_number', instance.customer_profile.phone_number
            )
            instance.customer_profile.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()
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
            "price",
            "service",      # 👈 added
            "children",
        ]

    def get_children(self, obj):
        qs = obj.children.all()
        return CategorySerializer(
            qs,
            many=True,
            context=self.context
        ).data

    def get_service(self, obj):
        """
        Return linked service if exists, otherwise None
        """
        try:
            service = obj.services.get()  # related_name='services'
        except Service.DoesNotExist:
            return None

        return ServiceSerializer(service, context=self.context).data

class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_icon = serializers.CharField(source="category.icon", read_only=True)
    root = serializers.SerializerMethodField()  # 👈 new field

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "category",
            "category_name",
            "category_icon",
            "root",  # 👈 include root
            "description",
            "price_info",
            "duration_minutes",
            "rating",
            "image",
            "price",
        ]

    def get_root(self, obj):
        category = obj.category
        if not category:
            return None
        # climb up to the top-most parent
        while category.parent:
            category = category.parent
        return {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "icon": category.icon,
        }

# serializers.py

class WorkerIdSerializer(serializers.Serializer):
    id = serializers.IntegerField()

class WorkerSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)  # 👈 use serializer instead of ID
    apply_date = serializers.DateTimeField(format="%Y-%m-%d", read_only=True)
    appointments_count = serializers.SerializerMethodField()  # 👈 counts by status

    class Meta:
        model = Worker
        fields = (
            'id',
            'user',
            'user_email',
            'experience_years',
            'bio',
            'categories',
            'status',
            'apply_date',
            "phone",
            "category",
            "appointments_count",  # 👈 include
        )

    def get_appointments_count(self, obj):
        qs = Appointment.objects.filter(worker=obj)
        return {
            "approved": qs.filter(status="APPROVED").count(),
            "rejected": qs.filter(status="REJECTED").count(),
            "pending": qs.filter(status="PENDING").count(),  # optional
        }

class WorkSampleWithWorkerSerializer(serializers.ModelSerializer):
    worker_profile = WorkerSerializer(read_only=True)

    class Meta:
        model = WorkSample
        fields = "__all__"
class CustomerSerializer(serializers.ModelSerializer):
    user = CustomUserMeSerializer(read_only=True)  # nested user object
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Customer
        fields = ('id', 'user', 'user_email', 'phone_number', 'address')

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
    worker = serializers.PrimaryKeyRelatedField(
        queryset=Worker.objects.all(), write_only=True
    )

    worker_profile = WorkerSerializer(source="worker", read_only=True)

    service_name = serializers.CharField(source='service.name', read_only=True)
    customer_email = serializers.EmailField(source='customer.user.email', read_only=True)
    customer_phone_number = serializers.CharField(source='customer.phone_number', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "start_time",
            "end_time",
            "status",
            "service",
            "service_name",
            "customer",
            "customer_email",
            "customer_phone_number",
            "worker",
            "worker_profile",   # 👈 added
            "created_at",
        ]
        read_only_fields = ("status", "created_at", "customer")


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
class BookedAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["id", "start_time", "end_time"]
from rest_framework import serializers
from .models import Appointment

class AppointmentWithProfilesSerializer(serializers.ModelSerializer):
    worker_profile = serializers.SerializerMethodField()
    user_profile = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id",
            "start_time",
            "end_time",
            "status",
            "worker_profile",
            "user_profile",
        ]

    def get_worker_profile(self, obj):
        if obj.worker is None:
            return None
        worker = obj.worker
        return {
            "id": worker.id,
            "email": getattr(worker.user, "email", None),
            "first_name": getattr(worker.user, "first_name", None),
            "last_name": getattr(worker.user, "last_name", None),
            "experience_years": worker.experience_years,
            "bio": worker.bio,
            "phone": worker.phone,
            "status": worker.status,
            "apply_date": worker.apply_date,
            "category": worker.category.name if worker.category else None,
        }

    def get_user_profile(self, obj):
        if obj.customer is None:
            return None
        customer = obj.customer
        return {
            "id": customer.id,
            "email": getattr(customer.user, "email", None),
            "first_name": getattr(customer.user, "first_name", None),
            "last_name": getattr(customer.user, "last_name", None),
            "phone_number": customer.phone_number,
            "address": customer.address,
            
        }

class WorkerApplicationSerializer(serializers.ModelSerializer):
    # Required user info
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone = serializers.CharField(write_only=True)
    birth_date = serializers.DateField(write_only=True, input_formats=['%d.%m.%Y'], required=False)
    address = serializers.CharField(write_only=True, required=False)
    city = serializers.CharField(write_only=True)
    postal_code = serializers.CharField(write_only=True, required=False)

    # Worker-specific
    service_category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True
    )
    experience_duration = serializers.CharField(max_length=20, default="0")
    cv = serializers.FileField(write_only=True)
    id_document = serializers.FileField(write_only=True, required=False)

    # Agreement checkboxes
    accept_terms = serializers.BooleanField(write_only=True)
    accept_privacy = serializers.BooleanField(write_only=True)

    class Meta:
        model = Worker
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'birth_date', 'address', 'city', 'postal_code',
            'service_category', 'experience_duration', 'cv', 'id_document',
            'accept_terms', 'accept_privacy'
        ]

    def validate(self, data):
        if not data.get('accept_terms'):
            raise ValidationError({'accept_terms': 'You must accept the terms.'})
        if not data.get('accept_privacy'):
            raise ValidationError({'accept_privacy': 'You must accept the privacy policy.'})

        cv = data.get('cv')
        if cv and cv.size > 5 * 1024 * 1024:
            raise ValidationError({'cv': 'CV file size must be 5MB or less.'})

        return data



    def create(self, validated_data):
        EXPERIENCE_MAP = {
            "0-1": 0,
            "1-3": 1,
            "3-5": 3,
            "5-10": 5,
            "10+": 10,
        }
        validated_data.pop('accept_terms', None)
        validated_data.pop('accept_privacy', None)

        if 'service_category' in validated_data:
            validated_data['category'] = validated_data.pop('service_category')

        if 'experience_duration' in validated_data:
            validated_data['experience_years'] = EXPERIENCE_MAP.get(validated_data.pop('experience_duration'), 0)

        # Set the user from context
        user = self.context['request'].user
        validated_data['user'] = user

        worker = Worker.objects.create(**validated_data)
        return worker
