from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from radio.sitemaps import StaticViewSitemap  # se você tiver isso

sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('radio.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    # outras rotas...
]
