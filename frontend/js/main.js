/**
 * ShopNow - Online Shopping System
 * Main Global Utility JavaScript (Pure Vanilla JS)
 */

// Global Storage Keys
const STORAGE_KEYS = {
    USER: 'shopnow_user_session',
    ADMIN: 'shopnow_admin_session',
    CART: 'shopnow_cart_items',
    ORDERS: 'shopnow_orders_history',
    PRODUCTS: 'shopnow_products_data'
};

// Backend API Base URL
const API_BASE_URL = 'http://localhost:8000/api';

/**
 * Universal Async API Fetch Helper for Python Backend Communication
 */
async function apiFetch(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        if (!response.ok) return null;
        return await response.json();
    } catch (err) {
        // Graceful fallback to client-side storage when server is offline
        return null;
    }
}

// Initial Sample Products Data (Used for Frontend Demo & Local Storage Fallback)
const DEFAULT_PRODUCTS = [
    {
        id: 1,
        name: 'Pro Wireless Smartphone 128GB',
        category_id: 1,
        category_name: 'Electronics',
        price: 699.99,
        discount: 15,
        stock: 15,
        rating: 4.5,
        image: 'images/phone.jpg',
        description: 'Experience cutting-edge smartphone technology with high-resolution camera system, long-lasting battery, and superfast processing power.'
    },
    {
        id: 2,
        name: 'UltraBook Slim 15 Pro Core i7',
        category_id: 2,
        category_name: 'Laptops',
        price: 1199.00,
        discount: 0,
        stock: 8,
        rating: 4.9,
        image: 'images/laptop.jpg',
        description: 'Lightweight ultra-performance laptop designed for software development, graphic creation, and multi-tasking productivity.'
    },
    {
        id: 3,
        name: 'Active Noise Cancelling Wireless Headphones',
        category_id: 4,
        category_name: 'Accessories',
        price: 149.99,
        discount: 20,
        stock: 25,
        rating: 4.2,
        image: 'images/headphones.jpg',
        description: 'Immersive sound quality with active noise cancellation, built-in HD microphone, and 30-hour playback battery life.'
    },
    {
        id: 4,
        name: 'Smart Fitness Watch Series 5',
        category_id: 4,
        category_name: 'Accessories',
        price: 89.99,
        discount: 0,
        stock: 18,
        rating: 4.6,
        image: 'images/watch.jpg',
        description: 'Track heart rate, daily steps, sleep patterns, and sports activities with water-resistant sleek OLED touchscreen.'
    },
    {
        id: 5,
        name: 'Men Classic Slim Fit Denim Jacket',
        category_id: 3,
        category_name: 'Fashion',
        price: 59.99,
        discount: 10,
        stock: 30,
        rating: 4.4,
        image: 'images/jacket.jpg',
        description: 'Stylish premium denim jacket crafted from comfortable breathable cotton blend. Suitable for all casual occasions.'
    },
    {
        id: 6,
        name: 'Automatic Stainless Steel Coffee Maker',
        category_id: 5,
        category_name: 'Home & Kitchen',
        price: 129.50,
        discount: 5,
        stock: 12,
        rating: 4.7,
        image: 'images/coffeemaker.jpg',
        description: 'Programmable drip coffee machine with thermal stainless steel carafe, automatic shut-off, and built-in bean grinder.'
    }
];

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
    initLocalProductsStore();
    updateHeaderCartCount();
    setupHeaderUserUI();
});

/**
 * Initialize Products in Local Storage if not present
 */
function initLocalProductsStore() {
    if (!localStorage.getItem(STORAGE_KEYS.PRODUCTS)) {
        localStorage.setItem(STORAGE_KEYS.PRODUCTS, JSON.stringify(DEFAULT_PRODUCTS));
    }
}

/**
 * Get Products List from Storage
 */
function getProducts() {
    initLocalProductsStore();
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.PRODUCTS)) || DEFAULT_PRODUCTS;
}

/**
 * Save Products List to Storage
 */
function saveProducts(products) {
    localStorage.setItem(STORAGE_KEYS.PRODUCTS, JSON.stringify(products));
}

/**
 * Get Current Logged-in Customer Session
 */
function getCurrentUser() {
    const userJson = localStorage.getItem(STORAGE_KEYS.USER);
    return userJson ? JSON.parse(userJson) : null;
}

/**
 * Set Customer Session
 */
function setCurrentUser(user) {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
}

/**
 * Logout Customer
 */
function logoutUser() {
    localStorage.removeItem(STORAGE_KEYS.USER);
    window.location.href = 'login.html';
}

/**
 * Get Current Admin Session
 */
function getAdminSession() {
    const adminJson = localStorage.getItem(STORAGE_KEYS.ADMIN);
    return adminJson ? JSON.parse(adminJson) : null;
}

/**
 * Set Admin Session
 */
function setAdminSession(adminData) {
    localStorage.setItem(STORAGE_KEYS.ADMIN, JSON.stringify(adminData));
}

/**
 * Logout Admin
 */
function logoutAdmin() {
    localStorage.removeItem(STORAGE_KEYS.ADMIN);
    window.location.href = 'login.html';
}

/**
 * Cart Storage Operations
 */
function getCart() {
    const cartJson = localStorage.getItem(STORAGE_KEYS.CART);
    return cartJson ? JSON.parse(cartJson) : [];
}

function saveCart(cartItems) {
    localStorage.setItem(STORAGE_KEYS.CART, JSON.stringify(cartItems));
    updateHeaderCartCount();
}

/**
 * Update Header Cart Count Badge
 */
function updateHeaderCartCount() {
    const cartCountBadge = document.getElementById('cartCount');
    if (cartCountBadge) {
        const cart = getCart();
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        cartCountBadge.textContent = totalItems;
    }
}

/**
 * Dynamically Adjust Header User Navigation based on login state
 */
function setupHeaderUserUI() {
    const userMenuSection = document.getElementById('userMenuSection');
    if (!userMenuSection) return;

    const user = getCurrentUser();
    if (user) {
        userMenuSection.innerHTML = `
            <span style="font-weight:600; font-size:0.9rem; color:var(--text-main);">Hi, ${user.name.split(' ')[0]}</span>
            <a href="profile.html" class="btn-link">Profile</a>
            <button id="headerLogoutBtn" class="btn-danger-outline" style="padding:4px 10px; font-size:0.8rem;">Logout</button>
        `;

        const headerLogoutBtn = document.getElementById('headerLogoutBtn');
        if (headerLogoutBtn) {
            headerLogoutBtn.addEventListener('click', logoutUser);
        }
    }
}

/**
 * Format Price to USD Currency String
 */
function formatCurrency(amount) {
    return '$' + parseFloat(amount).toFixed(2);
}

/**
 * Calculate Discounted Price
 */
function getDiscountedPrice(price, discountPercent) {
    if (!discountPercent || discountPercent <= 0) return price;
    return price - (price * (discountPercent / 100));
}

/**
 * Get URL Query Parameter Value
 */
function getUrlParam(paramName) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(paramName);
}

/**
 * Display User Alert Messages
 */
function showAlert(containerId, message, type = 'error') {
    const alertBox = document.getElementById(containerId);
    if (!alertBox) return;

    alertBox.className = `alert-message ${type}`;
    alertBox.textContent = message;
    alertBox.classList.remove('hidden');

    // Auto scroll to alert
    alertBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
