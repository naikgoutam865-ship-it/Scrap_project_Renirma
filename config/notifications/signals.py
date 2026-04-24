from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification
from scrap.models import ScrapRequest


@receiver(post_save, sender=ScrapRequest)
def debug_signal(sender, instance, created, **kwargs):

    print("🔥 SIGNAL FIRED 🔥")
    print("created =", created)
    print("status =", instance.status)
