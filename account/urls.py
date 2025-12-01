# account/urls.py
from django.urls import path
from . import views
from .backend import (
    MyTokenObtainPairView,
    get_services,
    set_services,
    get_operators,
    get_operator_info,
    set_operator_info,
    post_operator
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Frontend sayfaları
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('', views.home_view, name='home'),

    # JWT Endpoints
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Hizmetler
    path('api/services/', get_services, name='get_services'),          # GET
    path('api/services/add/', set_services, name='set_services'),     # POST (admin)

    # Ustalar
    path('api/operators/', get_operators, name='get_operators'),     # GET
    path('api/operator/info/', get_operator_info, name='get_operator_info'),  # GET
    path('api/operator/add/', set_operator_info, name='set_operator_info'),   # POST (admin)
    path('api/operator/select/', post_operator, name='post_operator'),        # POST
]
