-- ==========================================
-- 006_add_gap_analysis.sql — Добавление gap_analysis в predictions
-- ==========================================

ALTER TABLE predictions ADD COLUMN IF NOT EXISTS gap_analysis JSONB DEFAULT NULL;
