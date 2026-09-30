"""
ShopNow - Online Shopping System
Order Placement & Fulfillment Module (Pure Python)
"""

from datetime import datetime
from database import execute_query
from products import get_product_by_id

# Fallback Orders Memory
MOCK_ORDERS = [
    {
        'order_id': 10024,
        'user_id': 101,
        'customer_name': 'John Doe',
        'total_amount': 714.99,
        'payment_method': 'Cash on Delivery',
        'shipping_address': '123 University Campus St, Apt 4B, NY',
        'order_status': 'Pending',
        'order_date': '2026-09-13',
        'items': [
            {'product_id': 1, 'product_name': 'Pro Wireless Smartphone 128GB', 'quantity': 1, 'price': 699.99}
        ]
    }
]

def create_order(data):
    """
    Validates cart items & stock, creates order record and line items.
    """
    user_id = data.get('user_id', 101)
    customer_name = data.get('fullName', 'Customer').strip()
    shipping_address = data.get('address', '').strip()
    payment_method = data.get('paymentMethod', 'Cash on Delivery')
    items = data.get('items', [])

    if not shipping_address or not items:
        return {'success': False, 'message': 'Shipping address and items required.'}

    total_amount = 0.0
    order_items_to_save = []

    # 1. Validate Stock & Calculate Total Amount
    for item in items:
        prod_id = item.get('product_id')
        qty = item.get('quantity', 1)

        product = get_product_by_id(prod_id)
        if not product:
            return {'success': False, 'message': f'Product ID {prod_id} not found.'}

        if product['stock'] < qty:
            return {'success': False, 'message': f'Product "{product["name"]}" has insufficient stock.'}

        unit_price = float(product['price']) * (1 - float(product.get('discount', 0))/100)
        item_subtotal = unit_price * qty
        total_amount += item_subtotal

        order_items_to_save.append({
            'product_id': prod_id,
            'product_name': product['name'],
            'quantity': qty,
            'price': unit_price
        })

    shipping_fee = 15.00
    final_total = round(total_amount + shipping_fee, 2)
    order_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 2. Try DB Insertion
    order_id = execute_query(
        """INSERT INTO orders (user_id, total_amount, payment_method, shipping_address, order_status, order_date) 
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (user_id, final_total, payment_method, shipping_address, 'Pending', order_date_str),
        commit=True
    )

    if order_id:
        for oi in order_items_to_save:
            execute_query(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (order_id, oi['product_id'], oi['quantity'], oi['price']),
                commit=True
            )
            # Deduct stock
            execute_query(
                "UPDATE products SET stock = stock - %s WHERE product_id = %s",
                (oi['quantity'], oi['product_id']),
                commit=True
            )
        # Clear cart
        execute_query("DELETE FROM cart WHERE user_id = %s", (user_id,), commit=True)
        return {'success': True, 'message': 'Order placed successfully!', 'order_id': order_id}

    # 3. Fallback Memory Save
    new_order_id = 10000 + len(MOCK_ORDERS) + 1
    new_order = {
        'order_id': new_order_id,
        'user_id': user_id,
        'customer_name': customer_name,
        'total_amount': final_total,
        'payment_method': payment_method,
        'shipping_address': shipping_address,
        'order_status': 'Pending',
        'order_date': order_date_str[:10],
        'items': order_items_to_save
    }
    MOCK_ORDERS.insert(0, new_order)

    return {'success': True, 'message': 'Order placed successfully!', 'order_id': new_order_id}

def get_user_orders(user_id):
    """
    Retrieves previous orders for a customer.
    """
    db_orders = execute_query(
        "SELECT * FROM orders WHERE user_id = %s ORDER BY order_date DESC",
        (user_id,),
        fetchall=True
    )

    if db_orders:
        return db_orders

    return MOCK_ORDERS

def get_order_by_id(order_id):
    """
    Fetches single order details and item breakdown.
    """
    db_order = execute_query(
        "SELECT * FROM orders WHERE order_id = %s",
        (order_id,),
        fetchone=True
    )

    if db_order:
        items = execute_query(
            """SELECT oi.*, p.product_name 
               FROM order_items oi 
               JOIN products p ON oi.product_id = p.product_id 
               WHERE oi.order_id = %s""",
            (order_id,),
            fetchall=True
        )
        db_order['items'] = items if items else []
        return db_order

    # Fallback search
    for o in MOCK_ORDERS:
        if str(o['order_id']) == str(order_id):
            return o

    return None
