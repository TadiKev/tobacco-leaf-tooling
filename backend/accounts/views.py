# accounts/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated

# Simple register endpoint
class RegisterView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# Token blacklist (logout)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """
        Accepts {"refresh": "<refresh_token>"} to blacklist it (logout).
        If you're using rotating tokens, blacklist the passed refresh token.
        """
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail":"Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail":"Logged out"}, status=status.HTTP_200_OK)

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/account/profile/  -> returns current user
    PATCH /api/account/profile/ -> update allowed fields (username, email, first_name, last_name)
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user