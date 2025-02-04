from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Book
from .serializers import BookSerializer

class BookList(APIView):
    def get(self, request):
        books = Book.objects.all()  # Récupère tous les livres
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

class BookDetail(APIView):
    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk)  # Recherche le livre par ID
        except Book.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = BookSerializer(book)
        return Response(serializer.data)

class FrenchBookList(APIView):
    def get(self, request):
        books = Book.objects.filter(language='French')  # Filtrer les livres en français
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

class FrenchBookDetail(APIView):
    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk, language='French')  # Recherche un livre en français par ID
        except Book.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = BookSerializer(book)
        return Response(serializer.data)

class EnglishBookList(APIView):
    def get(self, request):
        books = Book.objects.filter(language='English')  # Filtrer les livres en anglais
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

class EnglishBookDetail(APIView):
    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk, language='English')  # Recherche un livre en anglais par ID
        except Book.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = BookSerializer(book)
        return Response(serializer.data)
