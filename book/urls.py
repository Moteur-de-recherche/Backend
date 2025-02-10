from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .book_views import BookListView, BookDetailView, BookSearchView, BookAdvancedSearchView, BookHighlightSearchView
from .author_views import AuthorListView, AuthorDetailView



urlpatterns = [
    path('authors/', AuthorListView.as_view(), name='author-list'),
    path('authors/<int:pk>/', AuthorDetailView.as_view(), name='author-detail'),
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<int:pk>/', BookDetailView.as_view(), name='book-detail'),
    path('books/search/', BookSearchView.as_view(), name='book-search'),
    path('books/advanced-search/', BookAdvancedSearchView.as_view(), name='advanced-search'),
    path('books/highlight-search/', BookHighlightSearchView.as_view(), name='book-highlight-search'),
]