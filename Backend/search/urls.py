from django.urls import path
from .views import SearchPrecedentsView

urlpatterns = [
    path("search/", SearchPrecedentsView.as_view(), name="search_precedents"),
]
