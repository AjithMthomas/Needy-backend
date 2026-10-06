"""posts URL routes (mounted under /api/v1/).

Route order matters: specific actions MUST precede the generic
``<action>`` catch-all, or Django would shadow them.
"""

from django.urls import path

from apps.posts import views

urlpatterns = [
    path("posts", views.FeedView.as_view(), name="feed"),
    path("posts/create", views.TaskCreateView.as_view(), name="task-create"),
    path("posts/<uuid:task_id>", views.TaskDetailView.as_view(), name="task-detail"),
    path("posts/<uuid:task_id>/apply", views.ApplyView.as_view(), name="task-apply"),
    path(
        "posts/<uuid:task_id>/applications",
        views.ApplicationsForTaskView.as_view(),
        name="task-applications",
    ),
    path("posts/<uuid:task_id>/save", views.SaveToggleView.as_view(), name="task-save"),
    path("posts/<uuid:task_id>/repost", views.RepostToggleView.as_view(), name="task-repost"),
    path("posts/<uuid:task_id>/rate", views.RateView.as_view(), name="task-rate"),
    path("posts/<uuid:task_id>/<str:action>", views.TaskActionView.as_view(), name="task-action"),
    path(
        "applications/<uuid:application_id>/<str:action>",
        views.ApplicationActionView.as_view(),
        name="application-action",
    ),
]
