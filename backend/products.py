"""
ShopNow - Online Shopping System
Products Management Module (Pure Python + MySQL)
Supports Search, Multi-Facet Filters, Sorting & Pagination
"""

import math
from database import execute_query

def get_all_products(category_id=None, search_query=None, sort_by=None, in_stock=False, 
                     min_price=None, max_price=None, min_rating=None, 
                     page=1, limit=12, include_inactive=False):
    """
    Retrieves filtered and paginated product list from MySQL.
    """
    where_clauses = []
    params = []

    if not include_inactive:
        where_clauses.append("p.is_active = 1")

    # Category Filter
    if category_id and str(category_id) != 'all':
        if str(category_id).isdigit():
            where_clauses.append("p.category_id = %s")
            params.append(int(category_id))
        else:
            where_clauses.append("LOWER(c.category_name) = LOWER(%s)")
            params.append(str(category_id))

    # Search Query
    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        where_clauses.append("(p.product_name LIKE %s OR p.description LIKE %s OR c.category_name LIKE %s)")
        params.extend([q, q, q])

    # Stock Filter
    if in_stock:
        where_clauses.append("p.stock > 0")

    # Price Range Filters
    if min_price is not None:
        try:
            min_p = float(min_price)
            where_clauses.append("(p.price * (1 - p.discount/100.0)) >= %s")
            params.append(min_p)
        except (ValueError, TypeError):
            pass

    if max_price is not None:
        try:
            max_p = float(max_price)
            where_clauses.append("(p.price * (1 - p.discount/100.0)) <= %s")
            params.append(max_p)
        except (ValueError, TypeError):
            pass

    # Rating Filter
    if min_rating is not None:
        try:
            min_r = float(min_rating)
            where_clauses.append("p.rating >= %s")
            params.append(min_r)
        except (ValueError, TypeError):
            pass

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # 1. Total Count Query for Pagination
    count_query = f"""
        SELECT COUNT(*) as total
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.category_id
        {where_sql}
    """
    count_res = execute_query(count_query, tuple(params), fetchone=True)
    total_records = count_res['total'] if count_res else 0

    # Sorting
    order_sql = "ORDER BY p.product_id ASC"
    if sort_by == 'price-low':
        order_sql = "ORDER BY (p.price * (1 - p.discount/100.0)) ASC"
    elif sort_by == 'price-high':
        order_sql = "ORDER BY (p.price * (1 - p.discount/100.0)) DESC"
    elif sort_by == 'rating':
        order_sql = "ORDER BY p.rating DESC"
    elif sort_by == 'newest':
        order_sql = "ORDER BY p.product_id DESC"

    # Pagination bounds
    try:
        p_num = max(1, int(page))
        l_num = max(1, min(100, int(limit)))
    except (ValueError, TypeError):
        p_num = 1
        l_num = 12

    offset = (p_num - 1) * l_num
    total_pages = max(1, math.ceil(total_records / l_num)) if total_records > 0 else 1

    # 2. Main Data Query with LIMIT and OFFSET
    data_query = f"""
        SELECT p.product_id, p.category_id, p.product_name, p.description, 
               p.price, p.discount, p.stock, p.rating, p.image, p.is_active, p.created_at,
               c.category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.category_id
        {where_sql}
        {order_sql}
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [l_num, offset]

    db_products = execute_query(data_query, tuple(data_params), fetchall=True)
    if db_products is None:
        return None

    # Harmonize keys for frontend compatibility
    for p in db_products:
        p['id'] = p['product_id']
        p['name'] = p['product_name']

    return {
        'products': db_products,
        'total': total_records,
        'page': p_num,
        'limit': l_num,
        'total_pages': total_pages
    }

def get_product_by_id(product_id: int):
    """
    Fetches details for a single product by ID from MySQL.
    """
    if not product_id:
        return None

    db_product = execute_query(
        """SELECT p.product_id, p.category_id, p.product_name, p.description, 
                  p.price, p.discount, p.stock, p.rating, p.image, p.is_active, p.created_at,
                  c.category_name 
           FROM products p 
           LEFT JOIN categories c ON p.category_id = c.category_id
           WHERE p.product_id = %s""",
        (product_id,),
        fetchone=True
    )

    if db_product:
        db_product['id'] = db_product['product_id']
        db_product['name'] = db_product['product_name']

    return db_product

def get_all_categories():
    """
    Fetches all product categories from MySQL.
    """
    return execute_query("SELECT category_id, category_name FROM categories ORDER BY category_id ASC", fetchall=True)
