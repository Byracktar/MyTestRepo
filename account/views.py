from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView


from .models import (
    Category, Service, Appointment, EmployeeAvailability, Customer, Worker , WorkSample, LegalText,
    
)
from .serializers import (
    CategorySerializer, ServiceSerializer, AppointmentSerializer, 
    EmployeeAvailabilitySerializer, CustomerSerializer, WorkerSerializer, 
    WorkSampleSerializer, LegalTextSerializer,CustomUserMeSerializer,WorkerMeSerializer
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


class WorkerViewSet(viewsets.ModelViewSet):
    queryset = Worker.objects.all()
    serializer_class = WorkerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            # Sadece Admin veya kendi profilini görme/güncelleme
            self.permission_classes = [IsSelfOrAdmin]
        return super().get_permissions()
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Worker.objects.none() 
        user = self.request.user
        # Çalışan sadece kendi profilini görebilir
        if user.is_authenticated and getattr(user, 'is_employee', False) and hasattr(user, 'worker_profile'):
            return Worker.objects.filter(user=user)

        return super().get_queryset()


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