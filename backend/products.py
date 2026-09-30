"""
ShopNow - Online Shopping System
Products Management Module (Pure Python)
"""

from database import execute_query

# Sample Fallback Products Data
FALLBACK_PRODUCTS = [
    {
        'id': 1,
        'product_id': 1,
        'name': 'Pro Wireless Smartphone 128GB',
        'category_id': 1,
        'category_name': 'Electronics',
        'price': 699.99,
        'discount': 15,
        'stock': 15,
        'rating': 4.5,
        'image': 'images/phone.jpg',
        'description': 'Experience cutting-edge smartphone technology with high-resolution camera system, long-lasting battery, and superfast processing power.'
    },
    {
        'id': 2,
        'product_id': 2,
        'name': 'UltraBook Slim 15 Pro Core i7',
        'category_id': 2,
        'category_name': 'Laptops',
        'price': 1199.00,
        'discount': 0,
        'stock': 8,
        'rating': 4.9,
        'image': 'images/laptop.jpg',
        'description': 'Lightweight ultra-performance laptop designed for software development, graphic creation, and multi-tasking productivity.'
    },
    {
        'id': 3,
        'product_id': 3,
        'name': 'Active Noise Cancelling Wireless Headphones',
        'category_id': 4,
        'category_name': 'Accessories',
        'price': 149.99,
        'discount': 20,
        'stock': 25,
        'rating': 4.2,
        'image': 'images/headphones.jpg',
        'description': 'Immersive sound quality with active noise cancellation, built-in HD microphone, and 30-hour playback battery life.'
    },
    {
        'id': 4,
        'product_id': 4,
        'name': 'Smart Fitness Watch Series 5',
        'category_id': 4,
        'category_name': 'Accessories',
        'price': 89.99,
        'discount': 0,
        'stock': 18,
        'rating': 4.6,
        'image': 'images/watch.jpg',
        'description': 'Track heart rate, daily steps, sleep patterns, and sports activities with water-resistant sleek OLED touchscreen.'
    },
    {
        'id': 5,
        'product_id': 5,
        'name': 'Men Classic Slim Fit Denim Jacket',
        'category_id': 3,
        'category_name': 'Fashion',
        'price': 59.99,
        'discount': 10,
        'stock': 30,
        'rating': 4.4,
        'image': 'images/jacket.jpg',
        'description': 'Stylish premium denim jacket crafted from comfortable breathable cotton blend. Suitable for all casual occasions.'
    },
    {
        'id': 6,
        'product_id': 6,
        'name': 'Automatic Stainless Steel Coffee Maker',
        'category_id': 5,
        'category_name': 'Home & Kitchen',
        'price': 129.50,
        'discount': 5,
        'stock': 12,
        'rating': 4.7,
        'image': 'images/coffeemaker.jpg',
        'description': 'Programmable drip coffee machine with thermal stainless steel carafe, automatic shut-off, and built-in bean grinder.'
    }
]

def get_all_products(category_id=None, search_query=None, sort_by=None, in_stock=False):
    """
    Retrieves product list with search keyword, category filter, and sorting.
    """
    # 1. Try MySQL Database
    db_products = execute_query(
        """SELECT p.*, c.category_name 
           FROM products p 
           LEFT JOIN categories c ON p.category_id = c.category_id""",
        fetchall=True
    )

    products = db_products if db_products else FALLBACK_PRODUCTS

    # Filter by Category
    if category_id and str(category_id) != 'all':
        products = [p for p in products if str(p.get('category_id')) == str(category_id) or str(p.get('category_name')).lower() == str(category_id).lower()]

    # Filter by Search Query
    if search_query:
        q = search_query.strip().lower()
        products = [p for p in products if q in p['name'].lower() or q in p['description'].lower() or q in p.get('category_name', '').lower()]

    # Filter by Stock Status
    if in_stock:
        products = [p for p in products if p['stock'] > 0]

    # Sorting
    if sort_by == 'price-low':
        products.sort(key=lambda p: float(p['price']) * (1 - float(p.get('discount', 0))/100))
    elif sort_by == 'price-high':
        products.sort(key=lambda p: float(p['price']) * (1 - float(p.get('discount', 0))/100), reverse=True)
    elif sort_by == 'rating':
        products.sort(key=lambda p: float(p.get('rating', 0)), reverse=True)

    # Standardize keys
    for p in products:
        if 'product_id' in p and 'id' not in p:
            p['id'] = p['product_id']

    return products

def get_product_by_id(product_id):
    """
    Fetches details for a single product by ID.
    """
    db_product = execute_query(
        """SELECT p.*, c.category_name 
           FROM products p 
           LEFT JOIN categories c ON p.category_id = c.category_id
           WHERE p.product_id = %s""",
        (product_id,),
        fetchone=True
    )

    if db_product:
        db_product['id'] = db_product['product_id']
        return db_product

    # Fallback lookup
    for p in FALLBACK_PRODUCTS:
        if str(p['id']) == str(product_id):
            return p

    return None
