from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("search.urls")),  # ← search 앱의 URL 추가
]
