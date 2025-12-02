# account/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'services', views.ServiceViewSet)
router.register(r'appointments', views.AppointmentViewSet)
router.register(r'availabilities', views.EmployeeAvailabilityViewSet)
router.register(r'customers', views.CustomerViewSet) 
router.register(r'workers', views.WorkerViewSet)
router.register(r'worksamples', views.WorkSampleViewSet) 
router.register(r'legaltexts', views.LegalTextViewSet)
api_urls = [
    # JWT
    path('api/token/', api.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # Categories
    path('api/categories/', api.get_categories, name='fbv_get_categories'),

    # Services
    path('api/services/', api.get_services, name='fbv_get_services'),
    path('api/services/add/', api.set_service, name='fbv_set_service'),

    # Workers
    path('api/workers/', api.get_workers, name='fbv_get_workers'),
    path('api/workers/<int:worker_id>/', api.get_worker_info, name='fbv_get_worker_info'),
    path('api/workers/add/', api.set_worker_info, name='fbv_set_worker_info'),

    # Appointments
    path('api/appointments/', api.get_user_appointments, name='fbv_get_user_appointments'),
    path('api/appointments/create/', api.create_appointment, name='fbv_create_appointment'),

    # Work Samples
    path('api/worksamples/', api.get_work_samples, name='fbv_get_work_samples'),
    path('api/worksamples/add/', api.set_work_sample, name='fbv_set_work_sample'),

    # Legal Texts
    path('api/legaltexts/', api.get_legal_texts, name='fbv_get_legal_texts'),
]

urlpatterns = [
    path('api/', include(router.urls)),
    path('login/', views.login_view, name='login'),
    path('', include(api_urls)),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path("", views.home_view, name="home"),
    # Djoser endpoints (JWT kullanıyorsanız sadece jwt ekleyin)
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
