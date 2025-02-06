from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=200)
    birth_year = models.IntegerField(null=True, blank=True)
    death_year = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'book'


class Book(models.Model):
    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author)
    language = models.CharField(max_length=100)  # Langue sous forme de chaîne séparée par des virgules
    description = models.TextField(null=True, blank=True)
    subjects = models.TextField(null=True, blank=True)
    bookshelves = models.TextField(null=True, blank=True)
    cover_image = models.URLField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    copyright = models.BooleanField(default=False)
    text_content = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title

    def get_languages(self):
        """Retourne les langues sous forme de liste."""
        return [lang.strip() for lang in self.language.split(",")]

    def set_languages(self, langs):
        """Met à jour le champ language avec une liste de langues."""
        self.language = ", ".join(langs)

    class Meta:
        app_label = 'book'


class Index(models.Model):
    word = models.CharField(max_length=255, db_index=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, db_index=True)
    occurrences_count = models.IntegerField()

    class Meta:
        unique_together = ('word', 'book')

    def __str__(self):
        return f"{self.word} in {self.book.title}"
