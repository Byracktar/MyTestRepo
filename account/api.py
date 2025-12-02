from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Category, Service, Worker, Customer, Appointment, WorkSample, LegalText
from .serializers import (
    CategorySerializer, ServiceSerializer, WorkerSerializer,
    CustomerSerializer, AppointmentSerializer, WorkSampleSerializer, LegalTextSerializer
)

# -------------------
# JWT Login Serializer
# -------------------
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['is_admin'] = user.is_admin
        token['is_employee'] = user.is_employee
        token['is_customer'] = user.is_customer
        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# -------------------
# Categories
# -------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_categories(request):
    categories = Category.objects.filter(parent=None)  # Only top-level
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)

# -------------------
# Services
# -------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_services(request):
    services = Service.objects.all()
    serializer = ServiceSerializer(services, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_service(request):
    if not request.user.is_admin:
        return Response({"error": "Yetkisiz erişim"}, status=status.HTTP_403_FORBIDDEN)
    serializer = ServiceSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------------------
# Workers
# -------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_workers(request):
    workers = Worker.objects.all()
    serializer = WorkerSerializer(workers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_worker_info(request, worker_id):
    try:
        worker = Worker.objects.get(id=worker_id)
    except Worker.DoesNotExist:
        return Response({"error": "Çalışan bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
    serializer = WorkerSerializer(worker)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_worker_info(request):
    if not request.user.is_admin:
        return Response({"error": "Yetkisiz erişim"}, status=status.HTTP_403_FORBIDDEN)
    worker_id = request.data.get('id')
    if worker_id:
        try:
            worker = Worker.objects.get(id=worker_id)
        except Worker.DoesNotExist:
            return Response({"error": "Çalışan bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = WorkerSerializer(worker, data=request.data, partial=True)
    else:
        serializer = WorkerSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------------------
# Appointments
# -------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_appointments(request):
    user = request.user
    if hasattr(user, 'customer_profile'):
        appointments = Appointment.objects.filter(customer=user.customer_profile)
    elif hasattr(user, 'worker_profile'):
        appointments = Appointment.objects.filter(worker=user.worker_profile)
    else:  # Admin
        appointments = Appointment.objects.all()
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_appointment(request):
    serializer = AppointmentSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------------------
# Work Samples
# -------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_work_samples(request):
    samples = WorkSample.objects.all()
    serializer = WorkSampleSerializer(samples, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_work_sample(request):
    if not request.user.is_employee:
        return Response({"error": "Yetkisiz erişim"}, status=status.HTTP_403_FORBIDDEN)
    data = request.data.copy()
    data['worker_profile'] = request.user.worker_profile.id
    serializer = WorkSampleSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------------------
# Legal Texts
# -------------------
@api_view(['GET'])
def get_legal_texts(request):
    texts = LegalText.objects.filter(is_active=True)
    serializer = LegalTextSerializer(texts, many=True)
    return Response(serializer.data)
