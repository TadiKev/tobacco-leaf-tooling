# backend/inference_logs/serializers.py
from rest_framework import serializers
from .models import InferenceLog

class InferenceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = InferenceLog
        fields = "__all__"
        read_only_fields = ("uploaded_at",)
