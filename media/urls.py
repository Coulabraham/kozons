from django.urls import path

from .views import CompleteUploadView, MediaAssetDetailView, PresignUploadView

urlpatterns = [
    path("presign/", PresignUploadView.as_view(), name="media-presign"),
    path("<int:asset_id>/complete/", CompleteUploadView.as_view(), name="media-complete"),
    path("<int:asset_id>/", MediaAssetDetailView.as_view(), name="media-detail"),
]
