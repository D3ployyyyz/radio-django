import os
import random
import time
import requests
import subprocess
import json
from datetime import datetime, timedelta
from threading import Thread, Lock

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

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
        'outtmpl': os.path.join(output_dir, sanitized + '.%(ext)s'),
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        # evita cache para garantir sempre download atualizado
        'cachedir': False,
    }

    queries = [
        f"{music_name} {artist_name} official music video",
        f"{music_name} {artist_name} official audio",
        f"{music_name} {artist_name}"
    ]

    for query in queries:
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                if 'entries' in info and info['entries']:
                    video = info['entries'][0]
                    # caminho do arquivo mp3 esperado
                    expected_file = os.path.join(output_dir, sanitized + '.mp3')
                    if os.path.exists(expected_file):
                        result_container["path"] = expected_file
                        return True
                    else:
                        # remove arquivos de outras extensões baixados para evitar confusão
                        for ext in ['.webm', '.m4a', '.opus', '.mp4']:
                            f = os.path.join(output_dir, sanitized + ext)
                            if os.path.exists(f):
                                os.remove(f)
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
        cmd = [
            'ffprobe', '-v', 'error',
            '-print_format', 'json',
            '-show_entries', 'format=duration',
            audio_path
        ]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(p.stdout)
        duration = float(info['format']['duration'])
        if duration < 1.0:
            raise ValueError("Duração inválida")
        return duration
    except Exception as e:
        print(f"[ERRO] obter_duracao_arquivo: {e} - arquivo: {audio_path}")
        return 180.0  # fallback padrão

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

        # Checar se vinheta existe
        if not os.path.exists(vinheta_path):
            print(f"[ERRO] Vinheta não encontrada: {vinheta_path}")
            time.sleep(5)
            continue

        with status_lock:
            status_data.update({
                "tipo": "vinheta",
                "url": f"static/{vinheta_rel}",
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
                "url": f"static/musicas/{os.path.basename(music_path)}",
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

thread_radio = Thread(target=ciclo_cronograma, daemon=True)
thread_radio.start()
