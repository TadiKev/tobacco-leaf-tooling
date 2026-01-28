# backend/inference_logs/models.py
from django.db import models

class InferenceLog(models.Model):
    image = models.ImageField(upload_to="inference_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    predicted_label = models.CharField(max_length=255, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    model_version = models.CharField(max_length=64, blank=True)
    recommendation_version = models.CharField(max_length=64, blank=True)
    user_feedback = models.TextField(blank=True)
    synced_for_retrain = models.BooleanField(default=False)
    uploader_ip = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.predicted_label} @{self.confidence}"
