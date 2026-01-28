# accounts/urls.py
from django.urls import path
from .views import RegisterView, LogoutView,ProfileView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),      # login
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("profile/", ProfileView.as_view(), name="auth-profile"),
]
