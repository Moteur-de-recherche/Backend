import re
import logging
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.db.models import Q
from .models import Book, Index
from .serializers import BookSerializer
from nltk.tokenize import word_tokenize


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# Liste des livres avec pagination
class BookListView(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    pagination_class = CustomPagination 

class BookDetailView(APIView):
    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk)
            serializer = BookSerializer(book)
            return Response(serializer.data)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

class BookSearchView(generics.ListAPIView):
    serializer_class = BookSerializer
    pagination_class = CustomPagination  

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip().lower()
        if not query:
            return Book.objects.none()
        
        indexed_books = Index.objects.filter(word=query).select_related("book")

        # Récupérer les IDs des livres concernés
        book_ids = indexed_books.values_list("book_id", flat=True).distinct()
        return Book.objects.filter(id__in=book_ids)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        query = request.query_params.get("q", "").strip().lower()
        occurrences_dict = {
            entry.book_id: entry.occurrences_count
            for entry in Index.objects.filter(word=query)
        }

        results = []
        for book in page:
            book_data = BookSerializer(book).data
            book_data["occurrences_count"] = occurrences_dict.get(book.id, 0)
            results.append(book_data)

        return self.get_paginated_response(results)

class BookAdvancedSearchView(APIView):
    pagination_class = CustomPagination

    def get(self, request):
        query = self.request.query_params.get("q", "")

        if not query:
            return Response({"detail": "No query provided."}, status=400)

        def execute_search():
            try:
                # Limitation à un nombre maximum de résultats pour éviter la surcharge de la base de données
                # Si vous avez un grand volume de livres, utilisez un nombre raisonnable de résultats
                max_results = 100  # Vous pouvez ajuster ce nombre selon votre besoin

                # Recherche dans le contenu textuel des livres (text_content)
                books_by_text_content = Book.objects.filter(
                    Q(text_content__regex=query)
                ).distinct()[:max_results]  # Limiter à un certain nombre de résultats

                # Recherche dans les mots de l'index (Index)
                books_in_index = Book.objects.filter(
                    Q(index__word__regex=query)
                ).distinct()[:max_results]  # Limiter également dans l'index

                # Combine les deux résultats (les livres peuvent apparaître dans les deux)
                books = books_by_text_content | books_in_index

                return books
            except Exception as e:
                return str(e)

        # Exécution de la recherche
        books = execute_search()

        # Pagination des résultats
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(books, request)
        
        if result_page is not None:
            serialized_books = BookSerializer(result_page, many=True)
            return paginator.get_paginated_response(serialized_books.data)

        return Response({"detail": "No results found."}, status=404)

class BookHighlightSearchView(APIView):
    pagination_class = CustomPagination

    def get(self, request):
        query = self.request.query_params.get("q", "").strip().lower()
        if not query:
            return Response({"detail": "No query provided."}, status=400)

        indexed_books = Index.objects.filter(word=query).select_related("book")

        # Récupérer les IDs des livres concernés
        book_ids = indexed_books.values_list("book_id", flat=True).distinct()
        books = Book.objects.filter(id__in=book_ids).order_by('id')  # Ajouter un ordre par défaut

        # Pagination des résultats
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(books, request)
        if result_page is not None:
            serialized_books = BookSerializer(result_page, many=True).data
            highlighted_books = self.highlight_words(serialized_books, query)
            return paginator.get_paginated_response(highlighted_books)

        # Si aucun résultat n'est trouvé
        if books:
            serialized_books = BookSerializer(books, many=True).data
            highlighted_books = self.highlight_words(serialized_books, query)
            return Response(highlighted_books)
        else:
            return Response({"detail": "No results found."}, status=404)

    def highlight_words(self, books, query):
        for book in books:
            index_entries = Index.objects.filter(book_id=book['id'], word=query)
            positions = []
            for entry in index_entries:
                positions.extend(entry.get_positions())  # Utiliser get_positions pour désérialiser
            positions = sorted(set(positions))  # Éliminer les doublons et trier les positions

            logging.debug(f"Book ID: {book['id']}, Positions: {positions}")

            text_content = book['text_content']
            highlighted_text = self.apply_highlight(text_content, positions, query)
            book['highlighted_text'] = highlighted_text
        return books

    def apply_highlight(self, text, positions, query):
        highlighted_text = ""
        last_pos = 0
        query_length = len(query)
        for pos in positions:
            pos = int(pos)  # Assurer que la position est un entier
            logging.debug(f"Position: {pos}, Last Position: {last_pos}")
            highlighted_text += text[last_pos:pos] + "<mark>" + text[pos:pos+query_length] + "</mark>"
            last_pos = pos + query_length
        highlighted_text += text[last_pos:]
        logging.debug(f"Highlighted Text: {highlighted_text}")
        return highlighted_text