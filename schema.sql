-- ========================================================
-- TaskFlow Database Schema for Supabase PostgreSQL
-- Run this in your Supabase Dashboard: SQL Editor -> New Query -> Run
-- ========================================================

-- 1. Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    project TEXT DEFAULT 'General',
    due_date TEXT,
    priority TEXT DEFAULT 'Medium',
    status TEXT DEFAULT 'Pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Enable Row Level Security (RLS)
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- 3. Add open RLS policies (so the client/API key can read & write)
DROP POLICY IF EXISTS "Allow public read access" ON tasks;
CREATE POLICY "Allow public read access"
ON tasks FOR SELECT
USING (true);

DROP POLICY IF EXISTS "Allow public insert access" ON tasks;
CREATE POLICY "Allow public insert access"
ON tasks FOR INSERT
WITH CHECK (true);

DROP POLICY IF EXISTS "Allow public update access" ON tasks;
CREATE POLICY "Allow public update access"
ON tasks FOR UPDATE
USING (true);

DROP POLICY IF EXISTS "Allow public delete access" ON tasks;
CREATE POLICY "Allow public delete access"
ON tasks FOR DELETE
USING (true);

-- 4. Insert initial sample startup tasks (if table is empty)
INSERT INTO tasks (id, name, project, due_date, priority, status)
VALUES
  ('1', 'Design MVP landing page mockup in Figma', 'Website Launch', '2026-10-30', 'High', 'In Progress'),
  ('2', 'Setup user authentication & secure session tokens', 'Backend API', '2026-11-02', 'High', 'Pending'),
  ('3', 'Draft seed fundraising pitch deck', 'Fundraising', '2026-11-10', 'Medium', 'Pending'),
  ('4', 'Conduct user interviews with 5 beta testers', 'Customer Discovery', '2026-10-28', 'Medium', 'Completed'),
  ('5', 'Configure production SSL & domain DNS settings', 'DevOps', '2026-10-25', 'Low', 'Completed')
ON CONFLICT (id) DO NOTHING;

