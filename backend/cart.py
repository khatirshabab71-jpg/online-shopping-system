"""
ShopNow - Online Shopping System
Cart Operations Module (Pure Python + MySQL)
"""

from database import execute_query
from products import get_product_by_id

def get_user_cart(user_id: int):
    """
    Retrieves the authenticated user's shopping cart items directly from MySQL.
    Calculates current effective prices and line subtotals.
    """
    db_cart = execute_query(
        """SELECT c.cart_id, c.quantity, p.product_id, p.product_name, 
                  p.price, p.discount, p.stock, p.image, p.is_active,
                  c.user_id
           FROM cart c 
           JOIN products p ON c.product_id = p.product_id 
           WHERE c.user_id = %s AND p.is_active = 1""",
        (user_id,),
        fetchall=True
    )

    if db_cart is None:
        return None

    items = []
    subtotal = 0.0

    for item in db_cart:
        price = float(item['price'])
        discount = float(item.get('discount', 0))
        unit_price = round(price * (1.0 - discount / 100.0), 2)
        qty = int(item['quantity'])
        line_total = round(unit_price * qty, 2)
        subtotal += line_total

        items.append({
            'cart_id': item['cart_id'],
            'product_id': item['product_id'],
            'id': item['product_id'],
            'product_name': item['product_name'],
            'name': item['product_name'],
            'price': unit_price,
            'original_price': price,
            'discount': discount,
            'stock': item['stock'],
            'quantity': qty,
            'image': item['image'],
            'line_total': line_total
        })

    return {
        'items': items,
        'subtotal': round(subtotal, 2),
        'item_count': sum(i['quantity'] for i in items)
    }

def add_to_cart(user_id: int, data: dict):
    """
    Adds a product to user's cart with server-side quantity and stock validation.
    """
    try:
        product_id = int(data.get('product_id'))
        quantity = int(data.get('quantity', 1))
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid product or quantity input.'}

    if quantity <= 0:
        return {'success': False, 'message': 'Quantity must be a positive whole number.'}

    product = get_product_by_id(product_id)
    if not product or product.get('is_active') == 0:
        return {'success': False, 'message': 'Product is not available for purchase.'}

    # Check existing quantity in cart
    existing = execute_query(
        "SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
        fetchone=True
    )

    current_qty = existing['quantity'] if existing else 0
    new_qty = current_qty + quantity

    if new_qty > product['stock']:
        return {
            'success': False, 
            'message': f"Insufficient stock. Available: {product['stock']}, already in cart: {current_qty}."
        }

    # Upsert into cart table
    res = execute_query(
        """INSERT INTO cart (user_id, product_id, quantity) 
           VALUES (%s, %s, %s) 
           ON DUPLICATE KEY UPDATE quantity = quantity + %s""",
        (user_id, product_id, quantity, quantity),
        commit=True
    )

    if res is None:
        return {'success': False, 'message': 'Failed to add item to cart. Database error.'}

    return {'success': True, 'message': f"Added '{product['product_name']}' to your cart!"}

def update_cart_quantity(user_id: int, data: dict):
    """
    Updates the quantity of an item in the user's cart with stock validation.
    """
    try:
        product_id = int(data.get('product_id'))
        quantity = int(data.get('quantity', 1))
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid product or quantity input.'}

    if quantity <= 0:
        return remove_from_cart(user_id, data)

    product = get_product_by_id(product_id)
    if not product:
        return {'success': False, 'message': 'Product not found.'}

    if quantity > product['stock']:
        return {
            'success': False,
            'message': f"Stock limit reached. Maximum available is {product['stock']}."
        }

    res = execute_query(
        "UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s",
        (quantity, user_id, product_id),
        commit=True
    )

    if res is None:
        return {'success': False, 'message': 'Failed to update cart.'}

    return {'success': True, 'message': 'Cart updated successfully.'}

def remove_from_cart(user_id: int, data: dict):
    """
    Removes a product from the user's cart.
    """
    try:
        product_id = int(data.get('product_id'))
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid product ID.'}

    res = execute_query(
        "DELETE FROM cart WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
        commit=True
    )

    if res is None:
        return {'success': False, 'message': 'Failed to remove item from cart.'}

    return {'success': True, 'message': 'Item removed from cart.'}

def clear_user_cart(user_id: int):
    """
    Clears all items in the user's cart.
    """
    res = execute_query("DELETE FROM cart WHERE user_id = %s", (user_id,), commit=True)
    if res is None:
        return {'success': False, 'message': 'Failed to clear cart.'}
    return {'success': True, 'message': 'Cart cleared.'}
