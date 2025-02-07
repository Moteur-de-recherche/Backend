# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from .models import Book
from .serializers import BookSerializer

class CustomPagination(PageNumberPagination):
    page_size = 10  # Nombre d'éléments par page
    page_size_query_param = 'page_size'  # Permet à l'utilisateur de changer la taille de la page
    max_page_size = 100  # Taille maximale autorisée

# Liste des livres avec pagination
class BookListView(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    pagination_class = CustomPagination  # Ajout de la pagination

class BookDetailView(APIView):
    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk)
            serializer = BookSerializer(book)
            return Response(serializer.data)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
