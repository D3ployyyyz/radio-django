from django.contrib import admin
from django.urls import path
from radio import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # página inicial, exemplo
    path('status', views.rota_status, name='status'),  # sua rota /status
]