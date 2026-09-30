# ShopNow - Online Shopping System

> **A University-Level Software Engineering Project**  
> Built from scratch with pure, unadulterated web technologies: **HTML5, CSS3, Vanilla JavaScript, Pure Python, and MySQL**.

---

## 📖 1. Project Overview

**ShopNow** is a complete, modern e-commerce web application designed to demonstrate the internal architecture of an online shopping system. It fulfills university software engineering requirements by using pure web standards without external frameworks (No React, Vue, Angular, Bootstrap, Tailwind, jQuery, Flask, Django, FastAPI, or Express).

### Key Purposes
1. **Educational Learning**: Demonstrates standard HTTP web requests, REST API endpoint routing, password hashing, database schema design, and DOM manipulation.
2. **Real-world E-commerce Workflow**: Covers customer registration, authentication, catalog browsing, real-time product search, filtering, quantity control, checkout, simulated payment, order placement, order tracking, and an administrator panel.

---

## 🚀 2. System Architecture

```text
               FRONTEND LAYER
      ┌────────────────────────────────┐
      │ HTML5 Semantic Markup          │
      │ CSS3 Modern Design System      │
      │ Vanilla JavaScript (ES6+)      │
      └───────────────┬────────────────┘
                      │
                      │ HTTP GET/POST (JSON Payload)
                      ▼
               BACKEND LAYER
      ┌────────────────────────────────┐
      │ Pure Python HTTP Server        │
      │ Built-in Modules:              │
      │ (http.server, json, hashlib,   │
      │  os, datetime, urllib.parse)   │
      └───────────────┬────────────────┘
                      │
                      │ SQL Queries (mysql-connector-python)
                      ▼
               DATABASE LAYER
      ┌────────────────────────────────┐
      │ MySQL Relational Database      │
      │ Tables: users, admins,         │
      │ categories, products, cart,    │
      │ orders, order_items            │
      └────────────────────────────────┘
```

---

## 🛠️ 3. Technologies Used

| Layer | Technologies & Built-in Modules |
|---|---|
| **Frontend** | HTML5, Vanilla CSS3 (CSS Variables, Flexbox, Grid), Vanilla JavaScript |
| **Backend** | Pure Python 3 (`http.server`, `json`, `os`, `hashlib`, `datetime`, `urllib.parse`, `sys`) |
| **Database** | MySQL Server 8.0+ |
| **Database Connector** | `mysql-connector-python` |

---

## 📂 4. Project Folder Structure

```text
online-shopping-system/
│
├── frontend/
│   ├── index.html                 # Home Page
│   ├── login.html                 # Customer Login Page
│   ├── register.html              # Customer Registration Page
│   ├── products.html              # Products Catalog & Search Page
│   ├── product-details.html       # Product Details Page
│   ├── cart.html                  # Shopping Cart Page
│   ├── checkout.html              # Order Checkout & Payment Page
│   ├── order-confirmation.html    # Order Receipt Confirmation Page
│   ├── orders.html                # Customer Order History Page
│   ├── profile.html               # User Profile Page
│   │
│   ├── admin/
│   │   ├── login.html             # Admin Authentication Page
│   │   ├── dashboard.html         # Admin Dashboard & Metrics
│   │   ├── products.html          # Admin Product Inventory CRUD Page
│   │   ├── users.html             # Admin Customer Directory Page
│   │   └── orders.html            # Admin Order Status Management Page
│   │
│   ├── css/
│   │   ├── style.css              # Main Customer Design System
│   │   ├── admin.css              # Admin Panel Stylesheet
│   │   └── responsive.css         # Responsive Breakpoints (Desktop, Laptop, Tablet, Mobile)
│   │
│   ├── js/
│   │   ├── main.js                # Global Utilities, Currency & API Helper
│   │   ├── auth.js                # Customer Register & Login Validation
│   │   ├── products.js            # Products Catalog, Search & Filter Logic
│   │   ├── cart.js                # Shopping Cart Logic
│   │   ├── checkout.js            # Order Placement & Receipt Logic
│   │   └── admin.js               # Admin Metrics, Product Modal & Order Status Handler
│   │
│   └── images/                    # Product Images Directory
│
├── backend/
│   ├── server.py                  # Pure Python HTTP Web & REST API Server
│   ├── auth.py                    # SHA-256 Hashing & User Auth Module
│   ├── products.py                # Product Catalog Data Operations
│   ├── cart.py                    # Cart Operations Module
│   ├── orders.py                  # Order Placement & Item Breakdown Module
│   ├── admin.py                   # Admin Management Backend Operations
│   ├── database.py                # Database Connection Pool Helper
│   └── config.py                  # Environment & Server Settings
│
├── database/
│   └── online_shopping.sql        # MySQL Database Creation & Seed Script
│
└── README.md                      # System Documentation
```

---

## ⚙️ 5. Installation & Setup Guide

### Step 1: Clone or Extract Workspace
Navigate to the root directory `c:\Users\Laptop Valley\Desktop\project of fida sir`.

### Step 2: Set Up MySQL Database
1. Start your MySQL Server (via XAMPP, WAMP, or standalone MySQL Server).
2. Open terminal or MySQL Workbench and import `database/online_shopping.sql`:
   ```bash
   mysql -u root -p < database/online_shopping.sql
   ```
3. Update database connection password in `backend/config.py` if needed:
   ```python
   DB_CONFIG = {
       'host': 'localhost',
       'user': 'root',
       'password': 'YOUR_MYSQL_PASSWORD',
       'database': 'online_shopping',
       'port': 3306
   }
   ```

### Step 3: Install MySQL Connector for Python
```bash
pip install mysql-connector-python
```

### Step 4: Run the Python Server
Launch the pure Python backend server:
```bash
python backend/server.py
```
*The server will start running at:* `http://localhost:8000`

---

## 🔑 6. Default Login Credentials

### Administrator Account
- **URL**: `http://localhost:8000/admin/login.html`
- **Username**: `admin`
- **Password**: `admin123`

### Demo Customer Account
- **URL**: `http://localhost:8000/login.html`
- **Email**: `john@example.com`
- **Password**: `123456`

---

## 📊 7. System Workflow & Data Flows

### Registration Flow
```text
User Registration Form -> JS Validation -> SHA-256 Hashing -> MySQL `users` table -> Login Redirect
```

### Search Flow
```text
Search Bar Input ("phone", "laptop") -> JS Filter -> Python Backend /api/products?search=... -> Dynamic Grid Update
```

### Order Placement Flow
```text
Cart Items -> Checkout Form -> Payment Method Selection -> Stock Validation -> MySQL `orders` & `order_items` tables -> Receipt Page (#ORD-XXXXX)
```

---

## 🧪 8. Testing Checklist

- [x] **Registration**: Validates email format, minimum 6-character password, matching password confirmation.
- [x] **Login**: Authenticates credentials, sets session token, updates header UI.
- [x] **Product Search**: Searches title/description. Displays `No products found.` when 0 matches return.
- [x] **Category Filter**: Filters catalog by Electronics, Laptops, Fashion, Accessories, Home & Kitchen, Sports.
- [x] **Cart Management**: Add items, increase/decrease quantity, prevent negative/zero values, calculate subtotal and shipping fees.
- [x] **Checkout & Payment**: Validates customer shipping info, toggles simulated credit card inputs, generates order receipt.
- [x] **Admin Panel**: Logs into dashboard, displays Total Revenue and Low Stock metrics, adds/edits/deletes products via modal dialog, updates order status inline (`Pending` -> `Delivered`).

---

## 🔒 9. Security & Error Handling

1. **No Real Card Storage**: Payment options simulate card transactions without capturing sensitive bank numbers.
2. **Password Hashing**: Stored passwords use SHA-256 encryption combined with a unique salt string.
3. **Quantity Integrity**: Protects against invalid values (`-5`, `0`, or `999999999`).
4. **Friendly User Alerts**: Technical stack trace errors are swallowed server-side; users see clean alert banners.
