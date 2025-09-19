# Defect Tracker Lite

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](#)
[![Flask](https://img.shields.io/badge/Flask-3.0-000?logo=flask)](#)
[![SQLite](https://img.shields.io/badge/SQLite-embedded-003B57?logo=sqlite)](#)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react\&logoColor=000)](#)
[![MUI](https://img.shields.io/badge/MUI-5-007FFF?logo=mui)](#)
[![JWT](https://img.shields.io/badge/Auth-JWT-FF6F00?logo=jsonwebtokens\&logoColor=fff)](#)

Мини-реестр дефектов для проектов: **логин → проекты → дефекты → статусы/приоритеты**.
Красивый интерфейс на MUI, простая архитектура, локальная SQLite. Запуск — в два шага.

## ✨ Что умеет

* 🧑‍💼 **Роли**: *manager* и *engineer* (менеджер может добавлять проекты)
* 🧱 **Проекты**: список и создание
* 🐞 **Дефекты**: создание, просмотр, обновление полей (title/desc/priority/status/assignee)
* 🏷️ **Статусы/приоритеты**: `new`, `in_progress`, `review`, `closed`, `cancelled` и `low/medium/high`
* 🔐 **Аутентификация**: JWT (Bearer) — минимально, но по-взрослому
* 💾 **SQLite**: база создаётся и наполняется демо-данными при первом запуске
* 🌐 **CORS** включён — фронт общается с API на `http://localhost:5000`

## 🚀 Быстрый старт

### 1) Backend (Flask + SQLite)

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python app.py

# Linux/Mac:
# source .venv/bin/activate
# pip install -r requirements.txt
# python app.py
```

> В WebStorm можно открыть `backend/app.py` и запустить **зелёной кнопкой Run** — это ок.

### 2) Frontend (React + MUI)

```bash
cd frontend
npm install
npm start
```

* API: `http://localhost:5000`
* UI:  `http://localhost:3000`

## 🔑 Демо-аккаунты

* **manager**: `admin@example.com / admin123`
* **engineer**: `eng@example.com / eng123`

## 🧱 Технологии

* **Backend**: Flask 3, Flask-SQLAlchemy 3, Flask-CORS, PyJWT
* **Frontend**: React 18 (CRA), MUI v5, Emotion, Axios
* **БД**: файл `app.db` рядом с `backend/app.py`

## 🗂️ Структура

```
defect-tracker-lite/
├─ backend/
│  ├─ app.py                # Flask-приложение: модели, эндпоинты, JWT
│  ├─ requirements.txt      # зависимости
│  ├─ .env.example          # SECRET_KEY, JWT_EXPIRES_DAYS
│  └─ app.db                # создастся на первом запуске
└─ frontend/
   ├─ package.json          # CRA + MUI + Axios
   ├─ public/index.html     # базовый HTML + шрифты
   └─ src/
      ├─ App.js             # UI: логин, фильтры, доска дефектов, диалоги
      ├─ api.js             # axios с baseURL
      ├─ theme.js           # тема (палитра/радиусы/типографика)
      └─ components/        # AppLayout, Toaster, Confirm
```

## 🔌 API (кратко)

**Аутентификация:** `Authorization: Bearer <token>`

| Метод | Путь               | Роль        | Описание                                                           |
| ----: | ------------------ | ----------- | ------------------------------------------------------------------ |
|  POST | `/api/auth/login`  | —           | Логин → `{ token, role, email }`                                   |
|   GET | `/api/projects`    | любой       | Список проектов                                                    |
|  POST | `/api/projects`    | **manager** | Создать проект: `{"name":"...", "description":"..."}`              |
|   GET | `/api/defects`     | любой       | Список дефектов (опц. `?project_id=1`)                             |
|  POST | `/api/defects`     | любой       | Создать дефект: `{"project_id":1,"title":"...","priority":"high"}` |
| PATCH | `/api/defects/:id` | любой       | Обновить поля: `title/description/priority/status/assignee_id`     |
|   GET | `/api/health`      | любой       | Пинг                                                               |

Пример:

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@example.com\",\"password\":\"admin123\"}"
```

## 🧑‍🏫 Демо-сценарий «за 30 секунд»

1. Залогинься под **manager**
2. Нажми **Новый проект**, создай «Корпус В»
3. Нажми **Новый дефект**, выбери проект, задай `priority=high`
4. Переключай табы статусов, покажи чипы приоритетов и даты
5. (Опционально) Залогинься под **engineer** и проверь доступ (без создания проектов)

## 🛠️ Полезно знать

* **Порты**: фронт `3000`, API `5000` (можно сменить `set PORT=3001 && npm start`)
* **Переменные**: см. `backend/.env.example` (`SECRET_KEY`, `JWT_EXPIRES_DAYS`)
* **Версии**: Python ≥ 3.10, Node ≥ 18 рекомендуется

## 📄 Лицензия

MIT — меняй, как требуется.