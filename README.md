# Py Smart Home

Минимальный сервер умного дома для Raspberry Pi: HTTP API, веб-панель, SQLite-хранилище и консольный клиент.

## Запуск на Raspberry Pi

1. Установить Docker и Compose plugin.
2. Скопировать проект на Raspberry Pi.
3. Запустить:

```bash
docker compose up -d --build
```

Автоматическая настройка Raspberry Pi:

```bash
chmod +x scripts/setup_raspberry.sh
./scripts/setup_raspberry.sh
```

Панель будет доступна по адресу:

```text
http://<ip-raspberry-pi>:8000
```

## Консольные команды

Список устройств:

```bash
python3 -m app.cli --url http://localhost:8000 devices
```

Включить устройство:

```bash
python3 -m app.cli --url http://localhost:8000 set hall_light power true
```

Запустить сцену:

```bash
python3 -m app.cli --url http://localhost:8000 run-scene evening
```

## API

- `GET /api/health`
- `GET /api/devices`
- `PATCH /api/devices/{device_id}` with `{"state": {"power": true}}`
- `GET /api/scenes`
- `POST /api/scenes/{scene_id}/run`
- `GET /api/events`

## Данные

Состояние хранится в SQLite внутри Docker volume `smart_home_data`, поэтому переживает перезапуск контейнера.

## Яндекс Алиса как Bluetooth-колонка

Скрипт запускается на Raspberry Pi хосте, не внутри Docker-контейнера, потому что Bluetooth и звук управляются системой.

Установить системные утилиты:

```bash
sudo apt update
sudo apt install -y bluez alsa-utils pulseaudio-utils
sudo systemctl enable --now bluetooth
```

Перевести Яндекс Станцию/Алису в режим Bluetooth-сопряжения. Обычно можно сказать:

```text
Алиса, включи Bluetooth
```

Найти колонку:

```bash
python3 scripts/alice_speaker.py scan
```

Подключить по MAC-адресу из вывода сканирования:

```bash
python3 scripts/alice_speaker.py pair AA:BB:CC:DD:EE:FF
```

Проверить звук:

```bash
python3 scripts/alice_speaker.py test
```

Если колонка уже была сопряжена:

```bash
python3 scripts/alice_speaker.py connect AA:BB:CC:DD:EE:FF
```

## Следующий практичный шаг

Подключить реальные устройства через один из транспортов:

- MQTT: Zigbee2MQTT, ESPHome, Tasmota.
- GPIO на Raspberry Pi: реле, кнопки, простые датчики.
- HTTP-интеграции: устройства, у которых уже есть локальный REST API.
# smart_house
