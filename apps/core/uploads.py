"""POST /api/v1/uploads — authenticated image upload.

Pilot-simple: bytes land on local disk (MEDIA_ROOT/uploads/). On Render's
ephemeral disk they die with the container — move to S3 when it matters
(STANDARDS.md §6). Returns an absolute URL usable directly as
AuctionItem.image_url.

Validation: JPEG/PNG/WebP only, 5 MB cap. The file extension is derived
from the declared content type — never from the client-supplied filename.
"""

import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

# Sniffed from magic bytes — never trust the client-declared content type.
_MAGIC_TO_EXT = (
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"RIFF", "webp"),  # + bytes 8-11 == b"WEBP" (checked below)
)


def _sniff_ext(head: bytes) -> str | None:
    """Return the extension for a recognized image signature, else None."""
    for magic, ext in _MAGIC_TO_EXT:
        if head.startswith(magic):
            if ext == "webp" and head[8:12] != b"WEBP":
                return None
            return ext
    return None


class UploadView(APIView):
    """POST /uploads — multipart field ``file``; 201 {url}."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        f = request.FILES.get("file")
        if f is None:
            return Response(
                {"detail": "multipart field 'file' is required.", "code": "invalid"},
                status=400,
            )
        if f.size > MAX_UPLOAD_BYTES:
            return Response(
                {"detail": "Image is too large (5 MB max).", "code": "invalid"},
                status=400,
            )
        ext = _sniff_ext(f.read(16))
        f.seek(0)  # rewind — sniffing advanced the pointer
        if ext is None:
            return Response(
                {"detail": "Only JPEG, PNG, or WebP images are allowed.", "code": "invalid"},
                status=400,
            )

        saved = default_storage.save(
            f"uploads/{uuid.uuid4().hex}.{ext}",
            ContentFile(f.read()),
        )
        url = request.build_absolute_uri(f"{settings.MEDIA_URL}{saved}")
        return Response({"url": url}, status=201)
