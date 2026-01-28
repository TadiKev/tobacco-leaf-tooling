from django.db import models

class HealthCheck(models.Model):
    created = models.DateTimeField(auto_now_add=True)
