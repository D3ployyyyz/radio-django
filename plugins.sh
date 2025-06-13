#!/bin/bash
set -e

echo "🔧 Instalando dependências Python..."
pip install -r requirements.txt
pip install -U yt-dlp

echo "🗃️ Aplicando migrations do Django..."
python manage.py migrate

echo "📦 Instalando unzip e curl..."
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

echo "✅ FFmpeg instalado em ./$FFMPEG_DIR"

echo "🍪 Verificando presença de cookies.txt (somente para downloads)..."
COOKIE_FILE="./cookies.txt"
if [ ! -f "$COOKIE_FILE" ]; then
  echo "⚠️ Aviso: cookies.txt não encontrado. Downloads protegidos podem falhar em runtime."
else
  echo "✅ cookies.txt disponível para autenticação em runtime"
fi

echo "🔄 Build completo. O processo de download de músicas ocorre em tempo de execução."
