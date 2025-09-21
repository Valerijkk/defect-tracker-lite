# SRS — Defect Tracker Lite

## 1. Цель
Мини-реестр дефектов по проектам: авторизация, создание и фильтрация дефектов, простые отчёты.

## 2. Роли
- **manager** — полные права, может создавать проекты.
- **engineer** — работа с дефектами (создание/обновление), просмотр проектов.

## 3. Функциональные требования (FR)
- FR-1: Логин (JWT).
- FR-2: Список проектов (GET), создание проектов (POST, manager).
- FR-3: CRUD дефектов: create (POST), update (PATCH).
- FR-4: Фильтры дефектов по `project_id`, `status`, `priority`, `q`, `date_from`, `date_to`.
- FR-5: Прикрепление файла (png/jpg/webp/pdf).
- FR-6: Отчёты: сводка по статусам/приоритетам.
- FR-7: Health-check.

## 4. Нефункциональные (NFR)
- NFR-1: Запуск локально в 2 шага (зелёная кнопка / `npm start`).
- NFR-2: Логирование с ротацией (1МБ×5).
- NFR-3: Ограничение размера/типов вложений.
- NFR-4: Тестируемость: pytest + CI.
- NFR-5: Масштабирование: перенос хранилища файлов и БД.

## 5. User Stories
- US-1: Как инженер, хочу быстро отфильтровать дефекты по проекту и статусу.
- US-2: Как инженер, хочу прикрепить файл к дефекту.
- US-3: Как менеджер, хочу создать проект и увидеть сводку по статусам.

## 6. Трассировка требований
| ID  | Эндпоинт/Экран     | Тест/Проверка                 |
|-----|---------------------|-------------------------------|
| FR-1| /api/auth/login     | test_login_ok_and_bad         |
| FR-2| /api/projects       | test_projects_role_access     |
| FR-3| /api/defects POST   | test_defect_create_and_filters|
| FR-4| /api/defects GET    | test_defect_create_and_filters|
| FR-5| /api/upload         | ручной smoke (UI)             |
| FR-6| /api/reports/summary| test_report_summary           |
| FR-7| /api/health         | test_health                   |

## 7. Риски и приоритет
- R1: Потеря/коррупция SQLite → `backup.py`. **Высокий**.
- R2: Нежелательные вложения → ALLOWED_EXT + MAX_CONTENT_LENGTH. **Средний**.
- R3: Рост данных → Postgres + хранилище файлов (S3/NAS). **Средний**.
- R4: Ошибки доступа → JWT, роль manager на POST /projects. **Средний**.

Приоритет: P0=FR-1..4, P1=FR-5..6, P2=FR-7.
