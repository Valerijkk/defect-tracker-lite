## Defect Tracker Lite

### 1 Контекст (C1)

```mermaid
flowchart LR
    engineer([Инженер]) --> ui[React SPA]
    manager([Менеджер]) --> ui
    ui --> api[Flask API (Defects)]
    api --> db[(SQLite: app.db)]
    subgraph Домены
      auth[[Users/Auth]]
      projects[[Projects]]
      defects[[Defects]]
      reports[[Reports (calc)]]
    end
    api --- auth
    api --- projects
    api --- defects
    api --- reports
```

### 2 Слои/Компоненты (C2)

```mermaid
flowchart TB
    subgraph Client[Клиент]
      UI[React SPA / Router / Fetch]
    end
    subgraph Server[Сервер: Flask]
      Controllers[Blueprints / Controllers]
      Services[Business Logic: SLA, Status Flow]
      Repos[Repositories (SQLAlchemy)]
    end
    DB[(SQLite: app.db)]
    UI --> Controllers
    Controllers --> Services
    Services --> Repos
    Repos --> DB
```

### 3 ER-диаграмма (таблицы и связи)

```mermaid
erDiagram
    USERS ||--o{ PROJECTS : manages
    PROJECTS ||--o{ DEFECTS : contains
    USERS ||--o{ DEFECTS : assigned_to
    DEFECTS ||--o{ COMMENTS : discussed_in

    USERS {
      int id PK
      string email
      string password_hash
      string role  // engineer|manager|viewer
    }
    PROJECTS {
      int id PK
      string name
      string code
      datetime created_at
    }
    DEFECTS {
      int id PK
      int project_id FK
      string title
      string status   // new|in_work|in_review|done|cancelled
      string priority // low|medium|high
      int assignee_id FK
      datetime created_at
      datetime updated_at
    }
    COMMENTS {
      int id PK
      int defect_id FK
      int author_id FK
      string body
      datetime created_at
    }
```

**Список таблиц (минимум):** `users`, `projects`, `defects`, `comments`.
**Отчёты** (`reports`) — вычисляемые выборки/вьюхи (по проектам, статусам, приоритетам).