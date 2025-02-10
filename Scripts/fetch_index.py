from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import sys
import os
import re
import django
import nltk
import json  # Utilisé pour stocker les positions en JSON
from django.db import transaction, connection
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Configurer Django
logging.basicConfig(level=logging.INFO)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygutenberg.settings')
django.setup()
from book.models import Book, Index

# Télécharger les ressources nécessaires
nltk.download('stopwords')
nltk.download('punkt')

# Mappage des codes de langue aux stopwords NLTK
LANGUAGE_MAPPING = {
    'en': 'english',
    'fr': 'french',
    'es': 'spanish',
    'de': 'german',
    'it': 'italian',
}

# Fonction pour charger les stopwords en fonction de la langue
def load_stopwords(language):
    try:
        nltk_language = LANGUAGE_MAPPING.get(language, 'english')
        return set(stopwords.words(nltk_language)) if nltk_language in stopwords.fileids() else set()
    except Exception:
        return set(stopwords.words('english'))

# Extraction des mots et de leurs positions SANS nettoyer le texte
def extract_words_with_positions(text, language='english'):
    stop_words = load_stopwords(language)
    word_positions = {}
    
    for match in re.finditer(r'\b\w+\b', text):  # Trouver chaque mot et sa position
        word = match.group()  # Extraire le mot
        pos = match.start()  # Position en caractères
        
        if word.lower() not in stop_words:
            if word not in word_positions:
                word_positions[word] = []
            word_positions[word].append(pos) 
    
    return word_positions


# Fonction pour indexer un livre
def index_book(book):
    try:
        if not book.text_content:
            logging.warning(f"Aucun texte pour le livre {book.title} (ID: {book.id})")
            return

        language = book.language.split(',')[0].strip().lower()
        logging.info(f"Langue détectée pour le livre '{book.title}': {language}")

        # Extraire les mots et leurs positions
        word_positions_map = extract_words_with_positions(book.text_content, language)

        # Créer les entrées pour l'index
        index_entries = [
            Index(
                word=word,
                book=book,
                occurrences_count=len(positions),
                positions=positions  # Stocker les positions sous forme de liste
            )
            for word, positions in word_positions_map.items()
        ]

        with transaction.atomic():
            Index.objects.bulk_create(index_entries, ignore_conflicts=True)

        connection.close()
        logging.info(f"Indexation du livre '{book.title}' (ID: {book.id}) terminée.")

    except Exception as e:
        logging.error(f"Erreur lors de l'indexation du livre {book.title} (ID: {book.id}): {e}")
        
        
# Fonction principale pour indexer les livres en parallèle
def index_books_concurrently():
    logging.info("Début de l'indexation des livres...")

    books_to_index = Book.objects.filter(text_content__isnull=False)

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_book = {executor.submit(index_book, book): book for book in books_to_index}

        for future in as_completed(future_to_book):
            book = future_to_book[future]
            try:
                future.result()
            except Exception as exc:
                logging.error(f"Erreur lors de l'indexation du livre {book.title} (ID: {book.id}): {exc}")
    
    logging.info("Indexation des livres terminée.")

if __name__ == "__main__":
    index_books_concurrently()
