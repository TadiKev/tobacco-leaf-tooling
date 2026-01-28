import uuid
from django.db import models
from django.conf import settings

class Recommendation(models.Model):
    SEVERITY_CHOICES = [('mild','Mild'),('moderate','Moderate'),('severe','Severe')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    disease_code = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='moderate')
    nonchem_recommendations = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_recs')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_recs')
    approved_at = models.DateTimeField(null=True, blank=True)
    version = models.IntegerField(default=1)
    published = models.BooleanField(default=False)
    safety_flag = models.BooleanField(default=False)
    tags = models.JSONField(default=list, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.disease_code}) - v{self.version}"


class Treatment(models.Model):
    TYPE_CHOICES = [('chemical','Chemical'),('organic','Organic'),('cultural','Cultural'),('preventive','Preventive')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, related_name='treatments')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=255)
    active_ingredient = models.CharField(max_length=255, blank=True)
    dose_text = models.TextField(blank=True)   # human-readable only
    application_method = models.CharField(max_length=200, blank=True)
    pre_harvest_interval = models.CharField(max_length=100, blank=True)
    ppe = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    source = models.CharField(max_length=400, blank=True)

    def __str__(self):
        return f"{self.name} ({self.type})"


class Dealer(models.Model):
    TYPE_CHOICES = [('agrodealer','Agrodealer'),('agrovet','Agrovet'),('veterinary_clinic','Veterinary Clinic')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='agrodealer')
    address = models.CharField(max_length=400, blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    inventory_tags = models.CharField(max_length=500, blank=True)  

    def __str__(self):
        return f"{self.name} ({self.type})"
