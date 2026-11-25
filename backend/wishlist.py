"""
ShopNow - Online Shopping System
Customer Wishlist & Saved Products Module (Pure Python + MySQL)
"""

from database import execute_query, get_db_connection
from products import get_product_by_id

def get_user_wishlist(user_id: int):
    """
    Retrieves the authenticated customer's saved wishlist items from MySQL.
    """
    query = """
        SELECT w.wishlist_id, w.created_at as saved_at,
               p.product_id, p.product_name, p.price, p.discount, p.stock, 
               p.rating, p.image, p.is_active, c.category_name
        FROM wishlist w
        JOIN products p ON w.product_id = p.product_id
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE w.user_id = %s
        ORDER BY w.created_at DESC
    """
    db_items = execute_query(query, (user_id,), fetchall=True)
    if db_items is None:
        return None

    items = []
    for item in db_items:
        price = float(item['price'])
        discount = float(item.get('discount', 0))
        unit_price = round(price * (1.0 - discount / 100.0), 2)

        items.append({
            'wishlist_id': item['wishlist_id'],
            'product_id': item['product_id'],
            'id': item['product_id'],
            'product_name': item['product_name'],
            'name': item['product_name'],
            'price': unit_price,
            'original_price': price,
            'discount': discount,
            'stock': item['stock'],
            'rating': float(item.get('rating', 4.5)),
            'image': item['image'],
            'is_active': item['is_active'],
            'category_name': item.get('category_name', 'General'),
            'saved_at': (item['saved_at'] or '').strftime('%Y-%m-%d') if hasattr(item['saved_at'], 'strftime') else str(item['saved_at'])[:10]
        })

    return {'items': items, 'total_count': len(items)}

def add_to_wishlist(user_id: int, product_id: int):
    """
    Saves a product to user's wishlist in MySQL.
    Repeat-safe (unique user/product pair).
    """
    try:
        p_id = int(product_id)
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid product ID.'}

    product = get_product_by_id(p_id)
    if not product or product.get('is_active') == 0:
        return {'success': False, 'message': 'Product not found or unavailable.'}

    res = execute_query(
        """INSERT INTO wishlist (user_id, product_id) VALUES (%s, %s)
           ON DUPLICATE KEY UPDATE created_at = CURRENT_TIMESTAMP""",
        (user_id, p_id),
        commit=True
    )

    if res is None:
        return {'success': False, 'message': 'Could not save item to wishlist.'}

    return {'success': True, 'message': f"Added '{product['product_name']}' to your wishlist!"}

def remove_from_wishlist(user_id: int, product_id: int):
    """
    Removes a product from user's wishlist in MySQL.
    """
    try:
        p_id = int(product_id)
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid product ID.'}

    res = execute_query(
        "DELETE FROM wishlist WHERE user_id = %s AND product_id = %s",
        (user_id, p_id),
        commit=True
    )

    if res is None:
        return {'success': False, 'message': 'Could not remove item from wishlist.'}

    return {'success': True, 'message': 'Item removed from your wishlist.'}

def move_to_cart(user_id: int, product_id: int):
    """
    Atomically moves an item from wishlist to active shopping cart:
    Validates stock, upserts into cart, and removes from wishlist only upon success.
    """
    try:
        p_id = int(product_id)
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid product ID.'}

    product = get_product_by_id(p_id)
    if not product or product.get('is_active') == 0:
        return {'success': False, 'message': 'Product is not available.'}

    if product['stock'] < 1:
        return {'success': False, 'message': 'Cannot move to cart: Product is currently out of stock.'}

    conn = get_db_connection()
    if not conn:
        return {'success': False, 'message': 'Database connection error.'}

    try:
        conn.autocommit = False
        cursor = conn.cursor()

        # Add to cart
        cursor.execute(
            """INSERT INTO cart (user_id, product_id, quantity) 
               VALUES (%s, %s, 1) 
               ON DUPLICATE KEY UPDATE quantity = quantity + 1""",
            (user_id, p_id)
        )

        # Remove from wishlist
        cursor.execute("DELETE FROM wishlist WHERE user_id = %s AND product_id = %s", (user_id, p_id))

        conn.commit()
        cursor.close()
        conn.close()

        return {'success': True, 'message': f"Moved '{product['product_name']}' to your cart!"}
    except Exception as e:
        if conn:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
        return {'success': False, 'message': f'Failed to move item to cart: {e}'}
