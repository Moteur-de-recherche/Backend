from django.urls import path
from .views import BookList, BookDetail, FrenchBookList, FrenchBookDetail, EnglishBookList, EnglishBookDetail

urlpatterns = [
    path('books/', BookList.as_view(), name='book-list'),
    path('book/<int:pk>/', BookDetail.as_view(), name='book-detail'),
    path('frenchbooks/', FrenchBookList.as_view(), name='french-book-list'),
    path('frenchbook/<int:pk>/', FrenchBookDetail.as_view(), name='french-book-detail'),
    path('englishbooks/', EnglishBookList.as_view(), name='english-book-list'),
    path('englishbook/<int:pk>/', EnglishBookDetail.as_view(), name='english-book-detail'),
]
