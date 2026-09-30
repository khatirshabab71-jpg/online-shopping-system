-- ============================================================================
-- ShopNow - Online Shopping System MySQL Database Schema
-- Database Name: online_shopping
-- Educational & Software Engineering University Project
-- ============================================================================

-- 1. Create Database if not exists and select database
CREATE DATABASE IF NOT EXISTS online_shopping;
USE online_shopping;

-- 2. Drop existing tables in reverse dependency order (to avoid FK constraints issues during re-import)
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS users;

-- ============================================================================
-- TABLE CREATION STATEMENTS
-- ============================================================================

-- Table 1: users (Stores registered customer account details)
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    password VARCHAR(255) NOT NULL, -- SHA-256 Hashed Password
    address TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table 2: admins (Stores administrator login accounts)
CREATE TABLE admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table 3: categories (Stores product category classifications)
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table 4: products (Stores inventory items available for purchase)
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    product_name VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    discount INT DEFAULT 0 CHECK (discount >= 0 AND discount <= 100),
    stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    rating DECIMAL(2, 1) DEFAULT 4.5 CHECK (rating >= 1.0 AND rating <= 5.0),
    image VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table 5: cart (Stores active customer shopping cart items)
CREATE TABLE cart (
    cart_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT unique_user_product UNIQUE (user_id, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table 6: orders (Stores customer order invoices)
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount >= 0),
    payment_method VARCHAR(50) NOT NULL,
    shipping_address TEXT NOT NULL,
    order_status ENUM('Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled') DEFAULT 'Pending',
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table 7: order_items (Stores individual line items within an order)
CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- SEED SAMPLE DATA INSERTS
-- ============================================================================

-- Seed Categories
INSERT INTO categories (category_id, category_name) VALUES
(1, 'Electronics'),
(2, 'Laptops & Computing'),
(3, 'Fashion & Apparel'),
(4, 'Accessories'),
(5, 'Home & Kitchen'),
(6, 'Sports & Outdoor');

-- Seed Default Admin Account (username: admin, password: SHA-256 for admin123)
INSERT INTO admins (username, password) VALUES
('admin', 'admin123');

-- Seed Sample Users
INSERT INTO users (user_id, name, email, phone, password, address, created_at) VALUES
(1, 'John Doe', 'john@example.com', '+1234567890', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', '123 University Campus St, Apt 4B, New York, NY 10001', '2026-09-01 10:00:00'),
(2, 'Jane Smith', 'jane@example.com', '+1555014499', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', '456 Tech Park Boulevard, Suite 12, San Francisco, CA 94107', '2026-09-05 14:30:00');

-- Seed 18 Realistic Products
INSERT INTO products (product_id, category_id, product_name, description, price, discount, stock, rating, image) VALUES
(1, 1, 'Pro Wireless Smartphone 128GB', 'Experience cutting-edge smartphone technology with high-resolution camera system, long-lasting battery, and superfast processing power.', 699.99, 15, 15, 4.5, 'images/phone.jpg'),
(2, 2, 'UltraBook Slim 15 Pro Core i7', 'Lightweight ultra-performance laptop designed for software development, graphic creation, and multi-tasking productivity.', 1199.00, 0, 8, 4.9, 'images/laptop.jpg'),
(3, 4, 'Active Noise Cancelling Wireless Headphones', 'Immersive sound quality with active noise cancellation, built-in HD microphone, and 30-hour playback battery life.', 149.99, 20, 25, 4.2, 'images/headphones.jpg'),
(4, 4, 'Smart Fitness Watch Series 5', 'Track heart rate, daily steps, sleep patterns, and sports activities with water-resistant sleek OLED touchscreen.', 89.99, 0, 18, 4.6, 'images/watch.jpg'),
(5, 3, 'Men Classic Slim Fit Denim Jacket', 'Stylish premium denim jacket crafted from comfortable breathable cotton blend. Suitable for all casual occasions.', 59.99, 10, 30, 4.4, 'images/jacket.jpg'),
(6, 5, 'Automatic Stainless Steel Coffee Maker', 'Programmable drip coffee machine with thermal stainless steel carafe, automatic shut-off, and built-in bean grinder.', 129.50, 5, 12, 4.7, 'images/coffeemaker.jpg'),
(7, 1, '4K Ultra HD Smart LED TV 55 Inch', 'Stunning 4K picture clarity with HDR display, built-in Wi-Fi, streaming apps, and immersive Dolby Atmos surround audio.', 499.00, 12, 10, 4.8, 'images/tv.jpg'),
(8, 2, 'Gaming Laptop i9 RTX 4080 32GB', 'High-end gaming laptop featuring 240Hz display refresh rate, advanced liquid cooling, and customizable RGB keyboard.', 2199.99, 8, 5, 4.9, 'images/gaminglaptop.jpg'),
(9, 1, 'Portable Bluetooth Waterproof Speaker', 'Rugged outdoor wireless speaker delivering deep bass audio, 20-hour battery life, and IPX7 waterproof protection.', 45.00, 0, 40, 4.3, 'images/speaker.jpg'),
(10, 3, 'Women Ergonomic Running Sneakers', 'Ultralight responsive cushion running shoes engineered for maximum comfort, support, and athletic endurance.', 79.99, 15, 22, 4.6, 'images/sneakers.jpg'),
(11, 4, 'Ergonomic Wireless Vertical Mouse', 'Prevents wrist strain with natural handshake grip position, silent click buttons, and dual Bluetooth wireless connection.', 29.99, 0, 50, 4.4, 'images/mouse.jpg'),
(12, 5, 'Digital Air Fryer Oven 5.8 Qt', 'Healthy oil-free cooking with 8 one-touch preset functions, nonstick dishwasher safe basket, and rapid air circulation.', 89.95, 10, 14, 4.7, 'images/airfryer.jpg'),
(13, 6, 'Adjustable Cast Iron Dumbbell Set 50lbs', 'Heavy-duty steel weight set with knurled chrome handles for home gym strength training and workouts.', 119.00, 5, 9, 4.5, 'images/dumbbells.jpg'),
(14, 3, 'Water Resistant Laptop Backpack 15.6"', 'Spacious travel backpack with built-in USB charging port, anti-theft hidden pocket, and padded laptop compartment.', 39.99, 0, 35, 4.6, 'images/backpack.jpg'),
(15, 6, 'Pro Non-Slip Yoga Mat 6mm Thick', 'High-density eco-friendly TPE foam mat providing joint cushioning and superior grip for yoga and pilates exercises.', 24.99, 0, 28, 4.3, 'images/yogamat.jpg'),
(16, 2, '27 Inch Curved Gaming Monitor 165Hz', 'Immersive 1500R curved QHD monitor with 1ms response time, AMD FreeSync Premium, and eye-care blue light filter.', 249.99, 15, 7, 4.8, 'images/monitor.jpg'),
(17, 5, 'Robot Vacuum Cleaner with Mop Combo', 'Smart LiDAR mapping navigation with 3000Pa suction power, automatic self-charging, and app remote control.', 299.00, 20, 6, 4.6, 'images/robotvacuum.jpg'),
(18, 4, 'Mechanical Gaming Keyboard RGB', 'Tactile mechanical switches with customizable per-key RGB backlighting, detachable Type-C cable, and aluminum frame.', 69.99, 10, 20, 4.7, 'images/keyboard.jpg');

-- Seed Sample Orders
INSERT INTO orders (order_id, user_id, total_amount, payment_method, shipping_address, order_status, order_date) VALUES
(10024, 1, 714.99, 'Cash on Delivery', '123 University Campus St, Apt 4B, New York, NY 10001', 'Pending', '2026-09-13 18:20:00'),
(10018, 2, 149.99, 'Simulated Card Payment', '456 Tech Park Boulevard, Suite 12, San Francisco, CA 94107', 'Delivered', '2026-09-01 11:45:00');

-- Seed Sample Order Items
INSERT INTO order_items (order_item_id, order_id, product_id, quantity, price) VALUES
(1, 10024, 1, 1, 699.99),
(2, 10018, 3, 1, 149.99);
