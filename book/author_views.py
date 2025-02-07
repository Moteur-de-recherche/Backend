# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Author
from .serializers import AuthorSerializer

class AuthorListView(APIView):
    def get(self, request):
        authors = Author.objects.all()
        serializer = AuthorSerializer(authors, many=True)
        return Response(serializer.data)

class AuthorDetailView(APIView):
    def get(self, request, pk):
        try:
            author = Author.objects.get(pk=pk)
            serializer = AuthorSerializer(author)
            return Response(serializer.data)
        except Author.DoesNotExist:
            return Response({"detail": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
