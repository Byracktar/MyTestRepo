# account/urls.py
from rest_framework.routers import DefaultRouter
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
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
schema_view = get_schema_view(
   openapi.Info(
      title="4ll In One API",
      default_version='v1',
      description="API dokümantasyonu",
      #terms_of_service="",
      #contact=openapi.Contact(email=""),
      #license=openapi.License(name=""),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('api/', include(router.urls)),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path("api/customer/me/", views.CustomerMeView.as_view(), name="customer-me"),
    path("", views.home_view, name="home"),
    path('auth/users/me/', views.MeView.as_view(), name='users_me'),
    path('api/worker/me/', views.WorkerMeView.as_view(), name='worker_me'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
