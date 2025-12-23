# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Customer, CustomUser

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
