import re
import logging
import json
import networkx as nx
from fuzzywuzzy import fuzz  # Pour la distance Levenshtein
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.db.models import Q, Count
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
        author = self.request.query_params.get("author", "").strip().lower()
        
        if not query and not author:
            return Book.objects.none()

        # Filtrer les livres par mot-clé
        indexed_books = Index.objects.filter(word=query).select_related("book")
        book_ids_by_keyword = indexed_books.values_list("book_id", flat=True).distinct()

        # Filtrer les livres par auteur
        if author:
            books_by_author = Book.objects.filter(authors__name__icontains=author).values_list("id", flat=True).distinct()
        else:
            books_by_author = Book.objects.values_list("id", flat=True).distinct()

        # Combiner les filtres
        book_ids = set(book_ids_by_keyword) & set(books_by_author)
        
        return Book.objects.filter(id__in=book_ids).order_by("id")

    def jaccard_similarity(self, set1, set2):
        """Calcul de la similarité de Jaccard entre deux ensembles."""
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union != 0 else 0

    def levenshtein_similarity(self, title1, title2):
        """Calcul de la similarité Levenshtein entre deux titres."""
        return fuzz.ratio(title1, title2) / 100  # Normalisé entre 0 et 1

    def get_similar_books_from_graph(self, book, all_books):
        """Retourne les voisins dans le graphe de Jaccard pour un livre donné."""
        similar_books = []
        book_keywords = set(Index.objects.filter(book_id=book.id).values_list('word', flat=True))
        
        for other_book in all_books:
            if book.id == other_book.id:
                continue
            other_book_keywords = set(Index.objects.filter(book_id=other_book.id).values_list('word', flat=True))
            jaccard_score = self.jaccard_similarity(book_keywords, other_book_keywords)
            
            # Ajouter les livres voisins dans le graphe
            if jaccard_score > 0.1:  # Seuil à ajuster
                similar_books.append({
                    "book": BookSerializer(other_book).data,
                    "jaccard_similarity": jaccard_score
                })
        
        return similar_books

    def list(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip().lower()
        author = request.query_params.get("author", "").strip().lower()
        if not query and not author:
            return self.get_paginated_response([])

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if not page:
            return self.get_paginated_response([])

        # Récupération des occurrences et index liés aux livres
        index_entries = Index.objects.filter(book_id__in=[book.id for book in page])
        occurrences_dict = {entry.book_id: entry.occurrences_count for entry in index_entries}

        # Calcul du PageRank
        pagerank_scores = compute_pagerank(page, index_entries) or {}

        # Calcul des livres similaires via Jaccard et Levenshtein
        similar_books = []
        for book in page:
            book_data = BookSerializer(book).data
            book_data["occurrences_count"] = occurrences_dict.get(book.id, 0)
            book_data["pagerank_score"] = pagerank_scores.get(book.id, 0)

            # Calcul des voisins dans le graphe de Jaccard
            similar_books_for_current = self.get_similar_books_from_graph(book, page)

            book_data["similar_books"] = similar_books_for_current
            similar_books.append(book_data)

        # Trier par occurrences et PageRank combiné
        results = sorted(similar_books, key=lambda x: (x["occurrences_count"], x["pagerank_score"]), reverse=True)

        return self.get_paginated_response(results)

class BookAdvancedSearchView(APIView):
    pagination_class = CustomPagination

    def get(self, request):
        query = self.request.query_params.get("q", "").strip()
        if not query:
            return Response({"detail": "No query provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            max_results = 100  # Limite des résultats

            # Filtrage full-text AVANT d’appliquer une limite
            books_by_full_text = Book.objects.filter(Q(text_content__icontains=query)).distinct()

            # Appliquer regex directement, SANS slice avant le filter
            books_by_regex = books_by_full_text.filter(Q(text_content__regex=query)).distinct()[:max_results]

            # Recherche dans l'index
            indexed_books = Index.objects.filter(
                word__regex=query
            ).values("book_id").annotate(occurrence_count=Count("id"))

            book_ids = [entry["book_id"] for entry in indexed_books]
            books_in_index = Book.objects.filter(id__in=book_ids)

            # Fusionner et enlever les doublons
            books = (books_by_regex | books_in_index).distinct()

            # Étape 4 : Classement par pertinence avec PageRank et occurrences des mots-clés
            pagerank_scores = compute_pagerank(books, Index.objects.filter(book_id__in=[b.id for b in books]))
            book_scores = {book.id: pagerank_scores.get(book.id, 0) for book in books}

            for entry in indexed_books:
                book_id = entry["book_id"]
                book_scores[book_id] += entry["occurrence_count"]

            sorted_books = sorted(books, key=lambda book: book_scores.get(book.id, 0), reverse=True)

            # Pagination
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(sorted_books, request)

            if result_page is not None:
                serialized_books = BookSerializer(result_page, many=True)
                return paginator.get_paginated_response(serialized_books.data)

            return Response({"detail": "No results found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




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
            pos = int(pos)
            logging.debug(f"Position: {pos}, Last Position: {last_pos}")
            highlighted_text += text[last_pos:pos] + "<mark>" + text[pos:pos+query_length] + "</mark>"
            last_pos = pos + query_length
        highlighted_text += text[last_pos:]
        logging.debug(f"Highlighted Text: {highlighted_text}")
        return highlighted_text
    
    
def compute_pagerank(books, index_entries):
    G = nx.Graph()

    # Ajouter les livres comme nœuds
    book_ids = {book.id for book in books}
    for book_id in book_ids:
        G.add_node(book_id)

    # Ajouter des arêtes basées sur la similarité Jaccard des mots-clés
    book_word_sets = {
        book_id: set(entry.word for entry in index_entries if entry.book_id == book_id)
        for book_id in book_ids
    }

    for book1 in book_ids:
        for book2 in book_ids:
            if book1 != book2:
                intersection = book_word_sets[book1] & book_word_sets[book2]
                union = book_word_sets[book1] | book_word_sets[book2]
                if union:
                    jaccard_similarity = len(intersection) / len(union)
                    if jaccard_similarity > 0:  # Ajouter une arête si similarité > 0
                        G.add_edge(book1, book2, weight=jaccard_similarity)

    # Calculer le PageRank
    pagerank_scores = nx.pagerank(G, weight='weight')
    return pagerank_scores
