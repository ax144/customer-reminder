-- 创建安徽财经大学校友信息表
CREATE TABLE IF NOT EXISTS alumni (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    background TEXT,
    company VARCHAR(200),
    stock_code VARCHAR(50),
    position VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_alumni_name ON alumni(name);
CREATE INDEX IF NOT EXISTS idx_alumni_company ON alumni(company);
CREATE INDEX IF NOT EXISTS idx_alumni_position ON alumni(position);

-- 查看表结构
-- \d alumni
