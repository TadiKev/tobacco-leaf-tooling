# backend/inference_logs/admin.py
from django.contrib import admin
from .models import InferenceLog

@admin.register(InferenceLog)
class InferenceLogAdmin(admin.ModelAdmin):
    list_display = ("uploaded_at","predicted_label","confidence","synced_for_retrain")
    list_filter = ("synced_for_retrain","predicted_label")
    search_fields = ("predicted_label","user_feedback")
    actions = ["mark_synced"]
    def mark_synced(self, request, queryset):
        queryset.update(synced_for_retrain=True)
        self.message_user(request, f"Marked {queryset.count()} logs as synced")
    mark_synced.short_description = "Mark selected logs as synced"
