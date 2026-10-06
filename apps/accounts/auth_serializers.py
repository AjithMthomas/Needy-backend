"""Auth serializers: email OTP request + verify.

verify() mints JWT access/refresh and returns the member payload in the
same response so the Flutter client signs in with one round-trip.
"""

from __future__ import annotations

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken


class OtpRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OtpVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.RegexField(r"^\d{6}$")

    def get_tokens(self, member) -> dict:
        refresh = RefreshToken.for_user(member)
        return {"access": str(refresh.access_token), "refresh": str(refresh)}


class NuvraTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Password login is unused (OTP-only auth), but kept so admin/CLI JWT
    paths work and a future password fallback is trivial."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["name"] = user.public_name
        return token
