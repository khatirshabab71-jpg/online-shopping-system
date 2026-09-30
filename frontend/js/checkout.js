/**
 * ShopNow - Online Shopping System
 * Checkout Validation, Payment Simulation & Receipt Confirmation Script
 */

document.addEventListener('DOMContentLoaded', () => {
    initCheckoutPage();
    initOrderConfirmationPage();
});

/**
 * Handle Checkout Page Setup, Validation & Placement
 */
function initCheckoutPage() {
    const checkoutForm = document.getElementById('checkoutForm');
    if (!checkoutForm) return;

    const cart = getCart();
    if (cart.length === 0) {
        alert('Your shopping cart is empty. Please add items before checking out.');
        window.location.href = 'products.html';
        return;
    }

    // Pre-fill user information if logged in
    const user = getCurrentUser();
    if (user) {
        document.getElementById('checkoutName').value = user.name || '';
        document.getElementById('checkoutEmail').value = user.email || '';
        document.getElementById('checkoutPhone').value = user.phone || '';
        document.getElementById('checkoutAddress').value = user.address || '';
    }

    // Render Order Summary Items
    const itemsList = document.getElementById('checkoutOrderItems');
    let subtotal = 0;

    if (itemsList) {
        itemsList.innerHTML = '';
        cart.forEach(item => {
            const itemTotal = item.price * item.quantity;
            subtotal += itemTotal;

            const div = document.createElement('div');
            div.className = 'summary-item';
            div.innerHTML = `
                <span>${item.product_name} (x${item.quantity})</span>
                <strong>${formatCurrency(itemTotal)}</strong>
            `;
            itemsList.appendChild(div);
        });
    }

    const shippingFee = 15.00;
    const finalTotal = subtotal + shippingFee;

    document.getElementById('checkoutSubtotal').textContent = formatCurrency(subtotal);
    document.getElementById('checkoutShipping').textContent = formatCurrency(shippingFee);
    document.getElementById('checkoutFinalTotal').textContent = formatCurrency(finalTotal);

    // Toggle Payment Options (Cash on Delivery vs Simulated Card)
    const payCOD = document.getElementById('payCOD');
    const payCard = document.getElementById('payCard');
    const simulatedCardDetails = document.getElementById('simulatedCardDetails');

    if (payCOD && payCard && simulatedCardDetails) {
        payCOD.addEventListener('change', () => {
            if (payCOD.checked) simulatedCardDetails.classList.add('hidden');
        });

        payCard.addEventListener('change', () => {
            if (payCard.checked) simulatedCardDetails.classList.remove('hidden');
        });
    }

    // Checkout Submission Event
    checkoutForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const name = document.getElementById('checkoutName').value.trim();
        const email = document.getElementById('checkoutEmail').value.trim();
        const phone = document.getElementById('checkoutPhone').value.trim();
        const address = document.getElementById('checkoutAddress').value.trim();
        const city = document.getElementById('checkoutCity').value.trim();
        const postalCode = document.getElementById('checkoutPostalCode').value.trim();
        const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked').value;

        // Validation
        if (!name || !email || !phone || !address || !city || !postalCode) {
            showAlert('checkoutAlert', 'Please fill in all required shipping and contact details.', 'error');
            return;
        }

        if (paymentMethod === 'card') {
            const cardNum = document.getElementById('cardNumber').value.trim();
            const cardExp = document.getElementById('cardExpiry').value.trim();
            const cardCvv = document.getElementById('cardCvv').value.trim();

            if (!cardNum || !cardExp || !cardCvv) {
                showAlert('checkoutAlert', 'Please enter simulated card details.', 'error');
                return;
            }
        }

        // Generate Order Record
        const orderId = 'ORD-' + Math.floor(10000 + Math.random() * 90000);
        const orderDate = new Date().toISOString().substring(0, 10);

        const newOrder = {
            order_id: orderId,
            user_id: user ? user.user_id : 'GUEST',
            customer_name: name,
            customer_email: email,
            customer_phone: phone,
            shipping_address: `${address}, ${city}, ${postalCode}`,
            total_amount: finalTotal,
            payment_method: paymentMethod === 'cod' ? 'Cash on Delivery' : 'Simulated Card Payment',
            order_status: 'Pending',
            order_date: orderDate,
            items: cart.map(item => ({
                product_id: item.product_id,
                product_name: item.product_name,
                quantity: item.quantity,
                price: item.price
            }))
        };

        // Save order to history
        const ordersHistory = JSON.parse(localStorage.getItem(STORAGE_KEYS.ORDERS)) || [];
        ordersHistory.unshift(newOrder);
        localStorage.setItem(STORAGE_KEYS.ORDERS, JSON.stringify(ordersHistory));

        // Deduct inventory stock in storage
        const products = getProducts();
        cart.forEach(cartItem => {
            const prod = products.find(p => p.id === cartItem.product_id);
            if (prod) prod.stock = Math.max(0, prod.stock - cartItem.quantity);
        });
        saveProducts(products);

        // Clear Cart
        saveCart([]);

        // Redirect to Order Confirmation page
        window.location.href = `order-confirmation.html?id=${orderId}`;
    });
}

/**
 * Handle Order Confirmation Page Receipt Rendering
 */
function initOrderConfirmationPage() {
    const confirmOrderId = document.getElementById('confirmOrderId');
    if (!confirmOrderId) return;

    const orderId = getUrlParam('id');
    const ordersHistory = JSON.parse(localStorage.getItem(STORAGE_KEYS.ORDERS)) || [];
    const order = ordersHistory.find(o => o.order_id === orderId) || ordersHistory[0];

    if (!order) {
        alert('Order record not found.');
        window.location.href = 'index.html';
        return;
    }

    // Populate receipt details
    confirmOrderId.textContent = `#${order.order_id}`;
    document.getElementById('confirmOrderDate').textContent = order.order_date;
    document.getElementById('confirmOrderStatus').textContent = order.order_status;
    document.getElementById('confirmCustomerName').textContent = order.customer_name;
    document.getElementById('confirmShippingAddress').textContent = order.shipping_address;
    document.getElementById('confirmPaymentMethod').textContent = order.payment_method;
    document.getElementById('confirmTotalAmount').textContent = formatCurrency(order.total_amount);

    // Populate Receipt Table Items
    const itemsListBody = document.getElementById('confirmItemsList');
    if (itemsListBody) {
        itemsListBody.innerHTML = '';
        order.items.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.product_name}</td>
                <td>${item.quantity}</td>
                <td>${formatCurrency(item.price)}</td>
                <td>${formatCurrency(item.price * item.quantity)}</td>
            `;
            itemsListBody.appendChild(tr);
        });
    }
}
