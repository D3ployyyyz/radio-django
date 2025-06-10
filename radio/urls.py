import os
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('status/', views.rota_status, name='rota_status'),
    path('salvar-comentario/', views.salvar_comentario, name='salvar_comentario'),
    path('curtir-comentario/', views.curtir_comentario, name='curtir_comentario'),
    path('descurtir-comentario/', views.descurtir_comentario, name='descurtir_comentario'),
    path('comentarios-json/', views.listar_comentarios, name='listar_comentarios'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=os.path.join(settings.BASE_DIR, 'radio', 'static')
    )
