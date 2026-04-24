from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from .models import Scrap, ScrapAlert

@receiver(post_save, sender=Scrap)
def notify_scrap_available(sender, instance, created, **kwargs):

    if not created:
        return

    alerts = ScrapAlert.objects.filter(
        category=instance.category,
        is_notified=False
    )

    for alert in alerts:

        if not alert.user.email:
            continue

        send_mail(
            subject="♻ Scrap Available Now on ReNirma!",
            message=f"""
Hello {alert.user.username},

Good news!

The scrap you were searching for is now available.

Category: {instance.category}
Weight: {instance.weight_kg} kg

Login now and request it before others do!

– ReNirma Team
""",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[alert.user.email],
            fail_silently=True,
        )

        alert.is_notified = True
        alert.save()
