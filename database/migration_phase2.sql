-- ============================================================================
-- ShopNow Phase 2 MVP Non-Destructive Migration Script
-- Adds Wishlist, Reviews, Account Tokens, Rate Limiting, Status History
-- Safe to execute against existing databases without data loss.
-- ============================================================================

USE online_shopping;

-- 1. Upgrade users table with verification flags
SET @col_verified_exists = 0;
SELECT COUNT(*) INTO @col_verified_exists 
FROM information_schema.columns 
WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name = 'is_verified';

SET @stmt_v = IF(@col_verified_exists = 0, 
    'ALTER TABLE users ADD COLUMN is_verified TINYINT(1) DEFAULT 0, ADD COLUMN email_verified_at DATETIME NULL', 
    'SELECT "Verification columns already exist in users"');
PREPARE run_v FROM @stmt_v;
EXECUTE run_v;
DEALLOCATE PREPARE run_v;

-- Set existing demo users to verified
UPDATE users SET is_verified = 1, email_verified_at = CURRENT_TIMESTAMP WHERE is_verified = 0 AND email IN ('john@example.com', 'jane@example.com');

-- 2. Upgrade sessions table with IP and User-Agent tracking for session hijacking defense
SET @col_ip_exists = 0;
SELECT COUNT(*) INTO @col_ip_exists 
FROM information_schema.columns 
WHERE table_schema = DATABASE() AND table_name = 'sessions' AND column_name = 'ip_address';

SET @stmt_ip = IF(@col_ip_exists = 0, 
    'ALTER TABLE sessions ADD COLUMN ip_address VARCHAR(45) NULL, ADD COLUMN user_agent VARCHAR(255) NULL', 
    'SELECT "IP tracking columns already exist in sessions"');
PREPARE run_ip FROM @stmt_ip;
EXECUTE run_ip;
DEALLOCATE PREPARE run_ip;

-- 3. Create account_tokens table (Single-use expiring tokens for Email Verification & Password Reset)
CREATE TABLE IF NOT EXISTS account_tokens (
    token_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    token_type ENUM('email_verification', 'password_reset') NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_token_hash (token_hash),
    INDEX idx_user_type (user_id, token_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Create login_attempts table (Brute-force and rate-limiting protection)
CREATE TABLE IF NOT EXISTS login_attempts (
    attempt_id INT AUTO_INCREMENT PRIMARY KEY,
    identifier VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    attempt_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    success TINYINT(1) DEFAULT 0,
    INDEX idx_ident_time (identifier, attempt_time),
    INDEX idx_ip_time (ip_address, attempt_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Create wishlist table (Persistent customer wishlist)
CREATE TABLE IF NOT EXISTS wishlist (
    wishlist_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    CONSTRAINT unique_wishlist_user_product UNIQUE (user_id, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Create reviews table (Customer product reviews, 1-5 ratings, verified purchases)
CREATE TABLE IF NOT EXISTS reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_title VARCHAR(150) NOT NULL,
    review_text TEXT NOT NULL,
    is_verified_purchase TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT unique_product_user_review UNIQUE (product_id, user_id),
    INDEX idx_prod_reviews (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Create order_status_history table (Audit trail for status changes)
CREATE TABLE IF NOT EXISTS order_status_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    changed_by VARCHAR(50) DEFAULT 'admin',
    notes VARCHAR(255) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    INDEX idx_order_hist (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Seed sample reviews for demo products
INSERT IGNORE INTO reviews (product_id, user_id, rating, review_title, review_text, is_verified_purchase, created_at) VALUES
(1, 1, 5, 'Outstanding Smartphone!', 'The battery life easily lasts two days, and the camera clarity is fantastic. Highly recommended for daily use.', 1, '2026-09-15 14:00:00'),
(1, 2, 4, 'Very good phone for the price', 'Build quality is premium. Charging is fast. Only complaint is the speaker could be slightly louder.', 1, '2026-09-18 16:30:00'),
(2, 1, 5, 'Top notch laptop for programming', 'Handles multiple virtual machines and IDEs without stuttering. Great keyboard and display.', 0, '2026-09-20 11:20:00'),
(3, 2, 4, 'Great noise cancellation', 'Blocks out subway and office noise comfortably. Battery lasts as advertised.', 1, '2026-09-02 09:15:00');
