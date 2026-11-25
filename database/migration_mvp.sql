-- ============================================================================
-- ShopNow MVP Migration Script (Safe to run on existing database)
-- Adds is_active to products and creates sessions table without deleting data.
-- ============================================================================

USE online_shopping;

-- 1. Create sessions table if not exists
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    user_id INT NOT NULL,
    role ENUM('customer', 'admin') DEFAULT 'customer',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Add is_active column to products if missing
SET @col_exists = 0;
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.columns 
WHERE table_schema = DATABASE() AND table_name = 'products' AND column_name = 'is_active';

SET @stmt = IF(@col_exists = 0, 'ALTER TABLE products ADD COLUMN is_active TINYINT(1) DEFAULT 1', 'SELECT "Column is_active already exists"');
PREPARE run_stmt FROM @stmt;
EXECUTE run_stmt;
DEALLOCATE PREPARE run_stmt;

-- 3. Update existing products to active
UPDATE products SET is_active = 1 WHERE is_active IS NULL;
