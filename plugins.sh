#!/bin/bash
set -e

# Criar pasta bin se não existir
mkdir -p bin

# Baixar ffmpeg + ffprobe
curl -L https://github.com/yt-dlp/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-linux64-gpl.zip -o ffmpeg.zip
unzip -o ffmpeg.zip
mv ffmpeg-master-latest-linux64-gpl/bin/ffmpeg ./bin/ffmpeg
mv ffmpeg-master-latest-linux64-gpl/bin/ffprobe ./bin/ffprobe
chmod +x ./bin/ffmpeg ./bin/ffprobe

# (Opcional) limpar arquivos temporários
rm -rf ffmpeg.zip ffmpeg-master-latest-linux64-gpl

# Inicia seu app
python app.py
