from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import sys
import os
import django
import nltk
from django.db import transaction
from django.db import connection
from collections import Counter
import re
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
    # Ajouter d'autres langues au besoin
}

# Fonction pour charger les stopwords en fonction de la langue
def load_stopwords(language):
    try:
        nltk_language = LANGUAGE_MAPPING.get(language, 'english')
        if nltk_language in stopwords.fileids():
            return set(stopwords.words(nltk_language))
        else:
            raise OSError(f"Stopwords non disponibles pour la langue '{language}'.")
    except OSError:
        logging.warning(f"Les stopwords pour la langue '{language}' sont introuvables. Utilisation des stopwords anglais par défaut.")
        return set(stopwords.words('english'))
    except Exception as e:
        logging.error(f"Erreur lors du chargement des stopwords pour '{language}': {e}")
        return set(stopwords.words('english'))  # Retourner l'anglais par défaut

# Nettoyage du texte
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)  # Garder uniquement les lettres et les espaces
    return text

# Extraction des mots
def extract_words(text, language='english'):
    stop_words = load_stopwords(language)
    cleaned_text = clean_text(text)
    words = word_tokenize(cleaned_text)  # Tokenisation du texte (sans spécifier language)
    filtered_words = [word for word in words if word not in stop_words]
    return filtered_words

# Fonction pour indexer un livre
def index_book(book):
    try:
        if not book.text_content:
            logging.warning(f"Aucun texte pour le livre {book.title} (ID: {book.id})")
            return

        language = book.language.split(',')[0].strip().lower()
        logging.info(f"Langue détectée pour le livre '{book.title}': {language}")
        words = extract_words(book.text_content, language)
        word_count = len(words)
        word_freq = Counter(words)

        with transaction.atomic():
            index_entries = [
                Index(word=word, book=book, occurrences_count=count)
                for word, count in word_freq.items()
            ]
            Index.objects.bulk_create(index_entries, ignore_conflicts=True)  # Insertion optimisée
            
        connection.close()
        logging.info(f"Indexation du livre '{book.title}' (ID: {book.id}) terminée avec {word_count} mots indexés.")

    except Exception as e:
        logging.error(f"Erreur lors de l'indexation du livre {book.title} (ID: {book.id}): {e}")
        
        
# Fonction principale pour indexer les livres en parallèle
def index_books_concurrently():
    logging.info("Début de l'indexation des livres...")

    # Récupérer tous les livres à indexer
    books_to_index = Book.objects.filter(text_content__isnull=False)

    # Utiliser ThreadPoolExecutor pour paralléliser l'indexation
    with ThreadPoolExecutor(max_workers=2) as executor:  # Ajuster max_workers selon ta capacité CPU
        future_to_book = {executor.submit(index_book, book): book for book in books_to_index}

        # Attendre la fin de chaque tâche et afficher les résultats
        for future in as_completed(future_to_book):
            book = future_to_book[future]
            try:
                future.result()  # Cette ligne permet de capturer les exceptions dans index_book
            except Exception as exc:
                logging.error(f"Erreur lors de l'indexation du livre {book.title} (ID: {book.id}): {exc}")
    
    logging.info("Indexation des livres terminée.")

# Exécution du script
if __name__ == "__main__":
    index_books_concurrently()
