# serializers.py
from rest_framework import serializers
from .models import Author, Book, Index

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'birth_year', 'death_year']

class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True)
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'authors', 'language', 'description', 'subjects', 'bookshelves', 'cover_image', 'download_count', 'copyright', 'text_content']

class IndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = Index
        fields = ['id', 'word', 'book', 'occurrences_count','positions']
