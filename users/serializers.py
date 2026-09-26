from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()                               # our custom User (never import it directly)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,                              # accepted IN, never sent back OUT
        validators=[validate_password],               # Django's password rules (length, common, etc.)
    )

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)  # create_user HASHES the password (1A-1)


class MeSerializer(serializers.ModelSerializer):     # "my profile"
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "is_staff", "date_joined"]
        read_only_fields = ["is_staff", "date_joined"]  # users can't make themselves staff
