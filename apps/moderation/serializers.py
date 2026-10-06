from rest_framework import serializers

from apps.moderation.models import Report


class ReportCreateSerializer(serializers.Serializer):
    task_id = serializers.UUIDField(required=False, allow_null=True)
    member_id = serializers.UUIDField(required=False, allow_null=True)
    reason = serializers.ChoiceField(choices=Report.Reason.choices)
    details = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")
