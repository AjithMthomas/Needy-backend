"""Business-rule exceptions shared by all apps.

Services raise these; the DRF layer translates them into the
``{detail, code}`` envelope automatically.
"""

from rest_framework.exceptions import APIException


class BusinessRuleError(APIException):
    status_code = 400
    default_code = "business_rule"


class ModerationBlockedError(BusinessRuleError):
    default_code = "moderation_blocked"


class KarmaInsufficientError(BusinessRuleError):
    status_code = 402
    default_code = "karma_insufficient"


class CapacityFullError(BusinessRuleError):
    status_code = 409
    default_code = "capacity_full"


class GenderRestrictedError(BusinessRuleError):
    status_code = 403
    default_code = "gender_restricted"
