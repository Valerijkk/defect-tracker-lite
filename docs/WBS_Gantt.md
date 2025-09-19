# WBS & Gantt

- Аналитика: SRS, UseCases, ERD, риски
- Бэк: JWT, фильтры, upload, отчёты, логи, backup
- Фронт: загрузка файла, фильтры, карточки
- Тесты/CI: pytest + GitHub Actions
- Эксплуатация: README

```mermaid
gantt
    title Defect Tracker Lite — План
    dateFormat  YYYY-MM-DD
    section Аналитика
    SRS/Диаграммы         :a1, 2025-09-19, 1d
    section Разработка
    API/Фильтры/Upload    :a2, 2025-09-20, 1d
    Reports/Logs/Backup   :a3, 2025-09-20, 0.5d
    section UI
    Фильтры/Вложения UI   :a4, 2025-09-20, 0.5d
    section Тесты/CI
    Pytest + CI           :a5, 2025-09-21, 0.5d
```