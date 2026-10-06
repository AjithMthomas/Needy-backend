from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import Badge, Member, OtpCode


@admin.register(Member)
class MemberAdmin(BaseUserAdmin):
    ordering = ["-created_at"]
    # Custom user without PermissionsMixin: no groups/permissions M2M.
    filter_horizontal = ()
    list_display = (
        "email",
        "public_name",
        "gender",
        "karma",
        "is_guardian",
        "available_now",
        "verified_badge",
        "is_active",
        "created_at",
    )
    list_filter = ("gender", "is_guardian", "available_now", "verified_badge", "is_active")
    search_fields = ("email", "public_name")
    readonly_fields = (
        "last_login",
        "joined_at",
        "created_at",
        "updated_at",
        "completed_count",
        "rating",
        "rating_count",
        "cancellations",
        "no_shows",
    )
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Profile",
            {
                "fields": (
                    "public_name",
                    "photo_url",
                    "gender",
                    "bio",
                    "categories",
                    "date_of_birth",
                    "age_gate_passed",
                    "profile_completed",
                    "availability_hours",
                )
            },
        ),
        ("Community", {"fields": ("karma", "is_guardian", "available_now")}),
        ("Safety", {"fields": ("safety_contact_name", "safety_contact_phone")}),
        (
            "Flags",
            {
                "fields": (
                    "is_email_verified",
                    "verified_badge",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        ("Dates", {"fields": ("last_login", "joined_at", "created_at", "updated_at")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "public_name")}),)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("member", "badge", "created_at")
    search_fields = ("member__email", "member__public_name")


@admin.register(OtpCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at", "expires_at", "consumed", "attempts")
    list_filter = ("consumed",)
    search_fields = ("email",)
