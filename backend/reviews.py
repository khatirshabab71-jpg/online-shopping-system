"""
ShopNow - Online Shopping System
Product Reviews & Ratings Management Module (Pure Python + MySQL)
"""

from database import execute_query

def get_product_reviews(product_id: int):
    """
    Retrieves all customer reviews for a product with reviewer names and verified purchase badges.
    """
    try:
        p_id = int(product_id)
    except (ValueError, TypeError):
        return []

    query = """
        SELECT r.review_id, r.product_id, r.user_id, r.rating, 
               r.review_title, r.review_text, r.is_verified_purchase, r.created_at,
               u.name AS reviewer_name
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.product_id = %s
        ORDER BY r.created_at DESC
    """
    reviews = execute_query(query, (p_id,), fetchall=True)
    if reviews:
        for r in reviews:
            r['created_at'] = (r['created_at'] or '').strftime('%Y-%m-%d') if hasattr(r['created_at'], 'strftime') else str(r['created_at'])[:10]
            r['is_verified_purchase'] = bool(r.get('is_verified_purchase', 0))
    return reviews if reviews is not None else []

def get_product_rating_summary(product_id: int):
    """
    Calculates average rating, total review count, and star distribution for a product.
    """
    try:
        p_id = int(product_id)
    except (ValueError, TypeError):
        return {'average_rating': 4.5, 'total_reviews': 0, 'distribution': {5:0, 4:0, 3:0, 2:0, 1:0}}

    res = execute_query(
        "SELECT AVG(rating) as avg_rating, COUNT(*) as total_count FROM reviews WHERE product_id = %s",
        (p_id,),
        fetchone=True
    )

    avg_val = round(float(res['avg_rating']), 1) if res and res.get('avg_rating') else 4.5
    total = int(res['total_count']) if res and res.get('total_count') else 0

    # Star distribution
    dist_rows = execute_query(
        "SELECT rating, COUNT(*) as cnt FROM reviews WHERE product_id = %s GROUP BY rating",
        (p_id,),
        fetchall=True
    )
    dist = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    if dist_rows:
        for d in dist_rows:
            dist[int(d['rating'])] = int(d['cnt'])

    return {
        'average_rating': avg_val,
        'total_reviews': total,
        'distribution': dist
    }

def check_verified_purchase(user_id: int, product_id: int) -> bool:
    """
    Checks if the user has an existing completed or confirmed order containing this product.
    """
    res = execute_query(
        """SELECT oi.order_item_id 
           FROM order_items oi
           JOIN orders o ON oi.order_id = o.order_id
           WHERE o.user_id = %s 
             AND oi.product_id = %s 
             AND o.order_status != 'Cancelled'
           LIMIT 1""",
        (user_id, product_id),
        fetchone=True
    )
    return bool(res)

def add_or_update_review(user_id: int, data: dict):
    """
    Submits or edits a customer review. Recalculates product rating.
    """
    try:
        product_id = int(data.get('product_id'))
        rating = int(data.get('rating', 5))
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid product ID or rating value.'}

    title = data.get('review_title', '').strip()
    text = data.get('review_text', '').strip()

    if rating < 1 or rating > 5:
        return {'success': False, 'message': 'Rating must be an integer between 1 and 5 stars.'}

    if not title or len(title) < 3:
        return {'success': False, 'message': 'Please provide a descriptive review title (at least 3 characters).'}

    if not text or len(text) < 10:
        return {'success': False, 'message': 'Review text must be at least 10 characters long.'}

    is_verified = 1 if check_verified_purchase(user_id, product_id) else 0

    # Upsert review
    res = execute_query(
        """INSERT INTO reviews (product_id, user_id, rating, review_title, review_text, is_verified_purchase)
           VALUES (%s, %s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE 
             rating = VALUES(rating), 
             review_title = VALUES(review_title), 
             review_text = VALUES(review_text),
             is_verified_purchase = VALUES(is_verified_purchase)""",
        (product_id, user_id, rating, title, text, is_verified),
        commit=True
    )

    if res is None:
        return {'success': False, 'message': 'Failed to save review in database.'}

    # Recalculate average rating for product
    _update_product_aggregate_rating(product_id)

    return {'success': True, 'message': 'Review submitted successfully! Thank you for your feedback.'}

def delete_review(user_id: int, review_id: int, is_admin: bool = False):
    """
    Deletes a review by its author or by a store administrator.
    """
    try:
        r_id = int(review_id)
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid review ID.'}

    rev = execute_query("SELECT product_id, user_id FROM reviews WHERE review_id = %s", (r_id,), fetchone=True)
    if not rev:
        return {'success': False, 'message': 'Review not found.'}

    if not is_admin and rev['user_id'] != user_id:
        return {'success': False, 'message': 'Unauthorized to delete this review.'}

    product_id = rev['product_id']
    execute_query("DELETE FROM reviews WHERE review_id = %s", (r_id,), commit=True)

    # Recalculate aggregate rating
    _update_product_aggregate_rating(product_id)

    return {'success': True, 'message': 'Review deleted successfully.'}

def _update_product_aggregate_rating(product_id: int):
    """
    Updates the stored rating column in the products table based on review averages.
    """
    res = execute_query(
        "SELECT AVG(rating) as avg_rating FROM reviews WHERE product_id = %s",
        (product_id,),
        fetchone=True
    )
    if res and res.get('avg_rating') is not None:
        new_rating = round(float(res['avg_rating']), 1)
        execute_query("UPDATE products SET rating = %s WHERE product_id = %s", (new_rating, product_id), commit=True)

def get_admin_reviews(search_query: str = None):
    """
    Retrieves all reviews for admin moderation.
    """
    query = """
        SELECT r.review_id, r.product_id, r.user_id, r.rating, 
               r.review_title, r.review_text, r.is_verified_purchase, r.created_at,
               p.product_name, u.name AS reviewer_name, u.email AS reviewer_email
        FROM reviews r
        JOIN products p ON r.product_id = p.product_id
        JOIN users u ON r.user_id = u.user_id
    """
    params = []
    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        query += " WHERE p.product_name LIKE %s OR r.review_title LIKE %s OR u.name LIKE %s"
        params.extend([q, q, q])

    query += " ORDER BY r.created_at DESC"
    reviews = execute_query(query, tuple(params), fetchall=True)
    if reviews:
        for r in reviews:
            r['created_at'] = (r['created_at'] or '').strftime('%Y-%m-%d') if hasattr(r['created_at'], 'strftime') else str(r['created_at'])[:10]
            r['is_verified_purchase'] = bool(r.get('is_verified_purchase', 0))
    return reviews if reviews is not None else []
