import os
import sys
import requests
import django
import logging
from tqdm import tqdm 
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygutenberg.settings')
django.setup()

from book.models import Book, Author

# Utiliser une session pour réutiliser les connexions HTTP
session = requests.Session()

def fetch_book_text(book_data):
    """Récupère le texte intégral d'un livre et retourne son contenu avec le nombre de mots."""
    text_url = None
    possible_formats = ['text/plain', 'text/plain; charset=utf-8', 'text/plain; charset=iso-8859-1', 'text/plain; charset=us-ascii']

    for fmt in possible_formats:
        if fmt in book_data['formats']:
            text_url = book_data['formats'][fmt]
            break

    if not text_url:
        logging.warning(f"Aucun texte disponible pour le livre ID {book_data['id']}.")
        return None, 0

    try:
        response = session.get(text_url, timeout=10)
        if response.status_code == 200:
            text_content = response.text.strip()
            if not text_content:
                logging.warning(f"Le livre ID {book_data['id']} semble vide.")
                return None, 0

            word_count = len(text_content.split())
            return text_content[:100000], word_count  # Limite pour éviter les gros fichiers
    except Exception as e:
        logging.error(f"Erreur lors du téléchargement du texte du livre {book_data['id']}: {e}")

    return None, 0


def fetch_and_insert_books():
    logging.info("Début de l'importation des livres...")
    url = "https://gutendex.com/books/"
    total_books_fetched = 0
    max_books = 200

    response = session.get(url)
    if response.status_code == 200:
        data = response.json()
        total_books_to_fetch = data.get('count', 0)
    else:
        logging.error(f"Échec de récupération du nombre total de livres : {response.status_code}")
        return

    with tqdm(total=min(total_books_to_fetch, max_books), desc="Importing books") as pbar, ThreadPoolExecutor(max_workers=5) as executor:
        while url and total_books_fetched < max_books:
            logging.info(f"Récupération des livres depuis {url}")
            response = session.get(url)

            if response.status_code == 200:
                data = response.json()
                books_data = data.get('results', [])

                futures = {executor.submit(fetch_book_text, book_data): book_data for book_data in books_data}

                for future in as_completed(futures):
                    book_data = futures[future]
                    try:
                        book_text, word_count = future.result()

                        if not book_text or word_count < 10000:
                            logging.info(f"Livre ignoré : {book_data['title']} (ID: {book_data['id']}), {word_count} mots.")
                            continue

                        with transaction.atomic():
                            book, created = Book.objects.get_or_create(
                                id=book_data['id'],
                                defaults={
                                    'title': book_data['title'],
                                    'language': ', '.join(book_data['languages']),
                                    'description': book_data.get('summaries', [''])[0] if book_data.get('summaries') else '',
                                    'subjects': ', '.join(book_data.get('subjects', [])),
                                    'bookshelves': ', '.join(book_data.get('bookshelves', [])),
                                    'cover_image': book_data['formats'].get('image/jpeg', ''),
                                    'download_count': book_data['download_count'],
                                    'copyright': book_data.get('copyright', False),
                                    'text_content': book_text
                                }
                            )

                            if created:
                                logging.info(f"Livre importé : {book.title} (ID: {book.id}) - {word_count} mots.")

                            for author_data in book_data.get('authors', []):
                                author, _ = Author.objects.get_or_create(
                                    name=author_data['name'],
                                    defaults={
                                        'birth_year': author_data.get('birth_year'),
                                        'death_year': author_data.get('death_year')
                                    }
                                )
                                book.authors.add(author)

                        pbar.update(1)
                        total_books_fetched += 1

                    except Exception as e:
                        logging.error(f"Erreur lors de l'insertion du livre ID {book_data['id']}: {e}")

                url = data.get('next')
                logging.info(f"Livres récupérés jusqu'ici : {total_books_fetched}")
            else:
                logging.error(f"Échec de récupération des livres : {response.status_code}")
                break

fetch_and_insert_books()
