# ShopNow - Online Shopping System (Phase 2 Production MVP)

> **Final Semester Software Engineering Project**  
> Built with pure standards-based web technologies: **HTML5, Custom CSS3, Vanilla JavaScript (ES6+), Pure Python (built-in `http.server`), and MySQL (InnoDB)**.  
> **Shared Source of Truth:** A customer places a Cash on Delivery order in one browser, Python processes and saves it in MySQL via an atomic ACID transaction with row-level locks, and the store administrator reviews, tracks audit history, and updates order status in real time from another browser.

---

## 📖 1. Project Overview & System Highlights

**ShopNow** is a full-stack, single-store e-commerce application demonstrating modern software engineering principles, OWASP web application security standards, database integrity, and asynchronous notifications without relying on third-party frameworks (no React, Angular, Vue, Flask, Django, or FastAPI):

1. **Frontend**: Clean semantic HTML5, responsive CSS3 design, and modular vanilla JavaScript communicating with backend REST endpoints (`/api/...`) via asynchronous `fetch` with session token authorization.
2. **Backend**: Pure Python HTTP server utilizing standard library modules (`http.server`, `hashlib`, `hmac`, `secrets`, `smtplib`, `threading`, `json`, `decimal`, `datetime`). Implements business logic, server-managed sessions, input sanitization, rate limiting, and security headers.
3. **Database**: MySQL 8.0+ with InnoDB storage engine ensuring ACID compliance, row locking (`SELECT ... FOR UPDATE`), referential integrity (`ON DELETE RESTRICT`), and audit logging.
4. **Email Notification Engine**: Asynchronous, non-blocking daemon thread delivery via standard SMTP with automatic fallback logging to `backend/logs/email_outbox.log` for offline development and academic testing.
5. **Customer Enhancements**: MySQL-backed Wishlist, verified purchase Product Reviews & 5-star Ratings with automatic aggregate recalculation, multi-facet product search/filtering, and pagination.

---

## 🏛️ 2. Architectural Diagram

```text
       CUSTOMER BROWSER (Browser A)              ADMIN BROWSER (Browser B)
   ┌───────────────────────────────────┐    ┌───────────────────────────────────┐
   │ HTML5 / CSS3 / Vanilla JavaScript │    │ Admin Portal (HTML / CSS / JS)    │
   │ Session Token in Authorization    │    │ Admin Session Token               │
   └─────────────────┬─────────────────┘    └─────────────────┬─────────────────┘
                     │                                        │
                     │ HTTP GET / POST (/api/...)             │ HTTP GET / POST (/api/admin/...)
                     ▼                                        ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │                      PYTHON BACKEND (server.py)                            │
   │  Built-in http.server.HTTPServer & BaseHTTPRequestHandler                  │
   │                                                                            │
   │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌─────────────┐  │
   │  │ auth.py        │ │ products.py    │ │ cart.py        │ │ orders.py   │  │
   │  │ scrypt + salt  │ │ Multi-filter   │ │ Stock bounds   │ │ ACID atomic │  │
   │  │ Rate limiting  │ │ Pagination     │ │ Session sync   │ │ FOR UPDATE  │  │
   │  └────────────────┘ └────────────────┘ └────────────────┘ └─────────────┘  │
   │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌─────────────┐  │
   │  │ wishlist.py    │ │ reviews.py     │ │ admin.py       │ │ email_svc.py│  │
   │  │ MySQL Wishlist │ │ Verified badge │ │ Metrics, Audit │ │ Async SMTP  │  │
   │  │ Move-to-cart   │ │ Star aggregate │ │ Review delete  │ │ Outbox log  │  │
   │  └────────────────┘ └────────────────┘ └────────────────┘ └─────────────┘  │
   └─────────────────────────────────────┬──────────────────────────────────────┘
                                         │
                                         │ mysql-connector-python (TCP 3306)
                                         ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │                         MySQL DATABASE (InnoDB)                            │
   │  online_shopping: users, admins, sessions, account_tokens, login_attempts, │
   │                   categories, products, cart, wishlist, reviews, orders,   │
   │                   order_items, order_status_history                        │
   └────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ 3. Security Hardening (OWASP Compliance)

| Security Domain | Implementation Details |
|---|---|
| **Password Hashing** | Python standard library `hashlib.scrypt` with unique 16-byte random salts (`scrypt$<salt_hex>$<hash_hex>`). Parameters: `n=16384, r=8, p=1`. Resistant to GPU/ASIC brute-force attacks. Backward compatible auto-upgrade for legacy hashes upon successful login. |
| **Password Strength** | Enforces minimum 8 characters, at least 1 uppercase letter (`A-Z`), 1 lowercase letter (`a-z`), 1 numeric digit (`0-9`), and 1 special symbol. |
| **Brute-Force Rate Limiting** | Blocks accounts/IP addresses after 5 consecutive failed login attempts within 15 minutes (`login_attempts` table with in-memory fallback). |
| **Session Security** | Cryptographically strong 256-bit random session tokens (`secrets.token_hex(32)`) stored server-side in MySQL with IP address and User-Agent tracking. Revoked immediately on logout or password change. |
| **Account Recovery & Verification** | Single-use expiring tokens (24h for email verification, 30m for password resets). Only SHA-256 hashes of tokens are stored in the database to prevent token leakage. |
| **Security Headers** | Injected on every HTTP response: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`. |
| **Path Traversal Protection** | Canonical absolute path resolution verifies requested static files never escape `frontend/` directory, responding with `403 Forbidden`. |
| **Data Integrity & Concurrency** | ACID transactions with row-level locks (`SELECT ... FOR UPDATE`) prevent race conditions, negative inventory, and duplicate checkouts. Referential integrity uses `ON DELETE RESTRICT` on `order_items`. |

---

## ⚙️ 4. Installation & Local Setup Guide (Windows)

### Prerequisites
- **Python 3.10+** (tested on Python 3.12 and 3.15)
- **MySQL Server 8.0+** (via XAMPP, WAMP, MySQL Installer, or Docker)

### Step 1: Install Python Dependencies
Open PowerShell or Command Prompt in the project folder:
```powershell
pip install mysql-connector-python pillow
```

### Step 2: Set Up MySQL Database
1. Start your local MySQL service (e.g. click **Start** next to MySQL in XAMPP Control Panel, or run `net start MySQL`).
2. Open terminal in the project root directory and import the database schema & seed data:
```powershell
mysql -u root -p < database/online_shopping.sql
```
*(If your local root user has no password, press Enter when prompted).*

> **Upgrading from Phase 1 without data loss?**  
> Run the non-destructive migration script:
> ```powershell
> mysql -u root -p online_shopping < database/migration_phase2.sql
> ```

### Step 3: Configure Environment Variables (Optional)
The system runs out-of-the-box with default localhost settings. Override any setting via environment variables:

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `localhost` | MySQL host address |
| `DB_PORT` | `3306` | MySQL TCP port |
| `DB_USER` | `root` | Database username |
| `DB_PASSWORD` | `""` | Database password (blank for default XAMPP) |
| `DB_NAME` | `online_shopping` | MySQL database name |
| `SERVER_PORT` | `8000` | HTTP server listening port |
| `SMTP_HOST` | `""` | SMTP mail server (e.g., `smtp.gmail.com`) |
| `SMTP_PORT` | `587` | SMTP port (typically 587 for TLS) |
| `SMTP_USER` | `""` | SMTP username / email address |
| `SMTP_PASSWORD` | `""` | SMTP password or App Password |
| `USE_HTTPS` | `false` | Set `true` to enable TLS encryption |
| `SSL_CERT_FILE` | `""` | Path to SSL certificate (`.crt` / `.pem`) |
| `SSL_KEY_FILE` | `""` | Path to SSL private key (`.key`) |

*(If SMTP is not configured, emails are automatically logged to `backend/logs/email_outbox.log` for inspection).*

### Step 4: Start the Python Backend Server
```powershell
python backend/server.py
```
Server banner output:
```text
======================================================================
SHOPNOW PYTHON BACKEND RUNNING AT: http://localhost:8000
Serving storefront from: D:\online shopping system\frontend
API Base URL: /api
Security Headers: Active (CSP, nosniff, DENY frame, XSS protection)
======================================================================
```

### Step 5: Open the Application in Your Browser
- **Customer Storefront**: [http://localhost:8000](http://localhost:8000)
- **Admin Management Portal**: [http://localhost:8000/admin/login.html](http://localhost:8000/admin/login.html)

---

## 🔑 5. Pre-Seeded Demonstration Accounts

| Role | Login URL | Email / Username | Password | Notes |
|---|---|---|---|---|
| **Store Administrator** | `/admin/login.html` | `admin` | `admin123` | Full dashboard metrics, product CRUD, status updates, review moderation |
| **Customer (John Doe)** | `/login.html` | `john@example.com` | `123456` | Has order history `#ORD-10024`, verified reviews |
| **Customer (Jane Smith)** | `/login.html` | `jane.smith@university.edu` | `123456` | Has order history `#ORD-10018` |

*(You can also register a new account on `/register.html` with any valid email and strong password).*

---

## 🧪 6. Automated Testing & Verification Suite

The repository includes three levels of automated tests:

### 1. Offline Unit & Security Logic Tests
Validates `scrypt` hashing, token generation, rate limiting, RFC email validation, custom JSON Decimal/datetime encoding, and email templates:
```powershell
python backend/test_api.py
```
*(Runs 8 tests in seconds, passes independently without requiring MySQL).*

### 2. Live HTTP Server Integration Tests
Validates live static file serving, path traversal defense, 401 unauthenticated cart/wishlist guards, 403 unauthorized admin guards, and 404 handlers:
```powershell
# With server.py running in another terminal:
python backend/test_server_http.py
```

### 3. End-to-End Database Integration & Concurrency Tests
Validates the full MySQL schema (all 13 tables, primary/foreign keys, `ON DELETE RESTRICT`), user registration, session management, catalog pagination, cart upsert, atomic checkout with `FOR UPDATE` row locking, stock rollback on inventory shortage, admin status audit trail, and verified purchase review submission:
```powershell
# Run with MySQL server active:
python backend/test_database_integration.py
```
*(If MySQL is offline, the script outputs a transparent diagnostic report identifying the blocker without failing unexpectedly).*

---

## 🌐 7. Production Deployment & HTTPS Setup

For production deployment:

### Native Python HTTPS / TLS
1. Generate or place your TLS certificate and private key in a secure folder:
   ```powershell
   # Self-signed certificate for local testing:
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   ```
2. Launch server with HTTPS enabled:
   ```powershell
   $env:USE_HTTPS="true"
   $env:SSL_CERT_FILE="D:\online shopping system\cert.pem"
   $env:SSL_KEY_FILE="D:\online shopping system\key.pem"
   python backend/server.py
   ```

### Reverse Proxy (Nginx on Linux or Windows)
Recommended production setup with Nginx handling SSL termination and static assets, proxying `/api` requests to Python:
```nginx
server {
    listen 443 ssl http2;
    server_name shopnow.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/shopnow.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shopnow.yourdomain.com/privkey.pem;

    location / {
        root /var/www/shopnow/frontend;
        index index.html;
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 🎙️ 8. Three-Minute Viva Presentation Script

> **Duration:** 3 Minutes  
> **Audience:** External Examiner / Project Review Committee

**[0:00 - 0:40] Introduction & Problem Solved**
> "Good morning, respected examiners. Today I am presenting **ShopNow**, a full-stack online shopping system built using pure web standards: HTML5, CSS3, vanilla JavaScript, Python's built-in HTTP server, and MySQL.  
> The core engineering problem we solved was eliminating fragile client-side storage and building a hardened, enterprise-grade architecture. In earlier prototypes, shopping carts and orders were held in browser memory, leaving the administrator blind to real customer orders. In ShopNow, MySQL is the single authoritative source of truth across all customer and admin sessions."

**[0:40 - 1:25] Security & Transaction Architecture**
> "We placed particular emphasis on OWASP application security without relying on external web frameworks:
> 1. **Authentication & Hashing:** We implemented Python standard library `scrypt` hashing with unique 16-byte random salts per password, protecting against rainbow tables and GPU attacks.
> 2. **Brute Force Protection:** Failed login attempts are tracked and rate-limited after 5 attempts.
> 3. **Account Recovery:** Email verification and password resets utilize single-use tokens expiring within 30 minutes, stored as SHA-256 hashes.
> 4. **Transactional ACID Checkout:** When a customer places a Cash on Delivery order, Python executes an atomic transaction with row-level locks using `SELECT ... FOR UPDATE`. In a single atomic unit, the server re-validates stock, creates the order header, inserts line items, decrements inventory, logs an audit entry in `order_status_history`, and clears the cart. If any product is out of stock, the transaction rolls back cleanly, leaving zero ghost records."

**[1:25 - 2:25] Live Two-Browser Demonstration**
> "Let's demonstrate cross-browser synchronization live:
> - In **Browser A**, logged in as customer John, I browse the catalog with multi-facet filters, add the 'Pro Wireless Smartphone' to my Wishlist, move it to the Cart, and submit a Cash on Delivery order. An order receipt is generated with MySQL ID `#ORD-10025`.
> - Simultaneously in **Browser B**, logged into the Admin portal, I open Order Management. Order `#ORD-10025` appears immediately.
> - I will now change the order status from `Pending` to `Shipped` and add the admin note: 'Dispatched via Express Courier'.
> - In John's browser, refreshing My Orders displays the status updated to `Shipped`, and John can now submit a 5-star review, which automatically receives the 'Verified Purchase' badge.
> - Meanwhile, in the background, our decoupled email daemon logged an order confirmation invoice and a shipping notification to our audit log."

**[2:25 - 3:00] Conclusion & Technical Significance**
> "In conclusion, ShopNow proves that a secure, scalable, and responsive e-commerce platform can be built with pure native technologies, strict database locking, server-managed sessions, and OWASP defenses. Thank you, and I look forward to your questions."

---

## 📂 9. Project Directory Tree

```text
online-shopping-system/
│
├── frontend/
│   ├── index.html                 # Customer Storefront Home Page
│   ├── login.html                 # Customer Login (with Forgot Password link)
│   ├── register.html              # Customer Registration (Strong password validation)
│   ├── verify-email.html          # Email Verification Landing Page
│   ├── forgot-password.html       # Password Reset Request Page
│   ├── reset-password.html        # New Password Submission Page
│   ├── products.html              # Catalog (Search, Price/Rating filters, Pagination)
│   ├── product-details.html       # Details, Ratings Breakdown, Customer Reviews
│   ├── wishlist.html              # Customer Saved Items & Move-to-Cart
│   ├── cart.html                  # Shopping Cart (Server-backed CRUD)
│   ├── checkout.html              # Cash on Delivery Checkout Form
│   ├── order-confirmation.html    # Order Receipt Confirmation Page
│   ├── orders.html                # Customer Order History Page
│   ├── profile.html               # Profile & Password Update with Current Password
│   │
│   ├── admin/
│   │   ├── login.html             # Admin Authentication Portal
│   │   ├── dashboard.html         # Real-time Metrics & Inventory Analytics
│   │   ├── products.html          # Product CRUD (Add, Edit, Soft Delete / Restore)
│   │   ├── users.html             # Customer Account Directory
│   │   ├── orders.html            # Order Fulfillment & Audit History Inspection
│   │   └── reviews.html           # Product Review Moderation & Deletion
│   │
│   ├── css/
│   │   ├── style.css              # Main Customer Storefront Stylesheet
│   │   ├── admin.css              # Admin Panel Theme & Component Styles
│   │   └── responsive.css         # Responsive Breakpoints (Mobile, Tablet, Desktop)
│   │
│   ├── js/
│   │   ├── main.js                # Core API Fetch Client, Session Tokens, Header Badges
│   │   ├── auth.js                # Auth, Strong Passwords, Rate Limiting & Verification
│   │   ├── products.js            # Multi-facet Filters, Pagination, Reviews & Wishlist
│   │   ├── wishlist.js            # Wishlist Rendering & Move-to-Cart Operations
│   │   ├── cart.js                # Server-backed Cart CRUD Operations
│   │   ├── checkout.js            # COD Checkout & Server Receipt Verification
│   │   ├── orders.js              # Customer Order History Loader
│   │   └── admin.js               # Admin Dashboard, Products, Orders, Reviews Moderation
│   │
│   └── images/                    # Local Product Placeholder Images (18 items)
│
├── backend/
│   ├── server.py                  # Pure Python HTTP Web & REST API Server (TLS optional)
│   ├── auth.py                    # scrypt Hashing, Tokens, Rate Limiting, Sessions
│   ├── products.py                # Multi-facet Catalog Filtering & Pagination Module
│   ├── cart.py                    # MySQL Cart Management Module
│   ├── wishlist.py                # MySQL Wishlist Management Module
│   ├── reviews.py                 # Customer Reviews, Verified Badges & Aggregate Ratings
│   ├── orders.py                  # Atomic Checkout (FOR UPDATE row locks) & History
│   ├── admin.py                   # Admin Analytics, Product CRUD, Status Updates & Audit
│   ├── database.py                # MySQL Connector Helper, Schema Auto-Provisioning
│   ├── email_service.py           # Asynchronous SMTP Email Dispatcher & HTML Templates
│   ├── config.py                  # System Configuration & Environment Variables
│   ├── test_api.py                # Automated Offline Unit & Security Test Suite
│   ├── test_server_http.py        # Automated HTTP Server Live Endpoint Test Suite
│   ├── test_database_integration.py # Automated MySQL Integration & Concurrency Test Suite
│   └── logs/
│       └── email_outbox.log       # Outbound Email Audit Log
│
├── database/
│   ├── online_shopping.sql        # Full MySQL Database Schema & Seed Data (Phase 2)
│   ├── migration_mvp.sql          # Non-destructive Phase 1 Migration Script
│   └── migration_phase2.sql       # Non-destructive Phase 2 Migration Script
│
├── .gitignore                     # Git Exclusion Rules (Secrets, __pycache__, logs)
└── README.md                      # Comprehensive System Guide & Presentation Script
```
