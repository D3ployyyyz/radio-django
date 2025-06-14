# radio_django/urls.py
from django.contrib import admin
from django.urls import path, include   # ← importe include()

urlpatterns = [
    path('admin/', admin.site.urls),
    # monta todas as URLs definidas em radio/urls.py na raiz "/"
    path('', include('radio.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),  # ← aqui
]
