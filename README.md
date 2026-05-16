# 📞 Piper + Voximplant — Исходящие звонки с голосом ИИ

Этот проект позволяет автоматически **звонить на телефонный номер и воспроизводить любой текст голосом**. Вы отправляете запрос с текстом и номером телефона — сервер синтезирует речь через Piper (открытый TTS) и запускает звонок через Voximplant.

---

## Как это работает

```
Ваш запрос (текст + номер)
        ↓
  FastAPI сервер
        ↓
  Piper — текст → WAV файл
        ↓
  Загрузка WAV на GitHub
        ↓
  Voximplant звонит на номер
        ↓
  Абонент слышит голос
```

---

## Что нужно перед началом

- **Python 3.9+** — язык программирования ([скачать](https://python.org))
- **Аккаунт Voximplant** — телефония ([зарегистрироваться](https://voximplant.com))
- **Аккаунт GitHub** — для хранения аудиофайлов
- **SSH** — для публичного доступа к серверу (встроен в macOS/Linux)

---

## Шаг 1 — Скачать проект

```bash
git clone https://github.com/ML-Lord/tts-audio.git
cd tts-audio
```

---

## Шаг 2 — Установить зависимости Python

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

---

## Шаг 3 — Скачать голосовую модель Piper

Модель не включена в репозиторий из-за большого размера (~61 МБ). Скачайте вручную:

```bash
mkdir -p models

# Русский голос "Ирина"
curl -L -o models/ru_RU-irina-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx

curl -L -o models/ru_RU-irina-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx.json
```

Другие голоса можно найти на [huggingface.co/rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices).

---

## Шаг 4 — Настроить Voximplant

### 4.1 Создать приложение
1. Зайдите на [manage.voximplant.com](https://manage.voximplant.com)
2. **Applications** → **+ New application** → придумайте имя (например `testtts`)

### 4.2 Создать сценарий
1. Откройте своё приложение → вкладка **Scenarios**
2. **+ New scenario** → назовите `outbound_tts`
3. Вставьте содержимое файла `voximplant_scenario.js` → **Save**

### 4.3 Создать правило маршрутизации
1. Вкладка **Routing** → **+ New rule**
2. Имя: `outbound_rule`, шаблон: `.*`
3. В поле Scenarios выберите `outbound_tts` → **Save**
4. Запомните **ID правила** — он виден в таблице

### 4.4 Получить API ключ
1. **Settings** (шестерёнка) → **API access** → **+ Add**
2. Права: `manage scenarios` → создайте и скопируйте ключ

### 4.5 Узнать ID аккаунта
Виден в правом верхнем углу панели Voximplant или в URL после входа.

---

## Шаг 5 — Настроить GitHub для хранения аудио

Voximplant скачивает аудиофайл с публичного URL. Самый надёжный способ — GitHub.

1. Создайте **публичный** репозиторий на GitHub (например `tts-audio`)
2. **Settings** → **Developer settings** → **Personal access tokens (classic)**
3. **Generate new token** → выберите scope **`repo`** → скопируйте токен

---

## Шаг 6 — Создать файл настроек

Скопируйте шаблон и заполните своими данными:

```bash
cp .env.example .env
```

Откройте `.env` и заполните:

```env
# Публичный URL вашего сервера (при использовании туннеля — адрес туннеля)
PUBLIC_BASE_URL=https://ваш-адрес.example.com

# Путь к голосовой модели
PIPER_MODEL=./models/ru_RU-irina-medium.onnx

# Voximplant — найдите в панели управления
VOXIMPLANT_ACCOUNT_ID=1234567
VOXIMPLANT_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
VOXIMPLANT_RULE_ID=1234567

# GitHub — для хранения аудиофайлов
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=ваш-логин/tts-audio
```

> ⚠️ **Никогда не публикуйте `.env` файл** — он содержит секретные ключи.

---

## Шаг 7 — Запустить сервер

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Вы увидите:
```
INFO:     Application startup complete.
```

---

## Шаг 8 — Открыть публичный доступ к серверу

Voximplant должен скачать аудиофайл с вашего сервера. Для локальной разработки используйте SSH-туннель:

```bash
# В отдельном терминале:
ssh -R 80:localhost:8000 nokey@localhost.run
```

Туннель выдаст адрес вида `https://xxxx.lhr.life`.
Скопируйте его и обновите `PUBLIC_BASE_URL` в `.env`, затем перезапустите сервер.

> **Важно:** при каждом перезапуске туннеля адрес меняется — нужно обновлять `.env`.

---

## Шаг 9 — Сделать звонок

### Звонок на SIP (бесплатно, для тестирования)

Установите приложение **Zoiper** на телефон, войдите с учётными данными Voximplant:
- Username: `ваш_пользователь`
- Domain: `ваше_приложение.ваш_аккаунт.voximplant.com`
- Password: пароль пользователя Voximplant

```bash
curl -X POST http://localhost:8000/calls \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "пользователь@приложение.аккаунт.voximplant.com",
    "caller_id": "пользователь@приложение.аккаунт.voximplant.com",
    "text": "Привет! Это автоматический звонок."
  }'
```

### Звонок на реальный номер телефона

Для звонков на реальные номера нужен купленный номер Voximplant (раздел **Numbers** в панели):

```bash
curl -X POST http://localhost:8000/calls \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "+79001234567",
    "caller_id": "+7НОМЕРвVoximplant",
    "text": "Добрый день! Это автоматическое уведомление."
  }'
```

---

## Проверка работы

```bash
# Сервер живой?
curl http://localhost:8000/health
# Ответ: {"status":"ok"}
```

---

## Возможные проблемы

| Проблема | Решение |
|---|---|
| `Piper executable not found` | Убедитесь что виртуальное окружение активировано: `source .venv/bin/activate` |
| `Missing required custom data` | В сценарии Voximplant используется старый код — вставьте заново содержимое `voximplant_scenario.js` |
| `User not found` (480) | Zoiper не подключён — проверьте зелёный статус Registered |
| `Error 502/503` при воспроизведении | Voximplant не может скачать файл — настройте GitHub хранилище |
| Звонок проходит, но тишина | Voximplant не скачал аудио — проверьте `GITHUB_TOKEN` и `GITHUB_REPO` в `.env` |

---

## Структура проекта

```
.
├── app/
│   ├── config.py          # Настройки из .env
│   ├── main.py            # FastAPI маршруты
│   ├── models.py          # Валидация запросов
│   ├── piper.py           # Синтез речи через Piper
│   └── voximplant.py      # Клиент Voximplant API
├── generated_audio/       # Сгенерированные WAV файлы
├── models/                # Голосовые модели Piper (не в git)
├── voximplant_scenario.js # Сценарий VoxEngine
├── .env.example           # Шаблон настроек
├── requirements.txt       # Зависимости Python
└── README.md
```

---

## Лицензия

MIT
