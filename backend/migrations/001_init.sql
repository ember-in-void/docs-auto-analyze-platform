-- ==========================================
-- 001_init.sql — Инициализация схемы БД
-- ==========================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- Таблица проектов
-- ==========================================
CREATE TABLE IF NOT EXISTS projects (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    description TEXT         NOT NULL DEFAULT '',
    status      VARCHAR(50)  NOT NULL DEFAULT 'active'
                             CHECK (status IN ('active', 'archived', 'completed')),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ==========================================
-- Таблица документов
-- ==========================================
CREATE TABLE IF NOT EXISTS documents (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID        NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title       VARCHAR(255) NOT NULL,
    content     TEXT         NOT NULL,
    doc_type    VARCHAR(50)  NOT NULL DEFAULT 'OTHER'
                             CHECK (doc_type IN ('TZ', 'ARCHITECTURE', 'REQUIREMENTS', 'LOGS', 'OTHER')),
    uploaded_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);

-- ==========================================
-- Таблица прогнозов
-- ==========================================
CREATE TABLE IF NOT EXISTS predictions (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id           UUID        NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    profitability_score  FLOAT       NOT NULL DEFAULT 0,
    risk_score           FLOAT       NOT NULL DEFAULT 0,
    relevance_score      FLOAT       NOT NULL DEFAULT 0,
    summary              TEXT        NOT NULL DEFAULT '',
    keywords             TEXT[]      NOT NULL DEFAULT '{}',
    model_version        VARCHAR(50) NOT NULL DEFAULT 'mock-v1',
    generated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_project_id ON predictions(project_id);

-- ==========================================
-- Функция авто-обновления updated_at
-- ==========================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
