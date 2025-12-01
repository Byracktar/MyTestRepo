# account/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'services', views.ServiceViewSet)
router.register(r'appointments', views.AppointmentViewSet)
router.register(r'availabilities', views.EmployeeAvailabilityViewSet)
router.register(r'customers', views.CustomerViewSet) 
router.register(r'workers', views.WorkerViewSet)
router.register(r'worksamples', views.WorkSampleViewSet) 
router.register(r'legaltexts', views.LegalTextViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path("", views.home_view, name="home"),
    # Djoser endpoints (JWT kullanıyorsanız sadece jwt ekleyin)
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
