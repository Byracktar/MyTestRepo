from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework import viewsets, mixins, status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.utils.timezone import now
from rest_framework.response import Response
from drf_yasg import openapi
from .models import (
    Category, Service, Appointment, EmployeeAvailability, Customer, Worker , WorkSample, LegalText,
    
)
from .serializers import (
    CategorySerializer, ServiceSerializer, AppointmentSerializer, 
    EmployeeAvailabilitySerializer, CustomerSerializer, WorkerSerializer, 
    WorkSampleSerializer, LegalTextSerializer,CustomUserMeSerializer,WorkerMeSerializer,
    WorkSampleWithWorkerSerializer, BookedAppointmentSerializer,AppointmentWithProfilesSerializer,
    WorkerApplicationSerializer,WorkerIdSerializer
)
from .permissions import (
    IsAdminUser, IsEmployeeUser, IsSelfOrAdmin, 
    IsAppointmentOwnerOrWorker, ReadOnlyOrAdmin, IsCustomerUser
)
from rest_framework.decorators import action
from rest_framework.response import Response

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserMeSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = CustomUserMeSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def login_view(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Giriş başarılı.")
            return redirect('home')
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı.")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'account/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # otomatik giriş yapma
            messages.success(request, "Kayıt başarılı — sisteme giriş yapıldı.")
            return redirect('home')
        else:
            # form.errors template içinde gösterilecektir; ayrıca mesaj da ekleyebilirsin
            messages.error(request, "Kayıt sırasında hata var. Lütfen tekrar kontrol et.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'account/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Çıkış yapıldı.")
    return redirect('login')

@login_required(login_url='login')
def home_view(request):
    return render(request, "account/home.html")

# ==============================
# API ViewSets
# ==============================

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(parent__isnull=True) # Sadece ana kategorileri listeleyelim.
    serializer_class = CategorySerializer
    permission_classes = [ReadOnlyOrAdmin]

    @action(detail=True, methods=['get'])
    def all_services(self, request, pk=None):
        category = self.get_object()
        services = Service.objects.filter(category=category)
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [ReadOnlyOrAdmin]
    @action(
        detail=True,
        methods=["get"],
        url_path="work-samples",
        serializer_class=WorkSampleWithWorkerSerializer
    )
    def work_samples(self, request, pk=None):
        service = self.get_object()

        queryset = (
            WorkSample.objects
            .filter(service=service)
            .select_related("worker_profile", "worker_profile__user")
        )

        return Response(
            self.get_serializer(queryset, many=True).data
        )


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Müşteri: Sadece kendi randevularını görsün
        if self.request.user.is_customer and hasattr(self.request.user, 'customer_profile'):
            return Appointment.objects.filter(customer=self.request.user.customer_profile).order_by('-start_time')
        # Çalışan: Sadece kendisine ait randevuları görsün
        if self.request.user.is_employee and hasattr(self.request.user, 'worker_profile'):
            return Appointment.objects.filter(worker=self.request.user.worker_profile).order_by('-start_time')
        # Admin/Superuser: Hepsini görsün
        return super().get_queryset()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Güncelleme ve silme için özel izin
            self.permission_classes = [IsAppointmentOwnerOrWorker | IsAdminUser]
        elif self.action == 'create':
            # Oluşturma sadece müşteriye açık
            self.permission_classes = [IsCustomerUser]
        return super().get_permissions()
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        appointment = Appointment.objects.get(pk=pk)
        user = request.user

        if not hasattr(user, "worker_profile"):
            return Response(
                {"detail": "Sadece çalışanlar randevu onaylayabilir."},
                status=status.HTTP_403_FORBIDDEN
            )

        if appointment.worker != user.worker_profile:
            return Response(
                {"detail": "Bu randevu size ait değil."},
                status=status.HTTP_403_FORBIDDEN
            )

        if appointment.status != "PENDING":
            return Response(
                {"detail": "Bu randevu zaten karara bağlanmış."},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = "APPROVED"
        appointment.save(update_fields=["status"])
        return Response(
            {"id": appointment.id, "status": appointment.status},
            status=status.HTTP_200_OK
        )

    # =========================
    # WORKER REJECT
    # =========================
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        appointment = Appointment.objects.get(pk=pk)
        user = request.user

        if not hasattr(user, "worker_profile"):
            return Response(
                {"detail": "Sadece çalışanlar randevu reddedebilir."},
                status=status.HTTP_403_FORBIDDEN
            )

        if appointment.worker != user.worker_profile:
            return Response(
                {"detail": "Bu randevu size ait değil."},
                status=status.HTTP_403_FORBIDDEN
            )

        if appointment.status != "PENDING":
            return Response(
                {"detail": "Bu randevu zaten karara bağlanmış."},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = "REJECTED"
        appointment.save(update_fields=["status"])

        return Response(
            {"status": appointment.status},
            status=status.HTTP_200_OK
        )
    @action(
        detail=False,
        methods=["get"],
        url_path="all-with-profiles",
        permission_classes=[IsAdminUser],  # Admin only
    )
    def all_with_profiles(self, request):
        """
        Admin-only: fetch all appointments with worker and customer profiles safely.
        Prints errors if something fails.
        """
        try:
            queryset = self.get_queryset().select_related(
                "worker__user", "customer__user", "service"
            )
            serializer = AppointmentWithProfilesSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            # Print the full error to console/log
            print("Error in all-with-profiles endpoint:", str(e))
            import traceback
            traceback.print_exc()

            # Return error response
            return Response(
                {"detail": "An error occurred. See server logs for details.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class EmployeeAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = EmployeeAvailability.objects.all()
    serializer_class = EmployeeAvailabilitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Çalışan: Sadece kendi müsaitliklerini görsün
        if self.request.user.is_employee and hasattr(self.request.user, 'worker_profile'):
            return EmployeeAvailability.objects.filter(worker_profile=self.request.user.worker_profile)
        # Diğerleri (Admin/Müşteri): Hepsini görebilir (Randevu almak için)
        return super().get_queryset()

    def perform_create(self, serializer):
        # Çalışanın kendi müsaitliğini eklemesini sağla
        if not self.request.user.is_employee or not hasattr(self.request.user, 'worker_profile'):
            # Adminler veya Superuser'lar için başka bir mantık gerekebilir, 
            # ancak bu örnekte sadece çalışanlar için sınırlıyorum.
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Sadece çalışanlar müsaitlik ekleyebilir.")
            
        serializer.save(worker_profile=self.request.user.worker_profile)
        
    def get_permissions(self):
        # Oluşturma, Güncelleme, Silme sadece çalışana/admin'e açık
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsEmployeeUser | IsAdminUser]
        return super().get_permissions()
    # ✅ NEW ACTION
    @action(
        detail=False,
        methods=['get'],
        url_path='by-worker/(?P<worker_id>[^/.]+)',
        permission_classes=[AllowAny]
    )
    def by_worker(self, request, worker_id=None):
        """
        Customer/Admin fetch availability + booked dates of a worker
        """

        # ✅ Weekly availability
        availabilities = EmployeeAvailability.objects.filter(
            worker_profile_id=worker_id,
            is_active=True
        )

        # ❌ Booked (occupied) slots
        booked_appointments = Appointment.objects.filter(
            worker_id=worker_id,
            status="APPROVED",       # optionally include PENDING
            end_time__gte=now()      # ignore past bookings
        ).order_by("start_time")

        return Response({
            "availabilities": EmployeeAvailabilitySerializer(
                availabilities, many=True
            ).data,
            "booked": BookedAppointmentSerializer(
                booked_appointments, many=True
            ).data
        })
    @action(
        detail=False,
        methods=['put'],
        url_path='bulk-update',
        permission_classes=[IsEmployeeUser | IsAdminUser]
    )
    def bulk_update(self, request):
        data_list = request.data
        if not isinstance(data_list, list):
            return Response({"detail": "Data must be a list."}, status=400)

        if not hasattr(request.user, 'worker_profile'):
            return Response({"detail": "User has no worker profile."}, status=400)

        updated_objects = []
        errors = []

        request_ids = []

        for item in data_list:
            obj_id = item.get('id')
            day_of_week = item.get('day_of_week')
            start_time = item.get('start_time') or "00:00:00"
            end_time = item.get('end_time') or "00:00:00"
            item['start_time'] = start_time
            item['end_time'] = end_time

            try:
                # Try to get existing by ID
                if obj_id:
                    availability = EmployeeAvailability.objects.get(
                        id=obj_id, worker_profile=request.user.worker_profile
                    )
                else:
                    # Or by unique constraint (day_of_week + times)
                    availability = EmployeeAvailability.objects.filter(
                        worker_profile=request.user.worker_profile,
                        day_of_week=day_of_week,
                        start_time=start_time,
                        end_time=end_time
                    ).first()

                if availability:
                    # Update existing
                    serializer = EmployeeAvailabilitySerializer(
                        availability, data=item, partial=True
                    )
                else:
                    # Create new
                    serializer = EmployeeAvailabilitySerializer(data=item)

                if serializer.is_valid():
                    serializer.save(worker_profile=request.user.worker_profile)
                    updated_objects.append(serializer.data)
                    if 'id' in serializer.data:
                        request_ids.append(serializer.data['id'])
                else:
                    errors.append({"item": item, "error": serializer.errors})

            except EmployeeAvailability.DoesNotExist:
                errors.append({"item": item, "error": "Not found"})
            except Exception as e:
                errors.append({"item": item, "error": f"Unexpected error: {str(e)}"})

        # Delete any existing availabilities not in the request
        EmployeeAvailability.objects.filter(
            worker_profile=request.user.worker_profile
        ).exclude(id__in=request_ids).delete()

        return Response({"updated": updated_objects, "errors": errors}, status=200)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            # Sadece Admin veya kendi profilini görme/güncelleme
            self.permission_classes = [IsSelfOrAdmin] 
        return super().get_permissions()
    
    def get_queryset(self):
        # Müşteri sadece kendi profilini görebilir
        if self.request.user.is_customer and hasattr(self.request.user, 'customer_profile'):
            return Customer.objects.filter(user=self.request.user)
        # Admin/Çalışan herkesi görebilir
        return super().get_queryset()
    @action(
        detail=False,
        methods=['get'],
        url_path='all',
        permission_classes=[IsAdminUser]  # Only admin can access
    )
    def all_customers(self, request):
        customers = Customer.objects.all().select_related('user')
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)

class WorkerViewSet(viewsets.ModelViewSet):
    queryset = Worker.objects.all()
    serializer_class = WorkerSerializer
    permission_classes = [IsAuthenticated]

    @action(
        detail=False,
        methods=['post'],
        url_path='approve',
        permission_classes=[IsAdminUser]
    )
    def approve(self, request):
        serializer = WorkerIdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        worker_id = serializer.validated_data['id']

        try:
            worker = Worker.objects.get(id=worker_id)
        except Worker.DoesNotExist:
            return Response({'detail': 'Worker not found.'}, status=status.HTTP_404_NOT_FOUND)

        if worker.status == 'approved':
            return Response({'detail': 'Worker already approved.'}, status=status.HTTP_400_BAD_REQUEST)

        worker.status = 'approved'
        worker.save(update_fields=['status'])
        return Response({'id': worker.id, 'status': worker.status})

    @action(
        detail=False,
        methods=['post'],
        url_path='reject',
        permission_classes=[IsAdminUser]
    )
    def reject(self, request):
        serializer = WorkerIdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        worker_id = serializer.validated_data['id']

        try:
            worker = Worker.objects.get(id=worker_id)
        except Worker.DoesNotExist:
            return Response({'detail': 'Worker not found.'}, status=status.HTTP_404_NOT_FOUND)

        if worker.status == 'rejected':
            return Response({'detail': 'Worker already rejected.'}, status=status.HTTP_400_BAD_REQUEST)

        worker.status = 'rejected'
        worker.save(update_fields=['status'])
        return Response({'id': worker.id, 'status': worker.status})
class WorkSampleViewSet(viewsets.ModelViewSet):
    queryset = WorkSample.objects.all()
    serializer_class = WorkSampleSerializer
    permission_classes = [ReadOnlyOrAdmin] # Varsayılan: Herkes görebilir, sadece Admin ekleyebilir/güncelleyebilir.
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Worker.objects.none() 
        # Çalışan kendi iş örneklerini görsün, Müşteri hepsini görsün.
        if self.request.user.is_employee and hasattr(self.request.user, 'worker_profile'):
            return WorkSample.objects.filter(worker_profile=self.request.user.worker_profile)
        return super().get_queryset()

    def get_permissions(self):
        # Yaratma, Güncelleme, Silme sadece Çalışan veya Admin'e açık olmalı.
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # İş örneği sadece kendi çalışanları tarafından eklenmeli veya Admin tarafından.
            self.permission_classes = [IsEmployeeUser | IsAdminUser]
        return super().get_permissions()
        
    def perform_create(self, serializer):
        # İş Örneği oluşturan kullanıcının Çalışan Profili'ni otomatik ata
        if self.request.user.is_employee and hasattr(self.request.user, 'worker_profile'):
            serializer.save(worker_profile=self.request.user.worker_profile)
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Sadece çalışanlar veya yöneticiler iş örneği ekleyebilir.")
        
class LegalTextViewSet(viewsets.ModelViewSet):
    queryset = LegalText.objects.filter(is_active=True).order_by('type')
    serializer_class = LegalTextSerializer
    
    def get_permissions(self):
        # Okuma (GET) herkese açık (AllowAny), Yaratma/Güncelleme/Silme sadece Admin'e açık.
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()
class WorkerMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        worker = request.user.worker_profile
        serializer = WorkerMeSerializer(worker)
        return Response(serializer.data)
    def patch(self, request):
        worker = request.user.worker_profile
        serializer = WorkerMeSerializer(
            worker,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class CustomerMeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: CustomerSerializer})
    def get(self, request):
        if not hasattr(request.user, "customer_profile"):
            return Response({"detail": "This user has no customer profile."}, status=404)
        serializer = CustomerSerializer(request.user.customer_profile)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=CustomerSerializer, responses={200: CustomerSerializer})
    def patch(self, request):
        if not hasattr(request.user, "customer_profile"):
            return Response({"detail": "This user has no customer profile."}, status=404)
        serializer = CustomerSerializer(request.user.customer_profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
class WorkerApplicationView(APIView):
    permission_classes = [permissions.AllowAny]  # Public endpoint

    REQUIRED_FIELDS = [
        'first_name', 'last_name', 'email', 'phone',
        'city', 'service_category', 'experience_duration',
         'cv', 'accept_terms', 'accept_privacy'
    ]

    # Define swagger schema manually
    request_body = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=REQUIRED_FIELDS,
        properties={
            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
            'phone': openapi.Schema(type=openapi.TYPE_STRING),
            'birth_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='gg.aa.yyyy'),
            'address': openapi.Schema(type=openapi.TYPE_STRING),
            'city': openapi.Schema(type=openapi.TYPE_STRING),
            'postal_code': openapi.Schema(type=openapi.TYPE_STRING),
            'service_category': openapi.Schema(type=openapi.TYPE_STRING),
            'experience_duration': openapi.Schema(type=openapi.TYPE_STRING),
            
            'cv': openapi.Schema(type=openapi.TYPE_FILE, description='PDF, max 5MB'),
            'id_document': openapi.Schema(type=openapi.TYPE_FILE, description='Optional'),
            'accept_terms': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'accept_privacy': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        }
    )

    @swagger_auto_schema(request_body=request_body, responses={201: WorkerSerializer})
    def post(self, request):
        # Ensure request.data is a dict
        if isinstance(request.data, str):
            import json
            try:
                data = json.loads(request.data)
            except Exception:
                return Response({"detail": "Invalid request format"}, status=400)
        else:
            data = request.data

        # Check required fields
        missing_fields = [
            field for field in self.REQUIRED_FIELDS
            if not data.get(field) or str(data.get(field)).strip() == ""
        ]

        if missing_fields:
            return Response(
                {"detail": "Missing or blank required fields", "fields": missing_fields},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = WorkerApplicationSerializer(data=data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
