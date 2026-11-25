"""
ShopNow - Online Shopping System
Order Placement & Fulfillment Module (Pure Python + MySQL Atomic Transactions)
Includes status history audit logging and asynchronous email notifications.
"""

from datetime import datetime
from database import get_db_connection, execute_query
from config import FIXED_SHIPPING_FEE
import email_service

def create_order(user_id: int, data: dict):
    """
    Places an order in a single atomic MySQL transaction.
    - Re-checks stock and locks products (FOR UPDATE)
    - Computes totals strictly from database prices
    - Inserts order header and order_items
    - Reduces product stock
    - Clears user's cart
    - Logs status change into order_status_history
    - Commits transaction; on any error rolls back completely
    - Fires order confirmation email in background thread without delaying HTTP response.
    """
    address = data.get('address', '').strip()
    city = data.get('city', '').strip()
    postal_code = data.get('postalCode', '').strip()

    full_address_parts = [p for p in [address, city, postal_code] if p]
    full_address = ', '.join(full_address_parts) if full_address_parts else address

    if not full_address or len(full_address) < 5:
        return {'success': False, 'message': 'Complete delivery address is required.'}

    conn = get_db_connection()
    if not conn:
        return {'success': False, 'message': 'Database connection error. Could not place order.'}

    cursor = None
    try:
        conn.autocommit = False
        cursor = conn.cursor(dictionary=True)

        # 1. Fetch user's cart with row locking (FOR UPDATE)
        cursor.execute("""
            SELECT c.cart_id, c.quantity, p.product_id, p.product_name, 
                   p.price, p.discount, p.stock, p.is_active
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = %s
            FOR UPDATE
        """, (user_id,))
        cart_items = cursor.fetchall()

        if not cart_items:
            conn.rollback()
            cursor.close()
            conn.close()
            return {'success': False, 'message': 'Your shopping cart is empty.'}

        # 2. Validate stock & calculate server-side totals
        order_items_to_save = []
        subtotal = 0.0

        for item in cart_items:
            if item.get('is_active') == 0:
                conn.rollback()
                cursor.close()
                conn.close()
                return {'success': False, 'message': f"Product '{item['product_name']}' is no longer active."}

            qty = item['quantity']
            if qty <= 0:
                conn.rollback()
                cursor.close()
                conn.close()
                return {'success': False, 'message': f"Invalid quantity for '{item['product_name']}'."}

            if item['stock'] < qty:
                conn.rollback()
                cursor.close()
                conn.close()
                return {
                    'success': False, 
                    'message': f"Insufficient stock for '{item['product_name']}'. Only {item['stock']} available."
                }

            price = float(item['price'])
            discount = float(item.get('discount', 0))
            unit_price = round(price * (1.0 - discount / 100.0), 2)
            line_total = round(unit_price * qty, 2)
            subtotal += line_total

            order_items_to_save.append({
                'product_id': item['product_id'],
                'product_name': item['product_name'],
                'quantity': qty,
                'price': unit_price
            })

        final_total = round(subtotal + FIXED_SHIPPING_FEE, 2)
        order_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 3. Insert into orders table (Cash on Delivery)
        cursor.execute("""
            INSERT INTO orders (user_id, total_amount, payment_method, shipping_address, order_status, order_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, final_total, 'Cash on Delivery', full_address, 'Pending', order_date_str))
        
        order_id = cursor.lastrowid
        if not order_id:
            raise Exception("Failed to insert order record.")

        # 4. Insert each order item and decrement product stock
        for oi in order_items_to_save:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, oi['product_id'], oi['quantity'], oi['price']))

            cursor.execute("""
                UPDATE products SET stock = stock - %s WHERE product_id = %s
            """, (oi['quantity'], oi['product_id']))

        # 5. Clear cart for user
        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))

        # 6. Insert initial status history record
        cursor.execute("""
            INSERT INTO order_status_history (order_id, status, changed_by, notes, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_id, 'Pending', 'customer', 'Cash on Delivery order placed', order_date_str))

        # 7. Commit atomic transaction
        conn.commit()
        cursor.close()
        conn.close()

        # 8. Asynchronously send email notification (non-blocking)
        user_info = execute_query("SELECT name, email FROM users WHERE user_id = %s", (user_id,), fetchone=True)
        if user_info:
            email_service.send_order_placed_email(
                user_info['email'],
                user_info['name'],
                order_id,
                final_total,
                full_address,
                order_items_to_save
            )

        return {
            'success': True,
            'message': 'Order placed successfully!',
            'order_id': order_id,
            'total_amount': final_total
        }

    except Exception as err:
        if conn:
            try:
                conn.rollback()
                if cursor:
                    cursor.close()
                conn.close()
            except Exception:
                pass
        print(f"Transaction Rollback Error: {err}")
        return {'success': False, 'message': f'Order could not be saved: {str(err)}'}

def get_user_orders(user_id: int):
    """
    Retrieves previous orders placed by the authenticated customer only.
    """
    db_orders = execute_query(
        """SELECT order_id, user_id, total_amount, payment_method, 
                  shipping_address, order_status, order_date 
           FROM orders 
           WHERE user_id = %s 
           ORDER BY order_date DESC""",
        (user_id,),
        fetchall=True
    )
    return db_orders if db_orders is not None else []

def get_order_by_id(order_id: int, user_id: int = None, is_admin: bool = False):
    """
    Fetches full order details including line items and status history.
    Enforces ownership: non-admin users can only view their own orders.
    """
    db_order = execute_query(
        """SELECT o.order_id, o.user_id, o.total_amount, o.payment_method, 
                  o.shipping_address, o.order_status, o.order_date,
                  u.name AS customer_name, u.email AS customer_email, u.phone AS customer_phone
           FROM orders o
           JOIN users u ON o.user_id = u.user_id
           WHERE o.order_id = %s""",
        (order_id,),
        fetchone=True
    )

    if not db_order:
        return None

    # Check permission
    if not is_admin and user_id is not None and db_order['user_id'] != user_id:
        return None

    items = execute_query(
        """SELECT oi.order_item_id, oi.order_id, oi.product_id, 
                  oi.quantity, oi.price, p.product_name, p.image
           FROM order_items oi
           JOIN products p ON oi.product_id = p.product_id
           WHERE oi.order_id = %s""",
        (order_id,),
        fetchall=True
    )

    history = execute_query(
        """SELECT status, changed_by, notes, created_at 
           FROM order_status_history 
           WHERE order_id = %s 
           ORDER BY created_at ASC""",
        (order_id,),
        fetchall=True
    )

    db_order['items'] = items if items else []
    db_order['history'] = history if history else []
    return db_order
