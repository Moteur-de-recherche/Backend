# MyGutenberg

MyGutenberg est un projet de gestion de livres avec des fonctionnalités de recherche avancée et de surlignage des mots recherchés.

## Installation

1. Clonez le dépôt :
    ```sh
    git clone https://github.com/votre-utilisateur/MyGutenberg.git
    cd MyGutenberg
    ```

2. Créez et activez un environnement virtuel :
    ```sh
    python3 -m venv myenv
    source myenv/bin/activate  # Sur Windows, utilisez `myenv\Scripts\activate`
    ```

3. Installez les dépendances :
    ```sh
    pip install -r requirements.txt
    ```

4. Appliquez les migrations :
    ```sh
    python manage.py makemigrations book
    python manage.py migrate
    ```

5. Démarrez le serveur de développement :
    ```sh
    python manage.py runserver
    ```

## Utilisation

### Liste des livres avec pagination

- **URL** : `/api/books/`
- **Méthode** : `GET`
- **Description** : Récupère la liste des livres avec pagination.

### Détail d'un livre

- **URL** : `/api/books/<id>/`
- **Méthode** : `GET`
- **Description** : Récupère les détails d'un livre spécifique.

### Recherche de livres

- **URL** : `/api/books/search/`
- **Méthode** : `GET`
- **Paramètre** : `q` (mot recherché) & `author`
- **Description** : Recherche des livres contenant le mot recherché dans l'index ainsi que l'auteur (non obligatoire).

### Recherche avancée de livres

- **URL** : `/api/books/advanced-search/`
- **Méthode** : `GET`
- **Paramètre** : `q` (mot recherché)
- **Description** : Recherche des livres contenant le mot recherché dans le contenu textuel et dans l'index.

### Recherche avec surlignage

- **URL** : `/api/books/highlight-search/`
- **Méthode** : `GET`
- **Paramètre** : `q` (mot recherché)
- **Description** : Recherche des livres contenant le mot recherché et surligne les mots trouvés dans le texte.

