from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Customer, Worker, Category, Service, WorkSample,
    Appointment, EmployeeAvailability, LegalText
)
from django.utils.translation import gettext_lazy as _


# ==============================
# Custom User Admin
# ==============================
class WorkerInline(admin.StackedInline):
    model = Worker
    can_delete = False


class CustomerInline(admin.StackedInline):
    model = Customer
    can_delete = False


class CustomUserAdmin(UserAdmin):
    list_display = (
        'email', 'first_name', 'last_name',
        'is_active', 'is_admin', 'is_employee', 'is_customer'
    )
    ordering = ('email',)

    inlines = [WorkerInline, CustomerInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'is_customer', 'is_employee', 'is_admin',
                'groups', 'user_permissions'
            )
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'fields': ('email', 'password1', 'password2',
                       'first_name', 'last_name',
                       'is_customer', 'is_employee', 'is_admin',
                       'is_staff', 'is_superuser')}
        ),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Category)
admin.site.register(Service)
admin.site.register(WorkSample)
admin.site.register(Appointment)
admin.site.register(EmployeeAvailability)
admin.site.register(LegalText)


