/**
 * ShopNow - Online Shopping System
 * Wishlist & Saved Products JavaScript
 * Directly connected to Python backend API and MySQL database.
 */

document.addEventListener('DOMContentLoaded', () => {
    initWishlistPage();
});

async function initWishlistPage() {
    const container = document.getElementById('wishlistContainer');
    const emptyView = document.getElementById('emptyWishlistView');
    if (!container) return;

    if (!getAuthToken()) {
        container.innerHTML = '';
        if (emptyView) {
            emptyView.classList.remove('hidden');
            emptyView.innerHTML = `
                <div class="empty-icon">🔒</div>
                <h2>Sign in to view your wishlist</h2>
                <p>Your wishlist is saved to your account so you can access it on any device.</p>
                <a href="login.html" class="btn-primary" style="margin-top: 15px;">Sign In to Your Account</a>
            `;
        }
        return;
    }

    const res = await apiFetch('/wishlist');

    if (!res || !res.success || !res.wishlist || res.wishlist.items.length === 0) {
        container.innerHTML = '';
        if (emptyView) emptyView.classList.remove('hidden');
        updateHeaderWishlistCount();
        return;
    }

    if (emptyView) emptyView.classList.add('hidden');
    container.innerHTML = '';

    const grid = document.createElement('div');
    grid.className = 'product-grid';

    res.wishlist.items.forEach(p => {
        const inStock = p.stock > 0;
        const card = document.createElement('div');
        card.className = 'product-card wishlist-card';

        card.innerHTML = `
            ${p.discount > 0 ? `<div class="product-badge">${p.discount}% OFF</div>` : ''}
            <div class="product-image-box">
                <a href="product-details.html?id=${p.product_id}">
                    <img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.product_name)}" onerror="this.onerror=null; this.src='https://via.placeholder.com/250x200?text=Product';">
                </a>
            </div>
            <div class="product-info">
                <span class="product-category">${escapeHTML(p.category_name)}</span>
                <h3 class="product-title"><a href="product-details.html?id=${p.product_id}">${escapeHTML(p.product_name)}</a></h3>
                <div class="product-rating">
                    <span class="stars">★★★★★</span>
                    <span class="rating-val">(${p.rating})</span>
                </div>
                <div class="product-price-box">
                    <span class="current-price">${formatCurrency(p.price)}</span>
                    ${p.discount > 0 ? `<span class="original-price">${formatCurrency(p.original_price)}</span>` : ''}
                </div>
                <div style="font-size:0.8rem; margin-bottom: 10px; color:${inStock ? '#10b981' : '#ef4444'}; font-weight:600;">
                    ${inStock ? `✓ ${p.stock} in stock` : '✕ Out of stock'}
                </div>
                <div class="product-actions" style="display:flex; gap:8px;">
                    <button class="btn-primary move-cart-btn" data-id="${p.product_id}" style="flex:1;" ${!inStock ? 'disabled style="opacity:0.6;"' : ''}>
                        🛒 Move to Cart
                    </button>
                    <button class="btn-danger-outline remove-wishlist-btn" data-id="${p.product_id}" title="Remove from wishlist" style="padding: 6px 12px;">
                        🗑️
                    </button>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });

    container.appendChild(grid);

    // Event Listeners
    grid.querySelectorAll('.move-cart-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const pId = parseInt(e.target.getAttribute('data-id'));
            btn.disabled = true;
            btn.textContent = 'Moving...';

            const moveRes = await apiFetch('/wishlist/move-to-cart', 'POST', { product_id: pId });
            if (moveRes && moveRes.success) {
                showToast(moveRes.message || 'Moved to cart!', 'success');
                updateHeaderCartCount();
                updateHeaderWishlistCount();
                initWishlistPage();
            } else {
                alert(moveRes ? moveRes.message : 'Could not move to cart.');
                btn.disabled = false;
                btn.textContent = '🛒 Move to Cart';
            }
        });
    });

    grid.querySelectorAll('.remove-wishlist-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const pId = parseInt(e.target.getAttribute('data-id'));
            const delRes = await apiFetch('/wishlist/remove', 'POST', { product_id: pId });
            if (delRes && delRes.success) {
                showToast('Item removed from wishlist', 'info');
                updateHeaderWishlistCount();
                initWishlistPage();
            } else {
                alert(delRes ? delRes.message : 'Failed to remove item.');
            }
        });
    });
}
