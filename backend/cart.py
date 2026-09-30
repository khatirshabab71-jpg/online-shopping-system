"""
ShopNow - Online Shopping System
Cart Operations Module (Pure Python)
"""

from database import execute_query
from products import get_product_by_id

# Fallback Memory Cart Storage (Session key mapped)
MOCK_CARTS = {}

def get_user_cart(user_id):
    """
    Retrieves user cart items.
    """
    db_cart = execute_query(
        """SELECT c.cart_id, c.quantity, p.product_id, p.product_name, p.price, p.discount, p.stock, p.image 
           FROM cart c 
           JOIN products p ON c.product_id = p.product_id 
           WHERE c.user_id = %s""",
        (user_id,),
        fetchall=True
    )

    if db_cart:
        return db_cart

    return MOCK_CARTS.get(str(user_id), [])

def add_to_cart(data):
    """
    Adds product to user cart with quantity validation.
    """
    user_id = str(data.get('user_id', 'GUEST'))
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    # Security & Sanity Checks for Quantities
    if not isinstance(quantity, int) or quantity <= 0 or quantity > 100:
        return {'success': False, 'message': 'Invalid product quantity specified.'}

    product = get_product_by_id(product_id)
    if not product:
        return {'success': False, 'message': 'Product not found.'}

    if product['stock'] < quantity:
        return {'success': False, 'message': f'Insufficient stock. Maximum available is {product["stock"]}.'}

    # Add to DB
    execute_query(
        """INSERT INTO cart (user_id, product_id, quantity) 
           VALUES (%s, %s, %s) 
           ON DUPLICATE KEY UPDATE quantity = quantity + %s""",
        (user_id, product_id, quantity, quantity),
        commit=True
    )

    # Fallback memory handler
    if user_id not in MOCK_CARTS:
        MOCK_CARTS[user_id] = []

    user_cart = MOCK_CARTS[user_id]
    existing = next((item for item in user_cart if item['product_id'] == product_id), None)

    if existing:
        existing['quantity'] += quantity
    else:
        user_cart.append({
            'cart_id': 'CART-' + str(len(user_cart) + 1),
            'product_id': product['id'],
            'product_name': product['name'],
            'price': product['price'],
            'stock': product['stock'],
            'quantity': quantity,
            'image': product['image']
        })

    return {'success': True, 'message': 'Product added to cart successfully!'}

def update_cart_quantity(data):
    """
    Updates cart item quantity.
    """
    user_id = str(data.get('user_id', 'GUEST'))
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if quantity <= 0:
        return remove_from_cart(data)

    execute_query(
        "UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s",
        (quantity, user_id, product_id),
        commit=True
    )

    if user_id in MOCK_CARTS:
        for item in MOCK_CARTS[user_id]:
            if item['product_id'] == product_id:
                item['quantity'] = quantity
                break

    return {'success': True, 'message': 'Cart updated.'}

def remove_from_cart(data):
    """
    Removes item from cart.
    """
    user_id = str(data.get('user_id', 'GUEST'))
    product_id = data.get('product_id')

    execute_query(
        "DELETE FROM cart WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
        commit=True
    )

    if user_id in MOCK_CARTS:
        MOCK_CARTS[user_id] = [item for item in MOCK_CARTS[user_id] if item['product_id'] != product_id]

    return {'success': True, 'message': 'Item removed from cart.'}
