/**
 * ShopNow - Online Shopping System
 * Checkout Validation, Payment Simulation & Receipt Confirmation Script
 * Connects directly to Python backend API & MySQL database.
 */

document.addEventListener('DOMContentLoaded', () => {
    initCheckoutPage();
    initOrderConfirmationPage();
});

/**
 * Handle Checkout Page Setup, Validation & Order Placement
 */
async function initCheckoutPage() {
    const checkoutForm = document.getElementById('checkoutForm');
    if (!checkoutForm) return;

    if (!getAuthToken()) {
        alert('Please log in to your account before proceeding to checkout.');
        window.location.href = 'login.html';
        return;
    }

    // 1. Fetch current cart from MySQL
    const cartRes = await apiFetch('/cart');
    if (!cartRes || !cartRes.success || !cartRes.cart || cartRes.cart.items.length === 0) {
        alert('Your shopping cart is empty. Please add items before checking out.');
        window.location.href = 'products.html';
        return;
    }

    const cart = cartRes.cart;

    // 2. Pre-fill customer details from database profile
    const profileRes = await apiFetch('/me');
    if (profileRes && profileRes.success && profileRes.user) {
        const u = profileRes.user;
        const nameField = document.getElementById('checkoutName');
        const emailField = document.getElementById('checkoutEmail');
        const phoneField = document.getElementById('checkoutPhone');
        const addressField = document.getElementById('checkoutAddress');

        if (nameField) nameField.value = u.name || '';
        if (emailField) emailField.value = u.email || '';
        if (phoneField) phoneField.value = u.phone || '';
        if (addressField) addressField.value = u.address || '';
    }

    // 3. Render Order Summary Items
    const itemsList = document.getElementById('checkoutOrderItems');
    if (itemsList) {
        itemsList.innerHTML = '';
        cart.items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'summary-item';
            div.innerHTML = `
                <span>${escapeHTML(item.name)} (x${item.quantity})</span>
                <strong>${formatCurrency(item.line_total)}</strong>
            `;
            itemsList.appendChild(div);
        });
    }

    const shippingFee = 15.00;
    const finalTotal = cart.subtotal + shippingFee;

    const subtotalEl = document.getElementById('checkoutSubtotal');
    const shippingEl = document.getElementById('checkoutShipping');
    const finalTotalEl = document.getElementById('checkoutFinalTotal');

    if (subtotalEl) subtotalEl.textContent = formatCurrency(cart.subtotal);
    if (shippingEl) shippingEl.textContent = formatCurrency(shippingFee);
    if (finalTotalEl) finalTotalEl.textContent = formatCurrency(finalTotal);

    // Keep Cash on Delivery selected for MVP
    const payCOD = document.getElementById('payCOD');
    if (payCOD) payCOD.checked = true;

    // 4. Handle Form Submit
    checkoutForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const name = document.getElementById('checkoutName').value.trim();
        const email = document.getElementById('checkoutEmail').value.trim();
        const phone = document.getElementById('checkoutPhone').value.trim();
        const address = document.getElementById('checkoutAddress').value.trim();
        const city = document.getElementById('checkoutCity').value.trim();
        const postalCode = document.getElementById('checkoutPostalCode').value.trim();

        if (!name || !email || !phone || !address || !city || !postalCode) {
            showAlert('checkoutAlert', 'Please fill in all required shipping and contact details.', 'error');
            return;
        }

        const placeOrderBtn = document.getElementById('placeOrderBtn') || checkoutForm.querySelector('button[type="submit"]');
        if (placeOrderBtn) {
            placeOrderBtn.disabled = true;
            placeOrderBtn.textContent = 'Processing Cash on Delivery Order...';
        }

        const res = await apiFetch('/checkout', 'POST', {
            name,
            phone,
            address,
            city,
            postalCode,
            paymentMethod: 'Cash on Delivery'
        });

        if (res && res.success && res.order_id) {
            updateHeaderCartCount();
            window.location.href = `order-confirmation.html?id=${res.order_id}`;
        } else {
            if (placeOrderBtn) {
                placeOrderBtn.disabled = false;
                placeOrderBtn.textContent = 'Place Order (Cash on Delivery)';
            }
            showAlert('checkoutAlert', res ? res.message : 'Checkout failed. Your cart was not changed.', 'error');
        }
    });
}

/**
 * Handle Order Confirmation Page Receipt Rendering directly from Python & MySQL
 */
async function initOrderConfirmationPage() {
    const confirmOrderId = document.getElementById('confirmOrderId');
    if (!confirmOrderId) return; // Not on order-confirmation page

    const orderId = getUrlParam('id');
    if (!orderId) {
        window.location.href = 'index.html';
        return;
    }

    const res = await apiFetch(`/order?id=${orderId}`);

    if (!res || !res.success || !res.order) {
        confirmOrderId.textContent = 'Not Found';
        const orderContainer = document.querySelector('.confirmation-card') || document.querySelector('main');
        if (orderContainer) {
            orderContainer.innerHTML = `
                <div class="empty-state" style="padding: 40px; text-align: center;">
                    <h2>Order Not Found</h2>
                    <p>${res ? res.message : 'Could not find the requested order record in the database.'}</p>
                    <a href="orders.html" class="btn-primary" style="margin-top: 15px;">View My Orders</a>
                </div>
            `;
        }
        return;
    }

    const order = res.order;

    // Populate receipt header
    confirmOrderId.textContent = `#ORD-${order.order_id}`;
    
    const dateEl = document.getElementById('confirmOrderDate');
    const statusEl = document.getElementById('confirmOrderStatus');
    const nameEl = document.getElementById('confirmCustomerName');
    const addressEl = document.getElementById('confirmShippingAddress');
    const paymentEl = document.getElementById('confirmPaymentMethod');
    const totalEl = document.getElementById('confirmTotalAmount');

    if (dateEl) dateEl.textContent = (order.order_date || '').substring(0, 19);
    if (statusEl) {
        statusEl.textContent = order.order_status;
        statusEl.className = `badge-status status-${(order.order_status || 'pending').toLowerCase()}`;
    }
    if (nameEl) nameEl.textContent = order.customer_name || 'Customer';
    if (addressEl) addressEl.textContent = order.shipping_address;
    if (paymentEl) paymentEl.textContent = order.payment_method;
    if (totalEl) totalEl.textContent = formatCurrency(order.total_amount);

    // Populate Receipt Table Line Items
    const itemsListBody = document.getElementById('confirmItemsList');
    if (itemsListBody && order.items) {
        itemsListBody.innerHTML = '';
        order.items.forEach(item => {
            const tr = document.createElement('tr');
            const itemPrice = parseFloat(item.price);
            const itemQty = parseInt(item.quantity);
            const lineSubtotal = itemPrice * itemQty;

            tr.innerHTML = `
                <td><strong>${escapeHTML(item.product_name)}</strong></td>
                <td>${itemQty}</td>
                <td>${formatCurrency(itemPrice)}</td>
                <td>${formatCurrency(lineSubtotal)}</td>
            `;
            itemsListBody.appendChild(tr);
        });
    }
}
