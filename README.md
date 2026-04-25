# NLP Platform — MVP

Веб-платформа для анализа документации ИТ-проектов. Дипломная работа.

## Запуск (Docker)

```bash
cp .env.example .env
docker compose up -d --build
```

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8080/api/v1
- **Health check:** http://localhost:8080/health

## Разработка (локально)

### Backend

```bash
cd backend
export POSTGRES_DSN="postgres://nlp_user:nlp_pass@localhost:5432/nlp_platform?sslmode=disable"
go run ./cmd/server
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

> Vite автоматически проксирует `/api` → `http://localhost:8080`

### База данных (только PostgreSQL)

```bash
docker compose up postgres -d
```

## Структура проекта

```
nlp-platform/
├── backend/
│   ├── cmd/server/main.go          # точка входа
│   ├── internal/
│   │   ├── domain/                 # сущности и интерфейсы
│   │   ├── repository/postgres/    # реализация репозиториев
│   │   ├── service/                # бизнес-логика (mock NLP)
│   │   ├── handler/                # HTTP хендлеры
│   │   └── router/                 # маршрутизация (Chi)
│   ├── migrations/                 # SQL миграции + seed-данные
│   └── pkg/                        # config, db
└── frontend/
    └── src/
        ├── api/                    # axios клиенты
        ├── hooks/                  # кастомные хуки
        ├── components/             # компоненты (layout, ui, domain)
        ├── pages/                  # страницы
        └── styles/index.css        # дизайн-система
```

## API

| Метод  | Endpoint                                       | Описание              |
|--------|------------------------------------------------|-----------------------|
| GET    | `/api/v1/projects`                             | Список проектов       |
| POST   | `/api/v1/projects`                             | Создать проект        |
| GET    | `/api/v1/projects/:id`                         | Детали проекта        |
| PUT    | `/api/v1/projects/:id`                         | Обновить проект       |
| DELETE | `/api/v1/projects/:id`                         | Удалить проект        |
| GET    | `/api/v1/projects/:id/documents`               | Документы проекта     |
| POST   | `/api/v1/projects/:id/documents`               | Добавить документ     |
| GET    | `/api/v1/documents/:id`                        | Просмотр документа    |
| DELETE | `/api/v1/documents/:id`                        | Удалить документ      |
| GET    | `/api/v1/projects/:id/predictions`             | Прогнозы проекта      |
| POST   | `/api/v1/projects/:id/predictions/generate`    | Запустить анализ      |
