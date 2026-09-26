from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from .views import MeView, RegisterView, UserDetailView

app_name = "users"

urlpatterns = [
    path("api/v1/auth/register/", RegisterView.as_view(), name="register"),
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token-obtain"),      # login -> 2 tokens
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),  # refresh -> new access
    path("api/v1/auth/token/verify/", TokenVerifyView.as_view(), name="token-verify"),    # is this token valid?
    path("api/v1/auth/me/", MeView.as_view(), name="me"),
    path("api/v1/users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
]
