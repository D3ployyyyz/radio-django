import os
import random
import time
import requests
import json
from datetime import datetime
from threading import Thread, Lock

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from pymediainfo import MediaInfo
from .models import Comentario

# Configurações
LASTFM_API_KEY = '9d7d79a952c5e5805a0decb0ccf1c9fd'
VINHETAS = [
    "vinhetas/vinheta_milenio.mp3",
    "vinhetas/vinheta_rock.mp3",
    "vinhetas/uma_hora.mp3"
]
CRONOGRAMA = [
    {"estilo": None,               "duracao": 120,  "publico": True},
    {"estilo": "nu-metal",         "duracao": 120,  "publico": False},
    {"estilo": "metalcore",        "duracao": 120,  "publico": False},
    {"estilo": "alt-rock",         "duracao": 120,  "publico": False},
    {"estilo": "indie rock",       "duracao": 120,  "publico": False},
    {"estilo": "brazilian rock",   "duracao": 120,  "publico": False},
]

# Estado global
status_lock = Lock()
status_data = {
    "tipo": None,
    "url": None,
    "nome": None,
    "artista": None,
    "capa": None,
    "estilo": None,
    "start_time": None
}
cronograma_index = 0

# --- Views Django ---

def home(request):
    comentarios = Comentario.objects.order_by('-pontos', '-data_criacao')
    return render(request, 'radio/index.html', {'comentarios': comentarios})


def rota_status(request):
    with status_lock:
        st = status_data.copy()
    elapsed = (datetime.now() - st['start_time']).total_seconds() if st['start_time'] else 0
    return JsonResponse({
        'tipo': st['tipo'],
        'url': st['url'],
        'nome': st['nome'] or 'Desconhecido',
        'artista': st['artista'] or 'Desconhecido',
        'capa': st['capa'],
        'estilo': st['estilo'] or 'Público',
        'tempo_decorrido': elapsed
    })


def listar_comentarios(request):
    qs = Comentario.objects.order_by('-data_criacao')
    data = [{
        'id': c.id,
        'texto': c.texto,
        'pontos': c.pontos,
        'liked': c.liked
    } for c in qs]
    return JsonResponse(data, safe=False)

@csrf_exempt
def salvar_comentario(request):
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=405)
    try:
        payload = json.loads(request.body)
        texto = payload.get('texto', '').strip()
        if not texto:
            return JsonResponse({'erro': 'Comentário vazio.'}, status=400)

        comentario = Comentario.objects.filter(texto__iexact=texto).first()
        if comentario:
            comentario.pontos += 1
            comentario.save()
            return JsonResponse({'duplicado': True, 'mensagem': 'Comentário duplicado. +1 ponto.', 'points': comentario.pontos})

        comentario = Comentario.objects.create(texto=texto)
        return JsonResponse({'sucesso': True, 'id': comentario.id, 'texto': comentario.texto, 'points': comentario.pontos, 'liked': comentario.liked})
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'JSON inválido.'}, status=400)
    except Exception:
        return JsonResponse({'erro': 'Erro interno.'}, status=500)

@csrf_exempt
def curtir_comentario(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            comentario = Comentario.objects.get(id=data.get('id'))
            comentario.pontos += 1
            comentario.save()
            return JsonResponse({'status': 'ok', 'pontos': comentario.pontos})
        except Comentario.DoesNotExist:
            return JsonResponse({'status': 'erro', 'mensagem': 'Comentário não encontrado'}, status=404)

@csrf_exempt
def descurtir_comentario(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            comentario = Comentario.objects.get(id=data.get('id'))
            if comentario.pontos > 0:
                comentario.pontos -= 1
                comentario.save()
            return JsonResponse({'status': 'ok', 'pontos': comentario.pontos})
        except Comentario.DoesNotExist:
            return JsonResponse({'status': 'erro', 'mensagem': 'Comentário não encontrado'}, status=404)

# --- Auxiliares ---

def buscar_musicas_por_estilo(estilo):
    url = (
        f'http://ws.audioscrobbler.com/2.0/'
        f'?method=tag.gettoptracks'
        f'&tag={requests.utils.quote(estilo)}'
        f'&api_key={LASTFM_API_KEY}'
        f'&format=json'
    )
    try:
        resp = requests.get(url, timeout=10)
        tracks = resp.json().get('tracks', {}).get('track', [])
        return [(t['name'], t['artist']['name']) for t in tracks]
    except Exception:
        return []

def buscar_info_correta(texto):
    url = (
        f'http://ws.audioscrobbler.com/2.0/'
        f'?method=track.search'
        f'&track={requests.utils.quote(texto)}'
        f'&api_key={LASTFM_API_KEY}'
        f'&format=json'
    )
    try:
        data = requests.get(url, timeout=10).json()
        tracks = data.get('results', {}).get('trackmatches', {}).get('track', [])
        if tracks:
            top = tracks[0]
            return top.get('name', '').strip(), top.get('artist', '').strip()
    except Exception:
        pass
    if ' - ' in texto:
        a, m = texto.split(' - ', 1)
        return m.strip().title(), a.strip().title()
    return texto.strip().title(), ''

def buscar_capa_do_album(musica, artista):
    url = (
        f'http://ws.audioscrobbler.com/2.0/'
        f'?method=track.getInfo'
        f'&api_key={LASTFM_API_KEY}'
        f'&artist={requests.utils.quote(artista)}'
        f'&track={requests.utils.quote(musica)}'
        f'&format=json'
    )
    try:
        imgs = requests.get(url, timeout=10).json() \
            .get('track', {}).get('album', {}).get('image', [])
        for img in reversed(imgs):
            if img.get('#text'):
                return img['#text']
    except Exception:
        pass
    return 'https://via.placeholder.com/300?text=Sem+Capa'

def obter_duracao(path):
    try:
        media_info = MediaInfo.parse(path)
        for track in media_info.tracks:
            if track.track_type in ('Video', 'Audio') and track.duration:
                return float(track.duration) / 1000.0
    except Exception:
        pass
    return 180.0

import os
from yt_dlp import YoutubeDL
from django.conf import settings

def download_music(nome, artista, result):
    # Sanitiza nome do arquivo
    nome_seguro = f"{artista} - {nome}".translate(str.maketrans("/\\:!?\"'", "_______"))

    # Diretório de saída
    output_dir = os.path.join(settings.BASE_DIR, 'radio', 'static', 'musicas')
    os.makedirs(output_dir, exist_ok=True)

    # Caminho absoluto para cookies.txt (localizado em: radio_django/cookies.txt)
    cookie_path = os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'cookies.txt'))

    # Verifica se o arquivo de cookies existe
    if not os.path.exists(cookie_path):
        print(f"⚠️ cookies.txt não encontrado em {cookie_path}")
    
    # Consultas alternativas para melhorar a chance de encontrar o áudio
    consultas = [
        f"{nome} {artista} official audio",
        f"{nome} {artista} lyrics",
        f"{nome} {artista}"
    ]

    for consulta in consultas:
        print(f"🔎 Tentando baixar: {consulta}")
        opts = {
            'quiet': True,
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': 192,
            'nocheckcertificate': True,
            'cookiefile': cookie_path,
            'default_search': 'ytsearch',
        }

        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(consulta, download=True)
                entry = (info.get('entries') or [info])[0]
                base = os.path.splitext(ydl.prepare_filename(entry))[0]

                # Verifica os possíveis formatos baixados
                for ext in ('.mp3', '.m4a', '.webm'):
                    caminho = base + ext
                    if os.path.exists(caminho):
                        result['path'] = caminho
                        print(f"✅ Sucesso: {caminho}")
                        return True

        except Exception as e:
            print(f"❌ Erro ao baixar com query '{consulta}': {e}")

    print("⚠️ Nenhuma versão foi baixada com sucesso.")
    return False

def atualizar_status(tipo, url=None, nome=None, artista=None, capa=None, estilo=None):
    with status_lock:
        status_data.update({
            'tipo': tipo,
            'url': url,
            'nome': nome,
            'artista': artista,
            'capa': capa,
            'estilo': estilo,
            'start_time': datetime.now()
        })

def tocar_comentario_mais_votado_ou_nu_metal(duracao_total):
    inicio = time.time()
    while time.time() - inicio < duracao_total:
        comentarios = Comentario.objects.order_by('-pontos', '-data_criacao')
        if comentarios.exists():
            # Vinheta antes do comentário
            vin = random.choice(VINHETAS)
            vin_path = os.path.join(settings.BASE_DIR, 'radio', 'static', vin).replace("\\", "/")
            atualizar_status('vinheta', url=f'static/{vin}', estilo='Público')
            time.sleep(obter_duracao(vin_path))

            c = comentarios.first()
            nome, artista = buscar_info_correta(c.texto.strip())
            result = {'path': None}
            if download_music(nome, artista, result):
                capa = buscar_capa_do_album(nome, artista)
                Comentario.objects.all().delete()
                atualizar_status('musica', url=f"static/musicas/{os.path.basename(result['path'])}", nome=nome, artista=artista, capa=capa, estilo='Público')
                time.sleep(obter_duracao(result['path']))
                continue
        # Fallback nu-metal com vinheta
        vin = random.choice(VINHETAS)
        vin_path = os.path.join(settings.BASE_DIR, 'radio', 'static', vin).replace("\\", "/")
        atualizar_status('vinheta', url=f'static/{vin}', estilo='Público')
        time.sleep(obter_duracao(vin_path))

        estilo_nm = 'nu-metal'
        tracks = buscar_musicas_por_estilo(estilo_nm)
        if not tracks:
            break
        nome, artista = random.choice(tracks)
        result = {'path': None}
        if download_music(nome, artista, result):
            capa = buscar_capa_do_album(nome, artista)
            atualizar_status('musica', url=f"static/musicas/{os.path.basename(result['path'])}", nome=nome, artista=artista, capa=capa, estilo='Público')
            time.sleep(obter_duracao(result['path']))
        else:
            break

def rodar_programa(entry):
    if entry.get('publico'):
        atualizar_status('publico', nome='Escolha do público', artista='', estilo='Público')
        time.sleep(1)
        # Remove vinheta extra: ciclo_cronograma já fez
        tocar_comentario_mais_votado_ou_nu_metal(entry['duracao'] * 60)
        return

    tracks = buscar_musicas_por_estilo(entry['estilo'])
    if tracks:
        nome, artista = random.choice(tracks)
        result = {'path': None}
        if download_music(nome, artista, result):
            capa = buscar_capa_do_album(nome, artista)
            atualizar_status('musica', url=f"static/musicas/{os.path.basename(result['path'])}", nome=nome, artista=artista, capa=capa, estilo=entry['estilo'])
            time.sleep(obter_duracao(result['path']))


def ciclo_cronograma():
    global cronograma_index
    while True:
        # Vinheta entre blocos de cronograma
        vin = random.choice(VINHETAS)
        vin_path = os.path.join(settings.BASE_DIR, 'radio', 'static', vin).replace("\\", "/")
        atualizar_status('vinheta', url=f'static/{vin}', estilo='Público')
        time.sleep(obter_duracao(vin_path))

        if cronograma_index >= len(CRONOGRAMA):
            cronograma_index = 0
        entry = CRONOGRAMA[cronograma_index]
        cronograma_index += 1
        rodar_programa(entry)
        time.sleep(1)

# Inicia rádio em thread separada
thread_radio = Thread(target=ciclo_cronograma, daemon=True)
thread_radio.start()
