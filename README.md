Moteur de Recherche de Livres Numériques (Backend)
Ce projet constitue le cœur d'un moteur de recherche de livres numériques. Développé en Python et Django, il permet d'indexer et de rechercher le contenu textuel des livres ainsi que de récupérer leurs métadonnées (titre, auteurs, description, sujets, rayons, image de couverture, nombre de téléchargements, statut de copyright, contenu intégral, etc.).

Le backend expose une API REST (documentée via drf-spectacular) qui est consommée par un frontend (Next.js) pour permettre aux utilisateurs d'effectuer des recherches avancées.

Table des Matières
Fonctionnalités
Technologies Utilisées
Installation et Configuration
Démarrage du Projet
API
Configuration CORS
Contribuer
Licence
Fonctionnalités
Indexation des livres
Traitement et indexation du contenu textuel des livres pour optimiser les recherches par mots-clés et expressions régulières.

Recherche avancée
Recherche des livres via une API REST avec filtrage et classement des résultats.

Récupération complète des métadonnées
Pour chaque livre, le backend renvoie des informations telles que :

Titre, auteurs, et description
Sujets et rayons
Image de couverture (URL)
Nombre de téléchargements
Statut de copyright
Contenu intégral du livre
Documentation API
La documentation est générée automatiquement via drf-spectacular.

Support CORS
Configuration de django-cors-headers pour autoriser les requêtes depuis le frontend.

Technologies Utilisées
Langage et Framework : Python, Django, Django REST Framework
Indexation et Traitement de Texte : NLTK
Base de Données : PostgreSQL (possibilité d'utilisation via Docker)
Documentation API : drf-spectacular
Gestion des Requêtes Cross-Origin : django-cors-headers
Installation et Configuration
1. Cloner le Dépôt
bash
Copier
git clone Moteur de Recherche
cd Backend
2. Créer un Environnement Virtuel
bash
Copier
python -m venv env
source env/bin/activate  # Sous Windows : env\Scripts\activate
3. Installer les Dépendances
bash
Copier
pip install -r requirements.txt
4. Configuration de la Base de Données
Vous pouvez utiliser une instance locale de PostgreSQL ou lancer une instance via Docker. Un exemple de fichier docker-compose.yml est fourni ci-dessous :

yaml
Copier
version: '3.8'

services:
  db:
    image: postgres:14
    restart: always
    environment:
      POSTGRES_DB: library
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
5. Mise à Jour des Paramètres
Dans le fichier settings.py :

Configurez la base de données selon vos besoins.
Le CORS est configuré avec django-cors-headers pour autoriser toutes les origines en développement (voir Configuration CORS).
Démarrage du Projet
Appliquer les Migrations
bash
Copier
python manage.py migrate
Lancer le Serveur de Développement
bash
Copier
python manage.py runserver
Le backend sera disponible par défaut sur http://127.0.0.1:8000.

API
Recherche de Livres
Endpoint : /book/books
Paramètre : search (ex. /book/books?search=alice)
Réponse : Un objet JSON structuré comme suit :
json
Copier
{
  "count": 117,
  "next": "http://localhost:8000/book/books/?page=2&search=alice",
  "previous": null,
  "results": [
    {
      "id": 26184,
      "title": "Simple Sabotage Field Manual",
      "authors": ["..."],
      "language": "en",
      "description": "...",
      "subjects": ["..."],
      "bookshelves": ["..."],
      "cover_image": "https://www.gutenberg.org/cache/epub/26184/pg26184.cover.medium.jpg",
      "download_count": 123,
      "copyright": false,
      "text_content": "..."
    },
    // ...
  ]
}
Documentation API
La documentation générée via drf-spectacular est accessible à l'URL configurée (ex. /schema/ ou /docs/, selon votre configuration).

Configuration CORS
Le projet utilise django-cors-headers pour autoriser les requêtes cross-origin. En développement, la configuration suivante est utilisée dans settings.py :

python
Copier
CORS_ALLOW_ALL_ORIGINS = True
En production, pensez à restreindre cette autorisation avec la variable CORS_ALLOWED_ORIGINS.

Contribuer
Les contributions sont les bienvenues ! Pour contribuer :

Forkez ce dépôt.
Créez une branche pour votre fonctionnalité (git checkout -b feature/ma-fonctionnalité).
Commitez vos modifications.
Ouvrez une Pull Request.
Licence
Ce projet est sous licence MIT.

