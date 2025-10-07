### 1 Контекст (C1)

```mermaid
flowchart LR
    engineer([Инженер])
    manager([Менеджер])
    ui[React SPA]
    api[[Flask API\nDefects]]
    db[(SQLite\napp.db)]

    subgraph Domains[Домены]
        auth[[Users / Auth]]
        projects[[Projects]]
        defects[[Defects]]
        reports[[Reports (calc)]]
    end

    engineer --> ui
    manager  --> ui
    ui       --> api
    api      --> db

    api --- auth
    api --- projects
    api --- defects
    api --- reports
```

### 2 Слои/Компоненты (C2)

```mermaid
flowchart TB
    subgraph Client[Клиент]
        UI[React SPA\nRouter\nFetch]
    end

    subgraph Server[Сервер: Flask]
        Controllers[Blueprints / Controllers]
        Services[Business Logic:\nSLA, Status Flow]
        Repos[Repositories\nSQLAlchemy]
    end

    DB[(SQLite\napp.db)]

    UI --> Controllers
    Controllers --> Services
    Services --> Repos
    Repos --> DB
```

### 3 ER-диаграмма (таблицы и связи)

```mermaid
erDiagram
    USERS ||--o{ PROJECTS : "manages"
    PROJECTS ||--o{ DEFECTS : "contains"
    USERS ||--o{ DEFECTS : "assigned_to"
    DEFECTS ||--o{ COMMENTS : "discussed_in"

    USERS {
      int id PK
      string email
      string password_hash
      string role
    }

    PROJECTS {
      int id PK
      string name
      string code
      string created_at
    }

    DEFECTS {
      int id PK
      int project_id FK
      string title
      string status
      string priority
      int assignee_id FK
      string created_at
      string updated_at
    }

    COMMENTS {
      int id PK
      int defect_id FK
      int author_id FK
      string body
      string created_at
    }
```
