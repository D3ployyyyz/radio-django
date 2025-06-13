#!/bin/bash
set -e  # Para o script em qualquer erro

echo "🔧 Instalando dependências Python..."
pip install -r requirements.txt
pip install -U yt-dlp

echo "🗃️ Aplicando migrations do Django..."
python manage.py migrate

echo "📦 Instalando unzip e curl (caso necessário)..."
apt-get update && apt-get install -y unzip curl

echo "🎞️ Instalando FFmpeg (versão estática)..."
FFMPEG_DIR="bin"
mkdir -p "$FFMPEG_DIR"
cd "$FFMPEG_DIR"

curl -L -o ffmpeg-release.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release.tar.xz
cd ffmpeg-*-static

cp ffmpeg ffprobe ../../"$FFMPEG_DIR"/
cd ../..
rm -rf "$FFMPEG_DIR"/ffmpeg-*-static "$FFMPEG_DIR"/ffmpeg-release.tar.xz

chmod +x "$FFMPEG_DIR"/ffmpeg "$FFMPEG_DIR"/ffprobe
echo "✅ FFmpeg instalado com sucesso em ./$FFMPEG_DIR"

echo "🍪 Verificando cookies do YouTube..."
COOKIE_FILE="./cookies.txt"
if [ ! -f "$COOKIE_FILE" ]; then
  echo "❌ Erro: arquivo de cookies não encontrado em $COOKIE_FILE"
  echo "💡 Exporte os cookies do YouTube com uma extensão de navegador (ex: Get cookies.txt) e salve como 'cookies.txt' na raiz do projeto."
  exit 1
fi
echo "✅ cookies.txt encontrado."

if [ -n "$VIDEO_URL" ]; then
  echo "📥 Baixando vídeo/música de: $VIDEO_URL"
  yt-dlp --cookies "$COOKIE_FILE" "$VIDEO_URL" \
    -o "media/%(title)s.%(ext)s" \
    --no-check-certificate

  echo "✅ Download concluído com sucesso."
else
  echo "ℹ️ Nenhuma variável de ambiente VIDEO_URL definida. Pulando etapa de download."
fi
