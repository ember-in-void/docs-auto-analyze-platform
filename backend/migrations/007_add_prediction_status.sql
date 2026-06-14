-- ==========================================
-- 007_add_prediction_status.sql — Добавление статуса в прогнозы
-- ==========================================

ALTER TABLE predictions ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'completed';
