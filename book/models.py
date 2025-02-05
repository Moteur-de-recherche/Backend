from django.db import models

# Modèle pour un auteur
class Author(models.Model):
    name = models.CharField(max_length=200)
    birth_year = models.IntegerField(null=True, blank=True)
    death_year = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'book'

# Modèle pour un livre
class Book(models.Model):
    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author)
    language = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    subjects = models.TextField(null=True, blank=True)
    bookshelves = models.TextField(null=True, blank=True)
    cover_image = models.URLField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    copyright = models.BooleanField(default=False)
    text_content = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        app_label = 'book'
