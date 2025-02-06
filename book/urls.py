from django.urls import path
from .views import SearchBooksByKeywordView

urlpatterns = [
    path('search/', SearchBooksByKeywordView.as_view(), name='search_books'),
]