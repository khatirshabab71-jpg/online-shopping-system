/**
 * ShopNow - Online Shopping System
 * Shopping Cart Management JavaScript
 * Connected to MySQL database via Python Backend API.
 */

document.addEventListener('DOMContentLoaded', () => {
    initCartPage();
});

/**
 * Add Product to Cart via Python API with Server-side Stock Validation
 */
async function addToCart(productId, quantity = 1) {
    if (!getAuthToken()) {
        alert('Please sign in to your customer account to add items to your cart.');
        window.location.href = 'login.html';
        return;
    }

    const res = await apiFetch('/cart/add', 'POST', {
        product_id: parseInt(productId),
        quantity: parseInt(quantity)
    });

    if (res && res.success) {
        showCartToast(res.message || 'Item added to your cart!');
        updateHeaderCartCount();
    } else {
        alert(res ? res.message : 'Could not add product to cart.');
    }
}

/**
 * Update Item Quantity in Cart via Python API
 */
async function updateCartQuantity(productId, quantity) {
    if (quantity <= 0) {
        await removeFromCart(productId);
        return;
    }

    const res = await apiFetch('/cart/update', 'POST', {
        product_id: parseInt(productId),
        quantity: parseInt(quantity)
    });

    if (res && res.success) {
        await initCartPage();
        updateHeaderCartCount();
    } else {
        alert(res ? res.message : 'Could not update quantity.');
        await initCartPage();
    }
}

/**
 * Remove Single Item from Cart via Python API
 */
async function removeFromCart(productId) {
    const res = await apiFetch('/cart/delete', 'POST', {
        product_id: parseInt(productId)
    });

    if (res && res.success) {
        await initCartPage();
        updateHeaderCartCount();
    } else {
        alert(res ? res.message : 'Could not remove item.');
    }
}

/**
 * Clear Entire Shopping Cart via Python API
 */
async function clearCart() {
    if (!confirm('Are you sure you want to clear your entire shopping cart?')) return;

    const res = await apiFetch('/cart/clear', 'POST');
    if (res && res.success) {
        await initCartPage();
        updateHeaderCartCount();
    } else {
        alert(res ? res.message : 'Could not clear cart.');
    }
}

/**
 * Render Cart Page UI directly from MySQL data
 */
async function initCartPage() {
    const cartTableBody = document.getElementById('cartTableBody');
    if (!cartTableBody) return;

    const cartLayout = document.getElementById('cartLayout');
    const emptyCartView = document.getElementById('emptyCartView');

    if (!getAuthToken()) {
        if (cartLayout) cartLayout.classList.add('hidden');
        if (emptyCartView) {
            emptyCartView.classList.remove('hidden');
            emptyCartView.innerHTML = `
                <div class="empty-icon">🛒</div>
                <h2>Your Shopping Cart is Empty</h2>
                <p>Please log in to view and manage your shopping cart.</p>
                <a href="login.html" class="btn-primary">Sign In to Your Account</a>
            `;
        }
        return;
    }

    const res = await apiFetch('/cart');

    if (!res || !res.success || !res.cart || res.cart.items.length === 0) {
        if (cartLayout) cartLayout.classList.add('hidden');
        if (emptyCartView) {
            emptyCartView.classList.remove('hidden');
            emptyCartView.innerHTML = `
                <div class="empty-icon">🛒</div>
                <h2>Your Shopping Cart is Empty</h2>
                <p>You haven't added any products to your cart yet.</p>
                <a href="products.html" class="btn-primary">Explore Products</a>
            `;
        }
        updateHeaderCartCount();
        return;
    }

    if (cartLayout) cartLayout.classList.remove('hidden');
    if (emptyCartView) emptyCartView.classList.add('hidden');

    const cartData = res.cart;
    cartTableBody.innerHTML = '';

    cartData.items.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="product-cell">
                <img src="${escapeHTML(item.image)}" alt="${escapeHTML(item.name)}" onerror="this.onerror=null; this.src='https://via.placeholder.com/80?text=Product';">
                <div class="product-cell-info">
                    <a href="product-details.html?id=${item.product_id}" class="product-name">${escapeHTML(item.name)}</a>
                    <span class="product-category-sm">In Stock: ${item.stock}</span>
                </div>
            </td>
            <td class="price-cell">${formatCurrency(item.price)}</td>
            <td class="qty-cell">
                <div class="qty-control-inline">
                    <button type="button" class="btn-qty-sm dec-btn" data-id="${item.product_id}">-</button>
                    <input type="number" value="${item.quantity}" min="1" max="${item.stock}" class="qty-input-inline" data-id="${item.product_id}">
                    <button type="button" class="btn-qty-sm inc-btn" data-id="${item.product_id}">+</button>
                </div>
            </td>
            <td class="subtotal-cell">${formatCurrency(item.line_total)}</td>
            <td class="action-cell">
                <button class="btn-delete-item remove-btn" data-id="${item.product_id}">🗑️ Remove</button>
            </td>
        `;
        cartTableBody.appendChild(row);
    });

    // Populate Summary Card
    const shippingFee = 15.00;
    const finalTotal = cartData.subtotal + shippingFee;

    const summaryTotalItems = document.getElementById('summaryTotalItems');
    const summarySubtotal = document.getElementById('summarySubtotal');
    const summaryShipping = document.getElementById('summaryShipping');
    const summaryTotalAmount = document.getElementById('summaryTotalAmount');

    if (summaryTotalItems) summaryTotalItems.textContent = `${cartData.item_count} item(s)`;
    if (summarySubtotal) summarySubtotal.textContent = formatCurrency(cartData.subtotal);
    if (summaryShipping) summaryShipping.textContent = formatCurrency(shippingFee);
    if (summaryTotalAmount) summaryTotalAmount.textContent = formatCurrency(finalTotal);

    // Event Listeners for Cart Controls
    cartTableBody.querySelectorAll('.dec-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pId = parseInt(e.target.getAttribute('data-id'));
            const input = cartTableBody.querySelector(`.qty-input-inline[data-id="${pId}"]`);
            const currentVal = parseInt(input.value) || 1;
            updateCartQuantity(pId, currentVal - 1);
        });
    });

    cartTableBody.querySelectorAll('.inc-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pId = parseInt(e.target.getAttribute('data-id'));
            const input = cartTableBody.querySelector(`.qty-input-inline[data-id="${pId}"]`);
            const currentVal = parseInt(input.value) || 1;
            updateCartQuantity(pId, currentVal + 1);
        });
    });

    cartTableBody.querySelectorAll('.qty-input-inline').forEach(input => {
        input.addEventListener('change', (e) => {
            const pId = parseInt(e.target.getAttribute('data-id'));
            const newQty = parseInt(e.target.value) || 1;
            updateCartQuantity(pId, newQty);
        });
    });

    cartTableBody.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pId = parseInt(e.target.getAttribute('data-id'));
            removeFromCart(pId);
        });
    });

    const clearCartBtn = document.getElementById('clearCartBtn');
    if (clearCartBtn) {
        clearCartBtn.onclick = clearCart;
    }
}

/**
 * Toast Notification for Add to Cart
 */
function showCartToast(message) {
    let toast = document.getElementById('cartToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'cartToast';
        toast.className = 'cart-toast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2500);
}
