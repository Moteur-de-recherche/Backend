import os
import sys
import requests
import django
from tqdm import tqdm  # Importer tqdm pour la barre de progression

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Définir le bon paramètre pour Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygutenberg.settings')

# Initialiser Django
django.setup()

from book.models import Book, Author  # Maintenant, ça devrait fonctionner

def fetch_and_insert_books():
    url = "https://gutendex.com/books/"  # L'URL de l'API avec un paramètre de langue
    total_books_fetched = 0  # Variable pour compter le nombre total de livres récupérés
    max_books = 2500  # Limite de livres à récupérer
    total_books_to_fetch = None  # Total de livres à importer, initialement inconnu

    # Première requête pour obtenir le total de livres
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        total_books_to_fetch = data.get('count', 0)  # Nombre total de livres dans l'API
    else:
        print(f"Failed to fetch total books count: {response.status_code}")
        return

    # Calculer la limite réelle pour la barre de progression (max 2500 livres)
    total_to_progress = min(total_books_to_fetch, max_books)

    # Barre de progression globale pour l'importation des livres
    with tqdm(total=total_to_progress, desc="Importing books", ncols=100, unit="book", position=0) as pbar:
        while url and total_books_fetched < max_books:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                books_data = data.get('results', [])
                total_books_fetched += len(books_data)
                
                # Utiliser tqdm pour la mise à jour sans redessiner à chaque livre
                for book_data in books_data:
                    # Vérifier si le livre existe déjà pour éviter les doublons
                    book, created = Book.objects.get_or_create(
                        id=book_data['id'],
                        defaults={
                            'title': book_data['title'],
                            'language': ', '.join(book_data['languages']),
                            'description': book_data.get('summaries', [''])[0] if book_data.get('summaries') else '',
                            'subjects': ', '.join(book_data.get('subjects', [])),
                            'bookshelves': ', '.join(book_data.get('bookshelves', [])),
                            'url': f"https://www.gutenberg.org/ebooks/{book_data['id']}",
                            'cover_image': book_data['formats'].get('image/jpeg', ''),
                            'download_count': book_data['download_count'],
                            'copyright': book_data['copyright'] or False
                        }
                    )

                    if created:
                        print(f"Livre importé : {book.title} (ID: {book.id})")

                    # Ajouter les auteurs au livre
                    for author_data in book_data.get('authors', []):
                        author, created = Author.objects.get_or_create(
                            name=author_data['name'],
                            defaults={
                                'birth_year': author_data.get('birth_year'),
                                'death_year': author_data.get('death_year')
                            }
                        )
                        book.authors.add(author)

                    pbar.update(1)  # Mettre à jour la barre de progression pour chaque livre

                # Mettre à jour l'URL pour la page suivante
                url = data.get('next')

                # Afficher le nombre total de livres récupérés après chaque page
                print(f"Total livres récupérés jusqu'ici : {total_books_fetched}")

            else:
                print(f"Failed to fetch books: {response.status_code}")
                break

# Appeler la fonction pour insérer les livres dans la base de données
fetch_and_insert_books()
