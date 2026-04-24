from django.db import models
from django.conf import settings

class ChatMemory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.created_at}"

class AIKnowledge(models.Model):
    key = models.CharField(max_length=200, unique=True)
    value = models.TextField()

    def __str__(self):
        return self.key
