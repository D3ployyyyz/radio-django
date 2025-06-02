#!/bin/bash
set -e

# Instalar unzip e curl se ainda não estiverem disponíveis
apt-get update && apt-get install -y unzip curl

# Criar pasta temporária para os binários
mkdir -p bin
cd bin

# Baixar o FFmpeg estático (exemplo: versão Linux 64 bits)
curl -L -o ffmpeg-release.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz

# Extrair os arquivos
tar -xf ffmpeg-release.tar.xz
cd ffmpeg-*-static

# Mover apenas os binários necessários
cp ffmpeg ffprobe ../../bin/

cd ../..
rm -rf bin/ffmpeg-*-static ffmpeg-release.tar.xz

# Tornar executáveis
chmod +x bin/ffmpeg bin/ffprobe

echo "FFmpeg instalado com sucesso em ./bin"
