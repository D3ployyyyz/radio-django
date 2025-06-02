import os
import random
import time
import requests
import json
from datetime import datetime, timedelta
from threading import Thread, Lock

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from mutagen import File  # biblioteca para ler metadados de áudio sem ffmpeg

# Configurações
LASTFM_API_KEY = '9d7d79a952c5e5805a0decb0ccf1c9fd'

VINHETAS = [
    "vinhetas/vinheta_milenio.mp3",
    "vinhetas/vinheta_rock.mp3",
    "vinhetas/uma_hora.mp3"
]

CRONOGRAMA = [
    {"estilo": "brazilian rock",   "duracao": 3},
    {"estilo": "alternative rock", "duracao": 3},
    {"estilo": "metalcore",        "duracao": 3},
    {"estilo": "alt-rock",         "duracao": 3},
    {"estilo": "indie rock",       "duracao": 3},
    {"estilo": "brazilian rock",   "duracao": 3},
]

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

# Views
def home(request):
    return render(request, 'radio/index.html')

def rota_status(request):
    with status_lock:
        st = status_data.copy()

    elapsed = (datetime.now() - st["start_time"]).total_seconds() if st["start_time"] else 0

    return JsonResponse({
        "tipo": st["tipo"],
        "url": st["url"],
        "nome": st["nome"],
        "artista": st["artista"],
        "capa": st["capa"],
        "estilo": st["estilo"],
        "tempo_decorrido": elapsed
    })

# Funções Auxiliares
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
        resp.raise_for_status()
        data = resp.json()
        tracks = data.get('tracks', {}).get('track', [])
        return [(t['name'], t['artist']['name']) for t in tracks] if tracks else []
    except Exception as e:
        print(f"[ERRO] buscar_musicas_por_estilo: {e}")
        return []

def download_music(music_name, artist_name, result_container):
    from yt_dlp import YoutubeDL

    sanitized = f"{artist_name} - {music_name}"
    for c in ["/", "\\", ":", "!", "?", '"', "'"]:
        sanitized = sanitized.replace(c, "_")

    output_dir = os.path.join(settings.BASE_DIR, 'radio', 'static', 'musicas')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{sanitized}.mp3")

    if os.path.exists(output_path):
        result_container["path"] = output_path
        return True

    ydl_opts = {
        'quiet': True,
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'extractaudio': True,
        'audioformat': 'mp3',
        'audioquality': 192,
        'prefer_ffmpeg': False,  # evitar usar ffmpeg
        'nocheckcertificate': True,
    }

    queries = [
        f"{music_name} {artist_name} official music video",
        f"{music_name} {artist_name} official audio",
        f"{music_name} {artist_name}"
    ]

    for query in queries:
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=True)
                if 'entries' in info and info['entries']:
                    video = info['entries'][0]
                    temp_file = ydl.prepare_filename(video)
                    # tenta localizar arquivo com extensões comuns
                    if not os.path.exists(temp_file):
                        for ext in ['.mp3', '.m4a', '.webm']:
                            alt_file = os.path.splitext(temp_file)[0] + ext
                            if os.path.exists(alt_file):
                                temp_file = alt_file
                                break

                    # renomear para .mp3 pode ser problemático se não for mp3
                    # mas vamos salvar como está para garantir reprodução
                    result_container["path"] = temp_file
                    return True
        except Exception as e:
            print(f"[ERRO] download_music attempt '{query}': {e}")

    result_container["path"] = None
    return False

def buscar_capa_do_album(musica, artista):
    url = (
        f"http://ws.audioscrobbler.com/2.0/"
        f"?method=track.getInfo"
        f"&api_key={LASTFM_API_KEY}"
        f"&artist={requests.utils.quote(artista)}"
        f"&track={requests.utils.quote(musica)}"
        f"&format=json"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        album = data.get('track', {}).get('album', {})
        images = album.get('image', [])
        for img in reversed(images):
            if img.get('#text'):
                return img['#text']
    except Exception as e:
        print(f"[ERRO] buscar_capa_do_album: {e}")
    return "https://via.placeholder.com/300?text=Sem+Capa"

def obter_duracao_arquivo(audio_path):
    try:
        audio = File(audio_path)
        if audio is not None and audio.info is not None:
            return audio.info.length
        else:
            print(f"[ERRO] obter_duracao_arquivo: arquivo sem info de duração: {audio_path}")
            return 180.0
    except Exception as e:
        print(f"[ERRO] obter_duracao_arquivo: {e}")
        return 180.0  # duração padrão

# Lógica Principal
def rodar_programa(estilo, duracao_minutos):
    global status_data
    fim_programa = datetime.now() + timedelta(minutes=duracao_minutos)

    while datetime.now() < fim_programa:
        musicas = buscar_musicas_por_estilo(estilo)
        if not musicas:
            time.sleep(5)
            continue

        musica, artista = random.choice(musicas)
        vinheta_rel = random.choice(VINHETAS)

        cont = {"path": None}
        sucesso = download_music(musica, artista, cont)
        if not sucesso or not cont["path"]:
            print(f"[RÁDIO] Falha ao baixar '{musica}' de {artista}. Pulando...")
            time.sleep(5)
            continue

        music_path = cont["path"].replace("\\", "/")
        vinheta_path = os.path.join(settings.BASE_DIR, 'radio', 'static', vinheta_rel).replace("\\", "/")

        with status_lock:
            status_data.update({
                "tipo": "vinheta",
                "url": f"radio_django/radio/static/{vinheta_rel}",
                "nome": None,
                "artista": None,
                "estilo": estilo,
                "capa": None,
                "start_time": datetime.now(),
            })

        duracao_vinheta = obter_duracao_arquivo(vinheta_path)
        time.sleep(duracao_vinheta)

        capa_url = buscar_capa_do_album(musica, artista)

        with status_lock:
            status_data.update({
                "tipo": "musica",
                "url": f"radio_django/radio/static/musicas/{os.path.basename(music_path)}",
                "nome": musica,
                "artista": artista,
                "estilo": estilo,
                "capa": capa_url,
                "start_time": datetime.now(),
            })

        duracao_musica = obter_duracao_arquivo(music_path)
        time.sleep(duracao_musica)

def ciclo_cronograma():
    global cronograma_index
    while True:
        if cronograma_index >= len(CRONOGRAMA):
            cronograma_index = 0
        prog = CRONOGRAMA[cronograma_index]
        cronograma_index += 1
        rodar_programa(prog["estilo"], prog["duracao"])
        time.sleep(1)

# Inicializa a thread da rádio
thread_radio = Thread(target=ciclo_cronograma, daemon=True)
thread_radio.start()
