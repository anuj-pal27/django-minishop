from django.contrib.auth import get_user_model
from rest_framework import generics, permissions

from .permissions import IsSelfOrStaff
from .serializers import MeSerializer, RegisterSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):          # POST only: create a user
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]       # anyone can sign up


class MeView(generics.RetrieveUpdateAPIView):        # GET / PATCH my own profile
    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]  # no valid token -> 401

    def get_object(self):
        return self.request.user                      # the user DRF found from the token


class UserDetailView(generics.RetrieveAPIView):      # GET /api/v1/users/<id>/  (1C-2 exercise)
    queryset = User.objects.all()
    serializer_class = MeSerializer                   # reuse: same fields
    permission_classes = [permissions.IsAuthenticated, IsSelfOrStaff]  # get_object() runs IsSelfOrStaff
