# backend/inference_logs/views.py
import os
import io
import logging
from typing import Any, Dict

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import InferenceLog
from .serializers import InferenceLogSerializer

LOG = logging.getLogger("inference_logs")
LOG.setLevel(logging.INFO)
if not LOG.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOG.addHandler(ch)


# Default ML endpoint (container hostname as seen by backend)
DEFAULT_ML_URL = os.environ.get("ML_INFER_URL", "http://mlserve:8000/infer")


class DetectView(APIView):
    """
    POST /detect/  - accepts multipart with an image file (key: 'file' or 'image')
                     forwards to mlserve, saves an InferenceLog, and returns the log + model response.
    GET  /detect/  - returns recent inference logs (simple list).
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (AllowAny,)

    def get_ml_url(self) -> str:
        # prefer Django settings, then env var, then default
        return getattr(settings, "ML_INFER_URL", os.environ.get("ML_INFER_URL", DEFAULT_ML_URL))

    def post(self, request, *args, **kwargs):
        """
        Expecting multipart/form-data with the image file under 'file' or 'image'.
        """
        # Accept either 'file' or 'image' key
        upload = request.FILES.get("file") or request.FILES.get("image")
        if upload is None:
            return Response({"detail": "No file uploaded. Use form key 'file' or 'image'."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Read bytes (we will use a ContentFile to save to Django model)
        try:
            upload.open()  # ensure readable
        except Exception:
            pass
        upload.seek(0)
        content_bytes = upload.read()
        if not content_bytes:
            return Response({"detail": "Uploaded file is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare files payload for ml service
        # Use same filename as uploaded
        ml_files = {
            "file": (upload.name, io.BytesIO(content_bytes), upload.content_type or "application/octet-stream")
        }

        ml_url = self.get_ml_url()
        LOG.info("Forwarding image '%s' to ML service at %s", upload.name, ml_url)

        try:
            # timeout small to fail fast; adjust as needed
            resp = requests.post(ml_url, files=ml_files, timeout=15)
        except requests.RequestException as e:
            LOG.exception("Failed to call ML service: %s", e)
            return Response({"detail": "ML service unavailable", "error": str(e)},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if resp.status_code != 200:
            LOG.warning("ML service returned non-200 %s: %s", resp.status_code, resp.text[:500])
            return Response({"detail": "ML service error", "status_code": resp.status_code, "body": resp.text},
                            status=status.HTTP_502_BAD_GATEWAY)

        try:
            ml_json: Dict[str, Any] = resp.json()
        except ValueError:
            LOG.exception("ML response was not JSON: %s", resp.text[:500])
            return Response({"detail": "Invalid response from ML service", "body": resp.text},
                            status=status.HTTP_502_BAD_GATEWAY)

        # Extract prediction fields (be tolerant if keys missing)
        predicted_label = ml_json.get("predicted_label") or ml_json.get("label") or ""
        confidence = ml_json.get("confidence")
        try:
            confidence = float(confidence) if confidence is not None else None
        except Exception:
            confidence = None

        model_path = ml_json.get("model_path") or ml_json.get("model") or ""
        model_type = ml_json.get("model_type") or ""

        # Save InferenceLog (use ContentFile to write bytes to ImageField)
        try:
            content_file = ContentFile(content_bytes, name=upload.name)
            log = InferenceLog.objects.create(
                image=content_file,
                uploaded_at=timezone.now(),
                predicted_label=predicted_label,
                confidence=confidence,
                model_version=model_path or "",
            )
        except Exception as e:
            LOG.exception("Failed to save InferenceLog: %s", e)
            # still return the ML result, but signal saving failed
            return Response({
                "detail": "Prediction succeeded but saving log failed",
                "ml_result": ml_json,
                "save_error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = InferenceLogSerializer(log, context={"request": request})

        # Return both the saved log and raw ml response for debugging
        return Response({
            "inference_log": serializer.data,
            "ml_response": ml_json,
        }, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        """
        Return last 50 inference logs (most recent first).
        """
        qs = InferenceLog.objects.all().order_by("-uploaded_at")[:50]
        serializer = InferenceLogSerializer(qs, many=True, context={"request": request})
        return Response({"count": qs.count(), "results": serializer.data})
