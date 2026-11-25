/**
 * ShopNow - Online Shopping System
 * Main Global Utility JavaScript (Pure Vanilla JS)
 * Serves as the central API client, session manager, and global UI handler.
 */

// Storage Keys
const STORAGE_KEYS = {
    USER_TOKEN: 'shopnow_token',
    USER_PROFILE: 'shopnow_user',
    ADMIN_TOKEN: 'shopnow_admin_token',
    ADMIN_PROFILE: 'shopnow_admin'
};

// Relative API Base URL (served from the same Python server origin)
const API_BASE_URL = '/api';

/**
 * Universal Async API Fetch Helper for Python Backend Communication.
 * Automatically attaches session authorization headers and handles error responses.
 */
async function apiFetch(endpoint, method = 'GET', data = null, isAdmin = false) {
    try {
        const headers = {
            'Content-Type': 'application/json'
        };

        // Attach appropriate bearer token
        const token = isAdmin ? getAdminToken() : (getAuthToken() || getAdminToken());
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
            headers['X-Session-Token'] = token;
        }

        const options = {
            method: method,
            headers: headers
        };

        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        let result = null;

        try {
            result = await response.json();
        } catch (e) {
            result = null;
        }

        if (!response.ok) {
            if (response.status === 401 && !window.location.pathname.includes('login.html')) {
                // Session expired or revoked
                if (isAdmin) {
                    removeAdminSession();
                } else {
                    removeUserSession();
                }
            }
            return result || { success: false, message: `Server error (${response.status})` };
        }

        return result || { success: true };
    } catch (err) {
        console.error('API Fetch Network Error:', err);
        return { 
            success: false, 
            message: 'Server is currently offline or unreachable. Please verify Python server is running.' 
        };
    }
}

// ----------------------------------------------------------------------
// USER SESSION MANAGEMENT
// ----------------------------------------------------------------------

function getAuthToken() {
    return localStorage.getItem(STORAGE_KEYS.USER_TOKEN);
}

function setAuthToken(token) {
    localStorage.setItem(STORAGE_KEYS.USER_TOKEN, token);
}

function getCurrentUser() {
    const raw = localStorage.getItem(STORAGE_KEYS.USER_PROFILE);
    try {
        return raw ? JSON.parse(raw) : null;
    } catch (e) {
        return null;
    }
}

function setCurrentUser(user) {
    localStorage.setItem(STORAGE_KEYS.USER_PROFILE, JSON.stringify(user));
}

function removeUserSession() {
    localStorage.removeItem(STORAGE_KEYS.USER_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER_PROFILE);
}

async function logoutUser() {
    try {
        await apiFetch('/logout', 'POST');
    } catch (e) {}
    removeUserSession();
    window.location.href = 'login.html';
}

// ----------------------------------------------------------------------
// ADMIN SESSION MANAGEMENT
// ----------------------------------------------------------------------

function getAdminToken() {
    return localStorage.getItem(STORAGE_KEYS.ADMIN_TOKEN);
}

function setAdminToken(token) {
    localStorage.setItem(STORAGE_KEYS.ADMIN_TOKEN, token);
}

function getAdminSession() {
    const raw = localStorage.getItem(STORAGE_KEYS.ADMIN_PROFILE);
    try {
        return raw ? JSON.parse(raw) : null;
    } catch (e) {
        return null;
    }
}

function setAdminSession(adminData) {
    localStorage.setItem(STORAGE_KEYS.ADMIN_PROFILE, JSON.stringify(adminData));
}

function removeAdminSession() {
    localStorage.removeItem(STORAGE_KEYS.ADMIN_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.ADMIN_PROFILE);
}

async function logoutAdmin() {
    try {
        await apiFetch('/logout', 'POST', null, true);
    } catch (e) {}
    removeAdminSession();
    window.location.href = 'login.html';
}

// ----------------------------------------------------------------------
// UI HELPERS, CART & WISHLIST BADGES
// ----------------------------------------------------------------------

async function updateHeaderCartCount() {
    const cartCountBadge = document.getElementById('cartCount');
    if (!cartCountBadge) return;

    const token = getAuthToken();
    if (!token) {
        cartCountBadge.textContent = '0';
        return;
    }

    const res = await apiFetch('/cart');
    if (res && res.success && res.cart) {
        cartCountBadge.textContent = res.cart.item_count || 0;
    } else {
        cartCountBadge.textContent = '0';
    }
}

async function updateHeaderWishlistCount() {
    const badge = document.getElementById('wishlistCount');
    const menuBadge = document.getElementById('menuWishlistCount');
    const token = getAuthToken();
    if (!token) {
        if (badge) badge.textContent = '0';
        if (menuBadge) menuBadge.textContent = '0';
        return;
    }

    const res = await apiFetch('/wishlist');
    const count = (res && res.success && res.wishlist) ? (res.wishlist.total_count || 0) : 0;
    if (badge) badge.textContent = count;
    if (menuBadge) menuBadge.textContent = count;
}

function setupHeaderUserUI() {
    const userMenuSection = document.getElementById('userMenuSection');
    if (!userMenuSection) return;

    const user = getCurrentUser();
    if (user && getAuthToken()) {
        const firstName = user.name ? user.name.split(' ')[0] : 'Customer';
        userMenuSection.innerHTML = `
            <span style="font-weight:600; font-size:0.9rem; color:var(--text-main);">Hi, ${escapeHTML(firstName)}</span>
            <a href="wishlist.html" class="btn-link" title="Saved Items">Wishlist (<span id="menuWishlistCount">0</span>)</a>
            <a href="orders.html" class="btn-link">My Orders</a>
            <a href="profile.html" class="btn-link">Profile</a>
            <button id="headerLogoutBtn" class="btn-danger-outline" style="padding:4px 10px; font-size:0.8rem; cursor:pointer;">Logout</button>
        `;

        const headerLogoutBtn = document.getElementById('headerLogoutBtn');
        if (headerLogoutBtn) {
            headerLogoutBtn.addEventListener('click', logoutUser);
        }
    }
}

function formatCurrency(amount) {
    return '$' + parseFloat(amount || 0).toFixed(2);
}

function getDiscountedPrice(price, discountPercent) {
    if (!discountPercent || discountPercent <= 0) return parseFloat(price);
    return parseFloat(price) * (1 - (discountPercent / 100));
}

function getUrlParam(paramName) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(paramName);
}

function showAlert(containerId, message, type = 'error') {
    const alertBox = document.getElementById(containerId);
    if (!alertBox) return;

    alertBox.className = `alert-message ${type}`;
    alertBox.textContent = message;
    alertBox.classList.remove('hidden');
    alertBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function showToast(message, type = 'info') {
    let toast = document.getElementById('globalToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'globalToast';
        toast.className = 'cart-toast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.className = `cart-toast show toast-${type}`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2800);
}

function escapeHTML(str) {
    if (!str) return '';
    return String(str).replace(/[&<>'"]/g, tag => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
    }[tag] || tag));
}

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
    updateHeaderCartCount();
    updateHeaderWishlistCount();
    setupHeaderUserUI();
});
