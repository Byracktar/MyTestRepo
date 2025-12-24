# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Customer, CustomUser,Category, Service

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_profile(sender, instance, created, **kwargs):
    if created:
        # Eğer kullanıcı müşteri rolünde ise
        if getattr(instance, 'is_customer', True):
            Customer.objects.get_or_create(user=instance)
        
        # Kullanıcının role alanını set et
        if not getattr(instance, 'role', None):
            instance.role = instance.get_role()
            instance.save()



@receiver(post_save, sender=Category)
def sync_service_with_category(sender, instance, created, **kwargs):
    # ❌ Root categories never have services
    if not instance.parent:
        return

    # 🔹 CREATE
    if created:
        Service.objects.create(
            category=instance,
            name=instance.name,
            description=instance.description_tr,
            price_info=instance.price,
            duration_minutes=60,
            rating=0.0,
            image=instance.image,
            price=instance.price,
        )
        return

    # 🔹 UPDATE
    try:
        service = instance.services.get()
    except Service.DoesNotExist:
        # Safety: if service was deleted manually
        Service.objects.create(
            category=instance,
            name=instance.name,
            description=f"{instance.name} service",
            price_info="",
            duration_minutes=60,
            rating=0.0,
            image=None,
            price=None,
        )
        return

    # 🔁 Sync fields
    service.name = instance.name
    service.description = f"{instance.name} service"

    # keep defaults consistent
    service.price_info = service.price_info or ""
    service.duration_minutes = service.duration_minutes or 60
    service.rating = service.rating or 0.0
    service.image = service.image
    service.price = service.price

    service.save()