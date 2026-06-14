-- ==========================================
-- 005_audit_journal.sql — Upgrade predictions table schema
-- ==========================================

ALTER TABLE predictions ADD COLUMN IF NOT EXISTS meta_info JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS executive_summary TEXT NOT NULL DEFAULT '';
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS tech_stack JSONB NOT NULL DEFAULT '{"detected": [], "missing": []}'::jsonb;
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS metrics JSONB NOT NULL DEFAULT '[]'::jsonb;
