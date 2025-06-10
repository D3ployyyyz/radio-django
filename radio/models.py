# radio/models.py
from django.db import models
from django.utils import timezone

# models.py
from django.db import models

class Comentario(models.Model):
    texto = models.TextField()
    pontos = models.IntegerField(default=0)
    data_criacao = models.DateTimeField(auto_now_add=True)
