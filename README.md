# DocuAudit AI — NLP Platform

> **Automated Risk & Profitability Assessment for IT Projects**

Микросервисная веб-платформа, использующая Natural Language Processing (NLP)
для анализа неструктурированной ИТ-документации, извлечения ключевых метрик
и автоматической оценки проектных рисков. Дипломная работа.

---

## Архитектура

```
┌─────────────┐     REST API      ┌──────────────┐     HTTP      ┌──────────────┐
│   React     │ ──────────────▶   │   Golang     │ ──────────▶   │   Python     │
│  Frontend   │   (JSON/JWT)      │   Backend    │               │  NLP Service │
│  Tailwind   │ ◀──────────────   │  Chi Router  │ ◀──────────   │  FastAPI     │
└─────────────┘                   └──────┬───────┘               │  RuBERT      │
                                         │                       └──────────────┘
                                         │ pgx
                                         ▼
                                  ┌──────────────┐
                                  │ PostgreSQL 16│
                                  └──────────────┘

                    ─── Всё в Docker Compose ───
```

## Быстрый старт

```bash
git clone <repo-url> && cd nlp-platform
cp .env.example .env
docker compose up -d --build
```

| Сервис | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8081/api/v1 |
| Health check | http://localhost:8081/health |
| NLP Service | http://localhost:8000/health (внутренний) |
| PostgreSQL | localhost:5433 |

## Разработка (локально)

### Backend (Go)

```bash
cd backend
export POSTGRES_DSN="postgres://nlp_user:nlp_pass@localhost:5433/nlp_platform?sslmode=disable"
go run ./cmd/server
```

### Frontend (React + Tailwind CSS)

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

> Vite автоматически проксирует `/api` → `http://localhost:8081`

### NLP Service (Python)

```bash
cd nlp-service
pip install -r requirements.txt
uvicorn main:app --port 8000
```

### База данных

```bash
docker compose up db -d   # PostgreSQL на порту 5433
```

## Структура проекта

```
nlp-platform/
├── backend/
│   ├── cmd/server/main.go              # Точка входа (zerolog)
│   ├── internal/
│   │   ├── domain/                     # Сущности и интерфейсы
│   │   ├── repository/postgres/        # Репозитории (pgx)
│   │   ├── service/                    # Бизнес-логика + NLP клиент
│   │   ├── handler/                    # HTTP хендлеры + middleware (JWT)
│   │   └── router/                     # Маршрутизация (Chi)
│   ├── migrations/                     # SQL миграции (001-003)
│   └── pkg/                            # config, db, parser
│
├── frontend/
│   └── src/
│       ├── api/                        # Axios клиенты (auth, projects, docs, predictions)
│       ├── context/AuthContext.jsx      # JWT авторизация
│       ├── hooks/                      # useProjects, useDocuments, usePredictions
│       ├── components/
│       │   ├── layout/                 # Navbar (glassmorphism), Footer
│       │   ├── auth/                   # ProtectedRoute
│       │   └── ui/                     # GaugeChart, ProjectCard, NerHighlighter,
│       │                               # FileUpload, FaqAccordion, Modal
│       └── pages/                      # 6 страниц (см. ниже)
│
├── nlp-service/
│   ├── main.py                         # FastAPI + RuBERT sentiment analysis
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
└── .env
```

## Страницы фронтенда

| Страница | Путь | Описание |
|---|---|---|
| Landing | `/` | Hero-секция, фичи, статистика, FAQ |
| Dashboard | `/dashboard` | Сетка проектов с GaugeChart (Risk / Profitability) |
| Workspace | `/workspace` | Drag&Drop загрузка, NER-подсветка, Summary |
| Architecture | `/architecture` | Визуальная схема микросервисов (для диплома) |
| Login | `/login` | Авторизация (JWT) |
| Register | `/register` | Регистрация |

## API Endpoints

| Метод | Endpoint | Описание |
|---|---|---|
| POST | `/api/v1/auth/register` | Регистрация |
| POST | `/api/v1/auth/login` | Авторизация → JWT токен |
| GET | `/api/v1/projects` | Список проектов |
| POST | `/api/v1/projects` | Создать проект |
| GET | `/api/v1/projects/:id` | Детали проекта |
| PUT | `/api/v1/projects/:id` | Обновить проект |
| DELETE | `/api/v1/projects/:id` | Удалить проект |
| GET | `/api/v1/projects/:id/documents` | Документы проекта |
| POST | `/api/v1/projects/:id/documents` | Загрузить документ (multipart) |
| GET | `/api/v1/documents/:id` | Просмотр документа |
| DELETE | `/api/v1/documents/:id` | Удалить документ |
| GET | `/api/v1/projects/:id/predictions` | Результаты анализа |
| POST | `/api/v1/projects/:id/predictions/generate` | Запустить NLP-анализ |

## Технологический стек

| Слой | Технологии |
|---|---|
| Frontend | React 18, Tailwind CSS 3, Vite, Axios, React Router 6 |
| Backend | Go 1.25, Chi Router, pgx, zerolog, JWT (HS256) |
| NLP Service | Python 3.11, FastAPI, Hugging Face Transformers, RuBERT |
| Database | PostgreSQL 16, UUID primary keys |
| DevOps | Docker Compose, Nginx (frontend proxy), multi-stage builds |

## Переменные окружения (.env)

```env
# PostgreSQL
POSTGRES_USER=nlp_user
POSTGRES_PASSWORD=nlp_pass
POSTGRES_DB=nlp_platform
DB_PORT_HOST=5433

# Backend
APP_PORT=8081
POSTGRES_DSN=postgres://nlp_user:nlp_pass@localhost:5433/nlp_platform?sslmode=disable
```

## Лицензия

Дипломный проект. Все права защищены.
