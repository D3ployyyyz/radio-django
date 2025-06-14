# radio/sitemaps.py

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    changefreq = "hourly"
    priority = 1.0

    def items(self):
        return [
            'home',
            'rota_status',
            'listar_comentarios',
            'salvar_comentario',
            'curtir_comentario',
            'descurtir_comentario',
        ]

    def location(self, item):
        return reverse(item)
