from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .book_views import BookListView, BookDetailView
from .author_views import AuthorListView, AuthorDetailView



urlpatterns = [
    path('authors/', AuthorListView.as_view(), name='author-list'),
    path('authors/<int:pk>/', AuthorDetailView.as_view(), name='author-detail'),
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<int:pk>/', BookDetailView.as_view(), name='book-detail'),
]