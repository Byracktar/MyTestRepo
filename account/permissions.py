# account/permissions.py
from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)

class IsEmployeeUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_employee)

class IsSelfOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        # obj.user ise (profile vb.)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False

class IsAppointmentOwnerOrWorker(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        # obj.customer ve obj.worker modellerimiz Customer/Worker instance'ları
        if hasattr(request.user, 'customer_profile') and obj.customer == request.user.customer_profile:
            return True
        if hasattr(request.user, 'worker_profile') and obj.worker == request.user.worker_profile:
            return True
        return False
class ReadOnlyOrAdmin(permissions.BasePermission):
    """Anonim kullanıcılar için sadece okuma (GET, HEAD, OPTIONS), diğerleri için Admin/Superuser gerektirir."""
    def has_permission(self, request, view):
        # Güvenli metotlar (GET, HEAD, OPTIONS) herkese açık.
        if request.method in permissions.SAFE_METHODS:
            return True
        # YAZMA (POST, PUT, DELETE) işlemleri için
        return bool(request.user and 
                    request.user.is_authenticated and 
                    (request.user.is_admin or request.user.is_superuser)
                   )
    
class IsCustomerUser(permissions.BasePermission):
    """Sadece is_customer=True olan kullanıcıların erişimine izin verir."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_customer)    