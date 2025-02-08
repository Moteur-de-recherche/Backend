#!/usr/bin/env python
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import sys
import os
import django
import nltk
import time
import re
from collections import Counter
from django.db import transaction, connection
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from tqdm import tqdm

# Configuration de la journalisation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration de Django
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygutenberg.settings')
django.setup()

from book.models import Book, Index

# Télécharger les ressources nécessaires pour de NLTK qui est utilée pour le traitement du texte
nltk.download('stopwords')
nltk.download('punkt')

# Mapping des codes de langue vers les identifiants attendus par NLTK
LANGUAGE_MAPPING = {
    'en': 'english',
    'fr': 'french',
    'es': 'spanish',
    'de': 'german',
    'it': 'italian',
    # Ajouter d'autres langues au besoin
}

def load_stopwords(language):
    """
    Charge les stopwords pour une langue donnée.
    En cas d'absence de stopwords pour la langue demandée, on retourne les stopwords anglais par défaut.
    """
    try:
        nltk_language = LANGUAGE_MAPPING.get(language, 'english')
        if nltk_language in stopwords.fileids():
            return set(stopwords.words(nltk_language))
        else:
            raise OSError(f"Stopwords non disponibles pour la langue '{language}'.")
    except OSError:
        logging.warning(
            f"Les stopwords pour la langue '{language}' sont introuvables. "
            f"Utilisation des stopwords anglais par défaut."
        )
        return set(stopwords.words('english'))
    except Exception as e:
        logging.error(f"Erreur lors du chargement des stopwords pour '{language}': {e}")
        return set(stopwords.words('english'))

def clean_text(text):
    """
    Nettoie le texte en le mettant en minuscule et en supprimant la ponctuation
    (tout en conservant les caractères alphabétiques, y compris les lettres accentuées).
    """
    text = text.lower()
    # [\W_] remplace tout caractère non alphabétique ou le soulignement par un espace
    text = re.sub(r'[\W_]+', ' ', text)
    return text

def extract_words(text, language='english'):
    """
    Extrait les mots du texte en nettoyant le contenu et en filtrant les stopwords.
    """
    stop_words = load_stopwords(language)
    cleaned_text = clean_text(text)
    words = word_tokenize(cleaned_text)
    filtered_words = [word for word in words if word not in stop_words]
    return filtered_words

def index_book(book):
    """
    Indexe le contenu textuel d'un livre en créant des entrées dans le modèle Index.
    La fonction enregistre le temps nécessaire pour l'indexation du livre.
    """
    start_time = time.time()
    try:
        if not book.text_content:
            logging.warning(f"Aucun texte pour le livre {book.title} (ID: {book.id})")
            return

        # On récupère le code de langue (le premier si plusieurs sont renseignés)
        language = book.language.split(',')[0].strip().lower()
        logging.info(f"Langue détectée pour le livre '{book.title}': {language}")

        # Extraction et filtrage des mots
        words = extract_words(book.text_content, language)
        word_count = len(words)
        word_freq = Counter(words)

        # Insertion en base de manière atomique
        with transaction.atomic():
            index_entries = [
                Index(word=word, book=book, occurrences_count=count)
                for word, count in word_freq.items()
            ]
            Index.objects.bulk_create(index_entries, ignore_conflicts=True)
        
        # Fermeture de la connexion pour libérer les ressources
        connection.close()
        elapsed_time = time.time() - start_time
        logging.info(
            f"Indexation du livre '{book.title}' (ID: {book.id}) terminée avec "
            f"{word_count} mots indexés en {elapsed_time:.2f} secondes."
        )

    except Exception as e:
        logging.error(f"Erreur lors de l'indexation du livre {book.title} (ID: {book.id}): {e}")

def index_books_concurrently():
    """
    Récupère tous les livres ayant un contenu textuel et lance leur indexation en parallèle.
    Une barre de progression affiche l'avancement de l'indexation.
    """
    logging.info("Début de l'indexation des livres...")
    books_to_index = Book.objects.filter(text_content__isnull=False)
    future_to_book = {}

    with ThreadPoolExecutor(max_workers=2) as executor:
        for book in books_to_index:
            future_to_book[executor.submit(index_book, book)] = book

        # Affichage d'une barre de progression avec tqdm
        for future in tqdm(as_completed(future_to_book),
                           total=len(future_to_book),
                           desc="Indexation des livres"):
            book = future_to_book[future]
            try:
                future.result()  # Récupère d'éventuelles exceptions
            except Exception as exc:
                logging.error(
                    f"Erreur lors de l'indexation du livre {book.title} (ID: {book.id}): {exc}"
                )

    logging.info("Indexation des livres terminée.")

if __name__ == "__main__":
    index_books_concurrently()
