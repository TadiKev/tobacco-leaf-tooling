# backend/inference_logs/urls.py
from django.urls import path
from .views import DetectView

urlpatterns = [
    path("detect", DetectView.as_view(), name="api-detect-no-slash"),
    path("detect/", DetectView.as_view(), name="api-detect"),
    path("predict", DetectView.as_view(), name="api-predict-no-slash"),
    path("predict/", DetectView.as_view(), name="api-predict"),
]
