/**
 * ShopNow - Online Shopping System
 * Shopping Cart Management JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    initCartPage();
});

/**
 * Add Product to Cart with Quantity Validation
 */
function addToCart(productId, quantity = 1) {
    const products = getProducts();
    const product = products.find(p => p.id === productId);

    if (!product) {
        alert('Product not found.');
        return;
    }

    if (product.stock < 1) {
        alert('Sorry, this product is currently out of stock.');
        return;
    }

    let cart = getCart();
    const existingIndex = cart.findIndex(item => item.product_id === productId);

    if (existingIndex > -1) {
        const newQty = cart[existingIndex].quantity + quantity;
        if (newQty > product.stock) {
            alert(`Cannot add more. Maximum available stock is ${product.stock}.`);
            return;
        }
        cart[existingIndex].quantity = newQty;
    } else {
        const finalPrice = getDiscountedPrice(product.price, product.discount);
        cart.push({
            cart_id: 'CART-' + Date.now(),
            product_id: product.id,
            product_name: product.name,
            product_image: product.image,
            category_name: product.category_name,
            price: finalPrice,
            quantity: quantity,
            stock: product.stock
        });
    }

    saveCart(cart);
    showCartToast(`Added "${product.name}" to your cart!`);
}

/**
 * Remove Item from Cart
 */
function removeFromCart(productId) {
    let cart = getCart();
    cart = cart.filter(item => item.product_id !== productId);
    saveCart(cart);
    initCartPage();
}

/**
 * Update Cart Item Quantity
 */
function updateCartQuantity(productId, quantity) {
    if (quantity <= 0) {
        removeFromCart(productId);
        return;
    }

    let cart = getCart();
    const item = cart.find(i => i.product_id === productId);
    if (item) {
        if (quantity > item.stock) {
            alert(`Stock limit reached. Maximum stock available is ${item.stock}.`);
            return;
        }
        item.quantity = quantity;
        saveCart(cart);
        initCartPage();
    }
}

/**
 * Clear Entire Shopping Cart
 */
function clearCart() {
    saveCart([]);
    initCartPage();
}

/**
 * Render Cart Page UI
 */
function initCartPage() {
    const cartTableBody = document.getElementById('cartTableBody');
    if (!cartTableBody) return;

    const cart = getCart();
    const cartLayout = document.getElementById('cartLayout');
    const emptyCartView = document.getElementById('emptyCartView');

    if (cart.length === 0) {
        if (cartLayout) cartLayout.classList.add('hidden');
        if (emptyCartView) emptyCartView.classList.remove('hidden');
        return;
    }

    if (cartLayout) cartLayout.classList.remove('hidden');
    if (emptyCartView) emptyCartView.classList.add('hidden');

    cartTableBody.innerHTML = '';
    let subtotal = 0;
    let totalItems = 0;

    cart.forEach(item => {
        const itemSubtotal = item.price * item.quantity;
        subtotal += itemSubtotal;
        totalItems += item.quantity;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="product-cell">
                <img src="${item.product_image}" alt="${item.product_name}" onerror="this.onerror=null; this.src='https://via.placeholder.com/80?text=Product';">
                <div class="product-cell-info">
                    <a href="product-details.html?id=${item.product_id}" class="product-name">${item.product_name}</a>
                    <span class="product-category-sm">${item.category_name || ''}</span>
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
            <td class="subtotal-cell">${formatCurrency(itemSubtotal)}</td>
            <td class="action-cell">
                <button class="btn-delete-item" data-id="${item.product_id}">🗑️ Remove</button>
            </td>
        `;

        cartTableBody.appendChild(row);
    });

    // Attach Event Listeners to Cart Controls
    cartTableBody.querySelectorAll('.dec-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pId = parseInt(e.target.getAttribute('data-id'));
            const item = cart.find(i => i.product_id === pId);
            if (item) updateCartQuantity(pId, item.quantity - 1);
        });
    });

    cartTableBody.querySelectorAll('.inc-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pId = parseInt(e.target.getAttribute('data-id'));
            const item = cart.find(i => i.product_id === pId);
            if (item) updateCartQuantity(pId, item.quantity + 1);
        });
    });

    cartTableBody.querySelectorAll('.qty-input-inline').forEach(input => {
        input.addEventListener('change', (e) => {
            const pId = parseInt(e.target.getAttribute('data-id'));
            const val = parseInt(e.target.value) || 1;
            updateCartQuantity(pId, val);
        });
    });

    cartTableBody.querySelectorAll('.btn-delete-item').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pId = parseInt(e.target.getAttribute('data-id'));
            removeFromCart(pId);
        });
    });

    // Update Summary Box Values
    const shippingFee = subtotal > 0 ? 15.00 : 0.00;
    const finalTotal = subtotal + shippingFee;

    const itemsElem = document.getElementById('summaryTotalItems');
    const subtotalElem = document.getElementById('summarySubtotal');
    const shippingElem = document.getElementById('summaryShipping');
    const totalElem = document.getElementById('summaryTotalAmount');

    if (itemsElem) itemsElem.textContent = `${totalItems} item(s)`;
    if (subtotalElem) subtotalElem.textContent = formatCurrency(subtotal);
    if (shippingElem) shippingElem.textContent = formatCurrency(shippingFee);
    if (totalElem) totalElem.textContent = formatCurrency(finalTotal);

    // Clear Cart Button Listener
    const clearCartBtn = document.getElementById('clearCartBtn');
    if (clearCartBtn) {
        clearCartBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to clear your cart?')) {
                clearCart();
            }
        });
    }
}

/**
 * Toast Notification Banner
 */
function showCartToast(message) {
    let toast = document.getElementById('cartToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'cartToast';
        toast.style.cssText = `
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #10b981;
            color: #fff;
            padding: 14px 24px;
            border-radius: 8px;
            font-weight: 600;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.2);
            z-index: 9999;
            transition: all 0.3s ease;
        `;
        document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.style.opacity = '1';

    setTimeout(() => {
        toast.style.opacity = '0';
    }, 2500);
}
