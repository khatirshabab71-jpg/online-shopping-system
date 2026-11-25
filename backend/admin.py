"""
ShopNow - Online Shopping System
Admin Management Backend Module (Pure Python + MySQL)
Includes product management, status updating, review moderation, and email alerts.
"""

from database import execute_query
from auth import verify_password, hash_password, create_session
import email_service

def admin_login(data: dict, ip_address: str = None, user_agent: str = None):
    """
    Authenticates administrator access against the admins table in MySQL.
    Creates a server-managed admin session upon success.
    """
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return {'success': False, 'message': 'Username and password are required.'}

    db_admin = execute_query(
        "SELECT admin_id, username, password FROM admins WHERE username = %s",
        (username,),
        fetchone=True
    )

    if not db_admin:
        return {'success': False, 'message': 'Invalid administrator credentials.'}

    stored_hash = db_admin.get('password', '')
    if not verify_password(password, stored_hash):
        return {'success': False, 'message': 'Invalid administrator credentials.'}

    # Auto-upgrade password to modern scrypt hash if stored in legacy or plaintext format
    if not stored_hash.startswith('scrypt$'):
        new_hash = hash_password(password)
        execute_query("UPDATE admins SET password = %s WHERE admin_id = %s", (new_hash, db_admin['admin_id']), commit=True)

    token = create_session(db_admin['admin_id'], role='admin', ip_address=ip_address, user_agent=user_agent)

    return {
        'success': True,
        'message': 'Admin authenticated successfully.',
        'token': token,
        'admin': {
            'username': db_admin['username'],
            'role': 'Administrator'
        }
    }

def get_dashboard_metrics():
    """
    Calculates actual database metrics directly from MySQL tables:
    Total active products, registered users, customer orders, total sales, pending orders, and low-stock alerts.
    """
    res_products = execute_query("SELECT COUNT(*) AS total FROM products WHERE is_active = 1", fetchone=True)
    res_users = execute_query("SELECT COUNT(*) AS total FROM users", fetchone=True)
    res_orders = execute_query("SELECT COUNT(*) AS total FROM orders", fetchone=True)
    res_sales = execute_query("SELECT COALESCE(SUM(total_amount), 0) AS total FROM orders WHERE order_status != 'Cancelled'", fetchone=True)
    res_pending = execute_query("SELECT COUNT(*) AS total FROM orders WHERE order_status = 'Pending'", fetchone=True)
    res_low_stock = execute_query("SELECT COUNT(*) AS total FROM products WHERE stock < 5 AND is_active = 1", fetchone=True)
    res_reviews = execute_query("SELECT COUNT(*) AS total FROM reviews", fetchone=True)

    if res_products is None or res_users is None:
        return None

    return {
        'total_products': res_products['total'] if res_products else 0,
        'total_users': res_users['total'] if res_users else 0,
        'total_orders': res_orders['total'] if res_orders else 0,
        'total_sales': round(float(res_sales['total']), 2) if res_sales else 0.0,
        'pending_orders': res_pending['total'] if res_pending else 0,
        'low_stock': res_low_stock['total'] if res_low_stock else 0,
        'total_reviews': res_reviews['total'] if res_reviews else 0
    }

def get_admin_products(search_query=None):
    """
    Retrieves all inventory products (including deactivated ones) for admin management.
    """
    query = """
        SELECT p.product_id, p.category_id, p.product_name, p.description, 
               p.price, p.discount, p.stock, p.rating, p.image, p.is_active, p.created_at,
               c.category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.category_id
    """
    params = []
    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        query += " WHERE p.product_name LIKE %s OR c.category_name LIKE %s"
        params.extend([q, q])

    query += " ORDER BY p.product_id DESC"
    products = execute_query(query, tuple(params), fetchall=True)
    if products:
        for p in products:
            p['id'] = p['product_id']
            p['name'] = p['product_name']
    return products if products is not None else []

def add_product(data: dict):
    """
    Adds a new product to store inventory in MySQL.
    """
    name = data.get('productName', '').strip()
    try:
        category_id = int(data.get('categoryId', 1))
        price = float(data.get('price', 0))
        discount = int(data.get('discount', 0))
        stock = int(data.get('stock', 0))
        rating = float(data.get('rating', 4.5))
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid numeric product input values.'}

    image = data.get('image', '').strip() or 'images/phone.jpg'
    description = data.get('description', '').strip()

    if not name or price <= 0 or stock < 0:
        return {'success': False, 'message': 'Product name, valid price (>0), and stock (>=0) are required.'}

    prod_id = execute_query(
        """INSERT INTO products (category_id, product_name, description, price, discount, stock, rating, image, is_active) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)""",
        (category_id, name, description, price, discount, stock, rating, image),
        commit=True
    )

    if not prod_id:
        return {'success': False, 'message': 'Failed to insert product into database.'}

    return {'success': True, 'message': 'Product added successfully!', 'product_id': prod_id}

def update_product(data: dict):
    """
    Updates existing product properties in MySQL.
    """
    try:
        product_id = int(data.get('productId'))
        category_id = int(data.get('categoryId', 1))
        price = float(data.get('price', 0))
        discount = int(data.get('discount', 0))
        stock = int(data.get('stock', 0))
        rating = float(data.get('rating', 4.5))
        is_active = int(data.get('is_active', 1))
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid numeric product inputs.'}

    name = data.get('productName', '').strip()
    image = data.get('image', '').strip()
    description = data.get('description', '').strip()

    if not product_id or not name or price <= 0:
        return {'success': False, 'message': 'Product ID, valid name, and price are required.'}

    res = execute_query(
        """UPDATE products 
           SET category_id = %s, product_name = %s, description = %s, 
               price = %s, discount = %s, stock = %s, rating = %s, image = %s, is_active = %s 
           WHERE product_id = %s""",
        (category_id, name, description, price, discount, stock, rating, image, is_active, product_id),
        commit=True
    )

    if res is None:
        return {'success': False, 'message': 'Failed to update product in database.'}

    return {'success': True, 'message': 'Product updated successfully!'}

def delete_product(product_id: int):
    """
    Deactivates a product (soft delete) to preserve historical order records and receipts.
    """
    try:
        p_id = int(product_id)
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Valid product ID is required.'}

    res = execute_query(
        "UPDATE products SET is_active = 0 WHERE product_id = %s",
        (p_id,),
        commit=True
    )

    if res is None:
        return {'success': False, 'message': 'Failed to deactivate product in database.'}

    return {'success': True, 'message': 'Product deactivated successfully. Historical order items remain intact.'}

def get_admin_users(search_query=None):
    """
    Retrieves registered customer directory from MySQL.
    Never exposes passwords or password hashes.
    """
    query = "SELECT user_id, name, email, phone, address, is_verified, created_at FROM users"
    params = []
    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        query += " WHERE name LIKE %s OR email LIKE %s"
        params.extend([q, q])

    query += " ORDER BY user_id DESC"
    users = execute_query(query, tuple(params), fetchall=True)
    if users:
        for u in users:
            u['is_verified'] = bool(u.get('is_verified', 0))
    return users if users is not None else []

def get_admin_orders(status_filter=None, search_query=None):
    """
    Retrieves all customer orders with buyer contact info from MySQL.
    """
    query = """
        SELECT o.order_id, o.user_id, o.total_amount, o.payment_method, 
               o.shipping_address, o.order_status, o.order_date,
               u.name AS customer_name, u.email AS customer_email, u.phone AS customer_phone
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
    """
    where_clauses = []
    params = []

    if status_filter and status_filter != 'all':
        where_clauses.append("o.order_status = %s")
        params.append(status_filter)

    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        where_clauses.append("(o.order_id LIKE %s OR u.name LIKE %s)")
        params.extend([q, q])

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY o.order_date DESC"
    orders = execute_query(query, tuple(params), fetchall=True)

    if orders:
        for o in orders:
            items = execute_query(
                """SELECT oi.order_item_id, oi.product_id, oi.quantity, oi.price, p.product_name 
                   FROM order_items oi
                   JOIN products p ON oi.product_id = p.product_id
                   WHERE oi.order_id = %s""",
                (o['order_id'],),
                fetchall=True
            )
            o['items'] = items if items else []

    return orders if orders is not None else []

def update_order_status(order_id: int, new_status: str, admin_username: str = 'admin', notes: str = None):
    """
    Updates customer order status: Pending, Confirmed, Processing, Shipped, Delivered, Cancelled.
    Records audit entry in order_status_history and notifies customer by email.
    """
    valid_statuses = ['Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
    if new_status not in valid_statuses:
        return {'success': False, 'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}

    try:
        o_id = int(order_id)
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid order ID format.'}

    # 1. Update order status
    res = execute_query(
        "UPDATE orders SET order_status = %s WHERE order_id = %s",
        (new_status, o_id),
        commit=True
    )

    if res is None:
        return {'success': False, 'message': 'Failed to update order status in database.'}

    # 2. Record in order_status_history audit trail
    execute_query(
        """INSERT INTO order_status_history (order_id, status, changed_by, notes)
           VALUES (%s, %s, %s, %s)""",
        (o_id, new_status, admin_username, notes or f"Status changed to {new_status}"),
        commit=True
    )

    # 3. Notify customer by email asynchronously
    order_info = execute_query(
        """SELECT o.order_id, u.name, u.email 
           FROM orders o 
           JOIN users u ON o.user_id = u.user_id 
           WHERE o.order_id = %s""",
        (o_id,),
        fetchone=True
    )
    if order_info:
        email_service.send_order_status_update_email(
            order_info['email'],
            order_info['name'],
            o_id,
            new_status,
            notes
        )

    return {'success': True, 'message': f'Order #{order_id} status updated to {new_status}. Customer notified.'}
