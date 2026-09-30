"""
ShopNow - Online Shopping System
Admin Management Backend Module (Pure Python)
"""

from database import execute_query
from products import get_all_products, get_product_by_id, FALLBACK_PRODUCTS
from auth import MOCK_USERS
from orders import MOCK_ORDERS

def admin_login(data):
    """
    Authenticates administrator access.
    """
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    # DB Admin check
    db_admin = execute_query(
        "SELECT * FROM admins WHERE username = %s AND password = %s",
        (username, password),
        fetchone=True
    )

    if db_admin or (username == 'admin' and password == 'admin123'):
        return {'success': True, 'message': 'Admin authenticated.', 'admin': {'username': username, 'role': 'Administrator'}}

    return {'success': False, 'message': 'Invalid admin credentials.'}

def get_dashboard_metrics():
    """
    Calculates system metrics: total products, total users, total orders, total sales, pending orders, low stock.
    """
    products = get_all_products()
    orders = MOCK_ORDERS
    users = MOCK_USERS

    total_products = len(products)
    total_users = len(users)
    total_orders = len(orders)
    total_sales = sum(float(o.get('total_amount', 0)) for o in orders)
    pending_orders = len([o for o in orders if o.get('order_status') == 'Pending'])
    low_stock = len([p for p in products if int(p.get('stock', 0)) < 5])

    return {
        'total_products': total_products,
        'total_users': total_users,
        'total_orders': total_orders,
        'total_sales': round(total_sales, 2),
        'pending_orders': pending_orders,
        'low_stock': low_stock
    }

def add_product(data):
    """
    Adds a new product to inventory.
    """
    name = data.get('productName', '').strip()
    category_id = int(data.get('categoryId', 1))
    price = float(data.get('price', 0))
    discount = int(data.get('discount', 0))
    stock = int(data.get('stock', 0))
    rating = float(data.get('rating', 4.5))
    image = data.get('image', '').strip()
    description = data.get('description', '').strip()

    if not name or price <= 0 or stock < 0 or not image:
        return {'success': False, 'message': 'Invalid product data inputs.'}

    # DB insert
    prod_id = execute_query(
        """INSERT INTO products (category_id, product_name, description, price, discount, stock, rating, image) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (category_id, name, description, price, discount, stock, rating, image),
        commit=True
    )

    if not prod_id:
        # Fallback memory
        new_id = len(FALLBACK_PRODUCTS) + 1
        FALLBACK_PRODUCTS.append({
            'id': new_id,
            'product_id': new_id,
            'name': name,
            'category_id': category_id,
            'category_name': 'General',
            'price': price,
            'discount': discount,
            'stock': stock,
            'rating': rating,
            'image': image,
            'description': description
        })
        prod_id = new_id

    return {'success': True, 'message': 'Product added successfully!', 'product_id': prod_id}

def update_product(data):
    """
    Updates existing product properties.
    """
    product_id = data.get('productId')
    name = data.get('productName', '').strip()
    category_id = int(data.get('categoryId', 1))
    price = float(data.get('price', 0))
    discount = int(data.get('discount', 0))
    stock = int(data.get('stock', 0))
    rating = float(data.get('rating', 4.5))
    image = data.get('image', '').strip()
    description = data.get('description', '').strip()

    if not product_id or not name:
        return {'success': False, 'message': 'Product ID and Name required.'}

    execute_query(
        """UPDATE products 
           SET category_id = %s, product_name = %s, description = %s, price = %s, discount = %s, stock = %s, rating = %s, image = %s 
           WHERE product_id = %s""",
        (category_id, name, description, price, discount, stock, rating, image, product_id),
        commit=True
    )

    for p in FALLBACK_PRODUCTS:
        if str(p['id']) == str(product_id):
            p['name'] = name
            p['category_id'] = category_id
            p['price'] = price
            p['discount'] = discount
            p['stock'] = stock
            p['rating'] = rating
            p['image'] = image
            p['description'] = description
            break

    return {'success': True, 'message': 'Product updated successfully!'}

def delete_product(product_id):
    """
    Deletes product from store inventory.
    """
    if not product_id:
        return {'success': False, 'message': 'Product ID required.'}

    execute_query("DELETE FROM products WHERE product_id = %s", (product_id,), commit=True)

    global FALLBACK_PRODUCTS
    FALLBACK_PRODUCTS = [p for p in FALLBACK_PRODUCTS if str(p['id']) != str(product_id)]

    return {'success': True, 'message': 'Product deleted successfully!'}

def update_order_status(order_id, new_status):
    """
    Updates customer order status: Pending, Confirmed, Processing, Shipped, Delivered, Cancelled.
    """
    valid_statuses = ['Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
    if new_status not in valid_statuses:
        return {'success': False, 'message': 'Invalid order status value.'}

    execute_query("UPDATE orders SET order_status = %s WHERE order_id = %s", (new_status, order_id), commit=True)

    for o in MOCK_ORDERS:
        if str(o['order_id']) == str(order_id):
            o['order_status'] = new_status
            break

    return {'success': True, 'message': f'Order #{order_id} status updated to {new_status}.'}
