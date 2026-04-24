from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):

    ROLE_CHOICES = (
        ('user', 'User'),
        ('dealer', 'Dealer'),
        ('artist', 'Artist'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="user"
    )
    phone = models.CharField(max_length=15, blank=True, null=True)

    language = models.CharField(max_length=10, default="en")
    
    def __str__(self):
        return self.username

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from scrap.models import Wallet

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):

    if created:
        Wallet.objects.create(user=instance)