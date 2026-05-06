#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/smart_house}"

echo "== Py Smart Home Raspberry Pi setup =="
echo "Project directory: $PROJECT_DIR"

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This script is intended for Raspberry Pi OS / Debian / Ubuntu with apt."
  exit 1
fi

echo "== Installing system packages =="
sudo apt-get update
sudo apt-get install -y \
  bluez \
  pi-bluetooth \
  alsa-utils \
  pulseaudio-utils \
  curl \
  git

if ! command -v docker >/dev/null 2>&1; then
  echo "== Installing Docker =="
  curl -fsSL https://get.docker.com | sh
fi

echo "== Installing Docker Compose plugin =="
sudo apt-get install -y docker-compose-plugin

echo "== Enabling services =="
sudo systemctl enable --now bluetooth
sudo systemctl enable --now docker

echo "== Allowing current user to run Docker =="
sudo usermod -aG docker "$USER" || true

if [ -d "$PROJECT_DIR/.git" ]; then
  echo "== Updating project =="
  git -C "$PROJECT_DIR" pull --ff-only || true
else
  echo "== Project directory does not look like a git checkout =="
  echo "Expected: $PROJECT_DIR/.git"
  echo "Clone it first:"
  echo "  git clone https://github.com/Fil-web/smart_house.git $PROJECT_DIR"
  exit 1
fi

echo "== Starting smart home server =="
cd "$PROJECT_DIR"
sudo docker compose up -d --build

echo "== Status =="
sudo docker compose ps
curl -fsS http://localhost:8000/api/health || true
echo

cat <<'NEXT'

Setup finished.

Open the panel from another device in the same network:
  http://<raspberry-ip>:8000

To pair Yandex Alice as a Bluetooth speaker:
  1. Say: "Алиса, включи Bluetooth"
  2. Run: python3 scripts/alice_speaker.py scan
  3. Run: python3 scripts/alice_speaker.py pair AA:BB:CC:DD:EE:FF
  4. Run: python3 scripts/alice_speaker.py test

If Docker still asks for sudo, log out and log back in once.
NEXT
