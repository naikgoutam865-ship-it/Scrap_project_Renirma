from django.conf import settings
from django.db import models

class Artwork(models.Model):

    artist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="artworks"
    )
    scrap = models.ForeignKey(
        "scrap.Scrap",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.FloatField()

    image = models.ImageField(upload_to="artworks/", null=True, blank=True)

    is_active = models.BooleanField(default=True)   # ✅ YE LINE ADD KARO

    
    
    quantity = models.PositiveIntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):

    # quantity 0 hone par artwork inactive ho jayega
        if self.quantity <= 0:
            self.is_active = False

        super().save(*args, **kwargs)

