"""Root URL configuration.

v1 API lives under /api/v1/. Django admin at /admin/. Health at /healthz/.
Media uploads are served in DEBUG (local pilot); wire S3 for production
(STANDARDS.md §6).
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
