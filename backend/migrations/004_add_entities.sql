-- ==========================================
-- 004_add_entities.sql — Добавление entities в predictions
-- ==========================================

ALTER TABLE predictions ADD COLUMN IF NOT EXISTS entities JSONB NOT NULL DEFAULT '[]'::jsonb;
