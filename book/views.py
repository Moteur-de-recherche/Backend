from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Index, Book
from .serializers import BookSerializer

class SearchBooksByKeywordView(APIView):
    def get(self, request):
        query = request.query_params.get('query', '')  # Récupérer le mot-clé depuis les paramètres de la requête

        # Recherche dans la table d'indexation pour récupérer les livres contenant le mot-clé
        index_entries = Index.objects.filter(word__icontains=query).order_by('-occurrences_count')

        # Récupérer les ids des livres associés
        book_ids = [entry.book.id for entry in index_entries]
        
        # Récupérer les livres correspondants
        books = Book.objects.filter(id__in=book_ids)

        # Sérialiser les livres et renvoyer la réponse
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)
    

