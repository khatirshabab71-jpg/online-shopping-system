/**
 * ShopNow - Online Shopping System
 * Admin Panel Interactive Operations JavaScript
 * Connects directly to the Python backend API and MySQL database.
 */

document.addEventListener('DOMContentLoaded', () => {
    initAdminLogin();
    initAdminDashboard();
    initAdminProductsPage();
    initAdminUsersPage();
    initAdminOrdersPage();
    initAdminReviewsPage();
});

/**
 * Handle Admin Authentication Login
 */
function initAdminLogin() {
    const adminLoginForm = document.getElementById('adminLoginForm');
    if (!adminLoginForm) return;

    adminLoginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = document.getElementById('adminUsername').value.trim();
        const password = document.getElementById('adminPassword').value;

        if (!username || !password) {
            showAlert('adminAlert', 'Please enter admin username and password.', 'error');
            return;
        }

        const loginBtn = document.getElementById('adminLoginBtn');
        if (loginBtn) {
            loginBtn.disabled = true;
            loginBtn.textContent = 'Authenticating...';
        }

        const res = await apiFetch('/admin/login', 'POST', { username, password });

        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.textContent = 'Login to Admin Portal';
        }

        if (res && res.success && res.token) {
            setAdminToken(res.token);
            setAdminSession(res.admin || { username, role: 'Administrator' });
            showAlert('adminAlert', 'Login successful! Opening dashboard...', 'success');
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 800);
        } else {
            showAlert('adminAlert', res ? res.message : 'Invalid administrator credentials.', 'error');
        }
    });
}

/**
 * Admin Session Guard & Logout Listener
 */
function checkAdminAuth() {
    const adminSessionUsername = document.getElementById('adminSessionUsername');
    const token = getAdminToken();

    if (!token && !window.location.href.includes('login.html')) {
        window.location.href = 'login.html';
        return false;
    }

    const session = getAdminSession();
    if (session && adminSessionUsername) {
        adminSessionUsername.textContent = session.username || 'Administrator';
    }

    const adminLogoutBtn = document.getElementById('adminLogoutBtn');
    if (adminLogoutBtn) {
        adminLogoutBtn.onclick = logoutAdmin;
    }

    return true;
}

/**
 * Render Admin Dashboard Metrics directly from MySQL Database
 */
async function initAdminDashboard() {
    const statTotalProducts = document.getElementById('statTotalProducts');
    if (!statTotalProducts) return;

    if (!checkAdminAuth()) return;

    const res = await apiFetch('/admin/dashboard', 'GET', null, true);

    if (res && res.success && res.metrics) {
        const m = res.metrics;
        statTotalProducts.textContent = m.total_products;
        
        const uEl = document.getElementById('statTotalUsers');
        const oEl = document.getElementById('statTotalOrders');
        const sEl = document.getElementById('statTotalSales');
        const pEl = document.getElementById('statPendingOrders');
        const lEl = document.getElementById('statLowStock');

        if (uEl) uEl.textContent = m.total_users;
        if (oEl) oEl.textContent = m.total_orders;
        if (sEl) sEl.textContent = formatCurrency(m.total_sales);
        if (pEl) pEl.textContent = m.pending_orders;
        if (lEl) lEl.textContent = m.low_stock;
    }
}

/**
 * Admin Product Management Page (Full CRUD connected to MySQL)
 */
async function initAdminProductsPage() {
    const adminProductsTableBody = document.getElementById('adminProductsTableBody');
    if (!adminProductsTableBody) return;

    if (!checkAdminAuth()) return;

    const modal = document.getElementById('productModal');
    const openModalBtn = document.getElementById('openAddProductModalBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const cancelModalBtn = document.getElementById('cancelModalBtn');
    const productForm = document.getElementById('productForm');
    const modalTitle = document.getElementById('modalTitle');
    const searchInput = document.getElementById('adminProductSearch');

    let currentProducts = [];

    async function renderAdminProductsTable(query = '') {
        adminProductsTableBody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 20px;">Loading inventory from MySQL...</td></tr>';

        const endpoint = query ? `/admin/products?search=${encodeURIComponent(query)}` : '/admin/products';
        const res = await apiFetch(endpoint, 'GET', null, true);

        if (!res || !res.success || !res.products) {
            adminProductsTableBody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 20px;" class="error-text">Failed to load products from database.</td></tr>';
            return;
        }

        currentProducts = res.products;
        adminProductsTableBody.innerHTML = '';

        if (currentProducts.length === 0) {
            adminProductsTableBody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 20px;">No products found in database.</td></tr>';
            return;
        }

        currentProducts.forEach(p => {
            const tr = document.createElement('tr');
            const isActive = (p.is_active !== 0);

            tr.innerHTML = `
                <td>#${p.product_id}</td>
                <td><img src="../${escapeHTML(p.image)}" alt="${escapeHTML(p.product_name)}" class="table-thumb" onerror="this.onerror=null; this.src='https://via.placeholder.com/40';"></td>
                <td><strong>${escapeHTML(p.product_name)}</strong></td>
                <td>${escapeHTML(p.category_name || 'General')}</td>
                <td>${formatCurrency(p.price)}</td>
                <td>${p.discount}%</td>
                <td>
                    <span class="badge-status ${p.stock < 5 ? 'status-cancelled' : 'status-delivered'}">${p.stock} In Stock</span>
                    ${!isActive ? '<span class="badge-status status-cancelled" style="margin-left:4px;">Deactivated</span>' : ''}
                </td>
                <td>★ ${p.rating}</td>
                <td class="table-actions-cell">
                    <button class="btn-sm btn-secondary edit-product-btn" data-id="${p.product_id}">Edit</button>
                    ${isActive ? `<button class="btn-sm btn-danger-outline delete-product-btn" data-id="${p.product_id}" title="Deactivates product without affecting previous orders">Deactivate</button>` : '<span style="font-size:0.8rem; color:var(--text-muted);">Inactive</span>'}
                </td>
            `;
            adminProductsTableBody.appendChild(tr);
        });

        // Edit Button Listeners
        adminProductsTableBody.querySelectorAll('.edit-product-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = parseInt(e.target.getAttribute('data-id'));
                openEditModal(id);
            });
        });

        // Deactivate Button Listeners
        adminProductsTableBody.querySelectorAll('.delete-product-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = parseInt(e.target.getAttribute('data-id'));
                const prod = currentProducts.find(p => p.product_id === id);

                if (confirm(`Deactivate product "${prod ? prod.product_name : id}"? Old order records will remain safe.`)) {
                    const delRes = await apiFetch('/admin/product/delete', 'POST', { product_id: id }, true);
                    if (delRes && delRes.success) {
                        showAlert('productAdminAlert', 'Product deactivated. Historical orders remain intact.', 'success');
                        renderAdminProductsTable(searchInput ? searchInput.value : '');
                    } else {
                        showAlert('productAdminAlert', delRes ? delRes.message : 'Failed to deactivate product.', 'error');
                    }
                }
            });
        });
    }

    function openAddModal() {
        productForm.reset();
        document.getElementById('productId').value = '';
        modalTitle.textContent = 'Add New Product';
        modal.classList.remove('hidden');
    }

    function openEditModal(productId) {
        const product = currentProducts.find(p => p.product_id === productId);
        if (!product) return;

        document.getElementById('productId').value = product.product_id;
        document.getElementById('productName').value = product.product_name;
        document.getElementById('productCategorySelect').value = product.category_id || 1;
        document.getElementById('productPrice').value = product.price;
        document.getElementById('productDiscount').value = product.discount;
        document.getElementById('productStock').value = product.stock;
        document.getElementById('productRating').value = product.rating;
        document.getElementById('productImagePath').value = product.image;
        document.getElementById('productDescription').value = product.description;

        modalTitle.textContent = 'Edit Product #' + product.product_id;
        modal.classList.remove('hidden');
    }

    function closeModal() {
        modal.classList.add('hidden');
    }

    if (openModalBtn) openModalBtn.addEventListener('click', openAddModal);
    if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
    if (cancelModalBtn) cancelModalBtn.addEventListener('click', closeModal);
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => renderAdminProductsTable(e.target.value), 300);
        });
    }

    // Handle Add / Edit Submission
    productForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const idVal = document.getElementById('productId').value;
        const name = document.getElementById('productName').value.trim();
        const categoryId = parseInt(document.getElementById('productCategorySelect').value);
        const price = parseFloat(document.getElementById('productPrice').value);
        const discount = parseInt(document.getElementById('productDiscount').value) || 0;
        const stock = parseInt(document.getElementById('productStock').value);
        const rating = parseFloat(document.getElementById('productRating').value) || 4.5;
        const image = document.getElementById('productImagePath').value.trim() || 'images/phone.jpg';
        const description = document.getElementById('productDescription').value.trim();

        if (!name || isNaN(price) || isNaN(stock) || price <= 0 || stock < 0) {
            alert('Please fill out all required fields with valid positive numbers.');
            return;
        }

        const payload = {
            productName: name,
            categoryId: categoryId,
            price: price,
            discount: discount,
            stock: stock,
            rating: rating,
            image: image,
            description: description
        };

        let res;
        if (idVal) {
            payload.productId = parseInt(idVal);
            payload.is_active = 1;
            res = await apiFetch('/admin/product/update', 'POST', payload, true);
        } else {
            res = await apiFetch('/admin/product/add', 'POST', payload, true);
        }

        if (res && res.success) {
            closeModal();
            showAlert('productAdminAlert', res.message || 'Product saved successfully to MySQL!', 'success');
            renderAdminProductsTable(searchInput ? searchInput.value : '');
        } else {
            alert(res ? res.message : 'Failed to save product in database.');
        }
    });

    renderAdminProductsTable();
}

/**
 * Admin User Management Page (Customer Directory from MySQL)
 */
async function initAdminUsersPage() {
    const adminUsersTableBody = document.getElementById('adminUsersTableBody');
    if (!adminUsersTableBody) return;

    if (!checkAdminAuth()) return;

    const searchInput = document.getElementById('adminUserSearch');

    async function renderUsersTable(filter = '') {
        adminUsersTableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 20px;">Loading customer accounts from MySQL...</td></tr>';

        const endpoint = filter ? `/admin/users?search=${encodeURIComponent(filter)}` : '/admin/users';
        const res = await apiFetch(endpoint, 'GET', null, true);

        if (!res || !res.success || !res.users) {
            adminUsersTableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 20px;" class="error-text">Failed to load customer accounts.</td></tr>';
            return;
        }

        adminUsersTableBody.innerHTML = '';

        if (res.users.length === 0) {
            adminUsersTableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 20px;">No registered users found.</td></tr>';
            return;
        }

        res.users.forEach(u => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>#${u.user_id}</td>
                <td><strong>${escapeHTML(u.name)}</strong></td>
                <td>${escapeHTML(u.email)}</td>
                <td>${escapeHTML(u.phone)}</td>
                <td>${escapeHTML(u.address || 'N/A')}</td>
                <td>${(u.created_at || '').substring(0, 19)}</td>
            `;
            adminUsersTableBody.appendChild(tr);
        });
    }

    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => renderUsersTable(e.target.value), 300);
        });
    }

    renderUsersTable();
}

/**
 * Admin Order Management Page & Status Updates
 */
async function initAdminOrdersPage() {
    const adminOrdersTableBody = document.getElementById('adminOrdersTableBody');
    if (!adminOrdersTableBody) return;

    if (!checkAdminAuth()) return;

    const orderStatusFilter = document.getElementById('adminOrderStatusFilter');
    const orderSearchInput = document.getElementById('adminOrderSearch');
    let loadedOrders = [];

    async function renderOrdersTable() {
        adminOrdersTableBody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 20px;">Loading orders from MySQL...</td></tr>';

        const statusVal = orderStatusFilter ? orderStatusFilter.value : 'all';
        const searchVal = orderSearchInput ? orderSearchInput.value.trim() : '';

        const params = new URLSearchParams();
        if (statusVal && statusVal !== 'all') params.append('status', statusVal);
        if (searchVal) params.append('search', searchVal);

        const res = await apiFetch(`/admin/orders?${params.toString()}`, 'GET', null, true);

        if (!res || !res.success || !res.orders) {
            adminOrdersTableBody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 20px;" class="error-text">Failed to load orders from database.</td></tr>';
            return;
        }

        loadedOrders = res.orders;
        adminOrdersTableBody.innerHTML = '';

        if (loadedOrders.length === 0) {
            adminOrdersTableBody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 20px;">No matching customer orders found.</td></tr>';
            return;
        }

        loadedOrders.forEach(o => {
            const statusClass = 'status-' + (o.order_status || 'pending').toLowerCase();
            const tr = document.createElement('tr');

            tr.innerHTML = `
                <td><strong>#ORD-${o.order_id}</strong></td>
                <td>${escapeHTML(o.customer_name || 'Customer')}</td>
                <td>${(o.order_date || '').substring(0, 19)}</td>
                <td>${formatCurrency(o.total_amount)}</td>
                <td>${escapeHTML(o.payment_method)}</td>
                <td><span class="badge-status ${statusClass}">${escapeHTML(o.order_status)}</span></td>
                <td>
                    <select class="status-select-inline" data-id="${o.order_id}">
                        <option value="Pending" ${o.order_status === 'Pending' ? 'selected' : ''}>Pending</option>
                        <option value="Confirmed" ${o.order_status === 'Confirmed' ? 'selected' : ''}>Confirmed</option>
                        <option value="Processing" ${o.order_status === 'Processing' ? 'selected' : ''}>Processing</option>
                        <option value="Shipped" ${o.order_status === 'Shipped' ? 'selected' : ''}>Shipped</option>
                        <option value="Delivered" ${o.order_status === 'Delivered' ? 'selected' : ''}>Delivered</option>
                        <option value="Cancelled" ${o.order_status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                    </select>
                </td>
                <td>
                    <button class="btn-sm btn-secondary view-order-details-btn" data-id="${o.order_id}">Details</button>
                </td>
            `;
            adminOrdersTableBody.appendChild(tr);
        });

        // Inline Status Selector Change Listener
        adminOrdersTableBody.querySelectorAll('.status-select-inline').forEach(select => {
            select.addEventListener('change', async (e) => {
                const orderId = e.target.getAttribute('data-id');
                const newStatus = e.target.value;

                const notes = prompt(`Optional admin notes for updating Order #${orderId} to "${newStatus}" (will be emailed to customer and logged in audit trail):`, `Status changed to ${newStatus}`);
                if (notes === null) {
                    renderOrdersTable();
                    return;
                }

                const updateRes = await apiFetch('/admin/order/status', 'POST', {
                    order_id: parseInt(orderId),
                    status: newStatus,
                    notes: notes || undefined
                }, true);

                if (updateRes && updateRes.success) {
                    showAlert('orderAdminAlert', `Order #${orderId} status updated to "${newStatus}" in MySQL. Customer notified.`, 'success');
                    renderOrdersTable();
                } else {
                    alert(updateRes ? updateRes.message : 'Failed to update order status.');
                    renderOrdersTable();
                }
            });
        });

        // Details Modal Button Listeners
        adminOrdersTableBody.querySelectorAll('.view-order-details-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const orderId = parseInt(e.target.getAttribute('data-id'));
                openOrderModal(orderId);
            });
        });
    }

    // Modal Control Functions
    const modal = document.getElementById('orderDetailsModal');
    const closeBtn = document.getElementById('closeOrderModalBtn');
    const closeBottomBtn = document.getElementById('closeOrderModalBottomBtn');

    async function openOrderModal(orderId) {
        if (!modal) return;

        // Fetch detailed order data including audit trail history
        const res = await apiFetch(`/order?id=${orderId}`, 'GET', null, true);
        const order = (res && res.success && res.order) ? res.order : loadedOrders.find(o => o.order_id === orderId);
        if (!order) return;

        document.getElementById('modalOrderId').textContent = `#ORD-${order.order_id}`;
        document.getElementById('modalCustomerName').textContent = order.customer_name || 'Customer';
        document.getElementById('modalCustomerEmail').textContent = order.customer_email || 'N/A';
        document.getElementById('modalCustomerPhone').textContent = order.customer_phone || 'N/A';
        document.getElementById('modalShippingAddress').textContent = order.shipping_address;
        document.getElementById('modalPaymentMethod').textContent = order.payment_method;

        const statusBadge = document.getElementById('modalOrderStatus');
        statusBadge.textContent = order.order_status;
        statusBadge.className = `badge-status status-${(order.order_status || 'pending').toLowerCase()}`;

        const itemsBody = document.getElementById('modalOrderItemsBody');
        itemsBody.innerHTML = '';
        if (order.items && order.items.length > 0) {
            order.items.forEach(item => {
                const tr = document.createElement('tr');
                const price = parseFloat(item.price);
                const qty = parseInt(item.quantity);
                tr.innerHTML = `
                    <td><strong>${escapeHTML(item.product_name)}</strong></td>
                    <td>${qty}</td>
                    <td>${formatCurrency(price)}</td>
                    <td>${formatCurrency(price * qty)}</td>
                `;
                itemsBody.appendChild(tr);
            });
        } else {
            itemsBody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No line items recorded.</td></tr>';
        }

        // Render Status Change & Audit History
        const historyBody = document.getElementById('modalOrderHistoryBody');
        if (historyBody) {
            historyBody.innerHTML = '';
            if (order.history && order.history.length > 0) {
                order.history.forEach(h => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><span class="badge-status status-${(h.status || 'pending').toLowerCase()}">${escapeHTML(h.status)}</span></td>
                        <td>${escapeHTML(h.changed_by || 'system')}</td>
                        <td>${escapeHTML(h.notes || '—')}</td>
                        <td>${(h.created_at || '').substring(0, 19)}</td>
                    `;
                    historyBody.appendChild(tr);
                });
            } else {
                historyBody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-light);">No status change history recorded yet.</td></tr>';
            }
        }

        modal.classList.remove('hidden');
    }

    if (closeBtn) closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
    if (closeBottomBtn) closeBottomBtn.addEventListener('click', () => modal.classList.add('hidden'));

    if (orderStatusFilter) orderStatusFilter.addEventListener('change', renderOrdersTable);
    if (orderSearchInput) {
        let debounceTimer;
        orderSearchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(renderOrdersTable, 300);
        });
    }

    renderOrdersTable();
}

/**
 * Admin Product Review Moderation Page
 */
async function initAdminReviewsPage() {
    const adminReviewsTableBody = document.getElementById('adminReviewsTableBody');
    if (!adminReviewsTableBody) return;

    if (!checkAdminAuth()) return;

    const searchInput = document.getElementById('adminReviewSearch');

    async function renderReviewsTable(query = '') {
        adminReviewsTableBody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 20px;">Loading customer reviews from MySQL...</td></tr>';

        const endpoint = query ? `/admin/reviews?search=${encodeURIComponent(query)}` : '/admin/reviews';
        const res = await apiFetch(endpoint, 'GET', null, true);

        if (!res || !res.success || !res.reviews) {
            adminReviewsTableBody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 20px;" class="error-text">Failed to load reviews from database.</td></tr>';
            return;
        }

        adminReviewsTableBody.innerHTML = '';

        if (res.reviews.length === 0) {
            adminReviewsTableBody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 20px;">No product reviews found.</td></tr>';
            return;
        }

        res.reviews.forEach(r => {
            const tr = document.createElement('tr');
            const verifiedBadge = r.is_verified_purchase 
                ? '<span style="color:#059669; font-weight:600; font-size:0.8rem;">✓ Verified</span>' 
                : '<span style="color:#9ca3af; font-size:0.8rem;">Standard</span>';
            const stars = '★'.repeat(r.rating) + '☆'.repeat(Math.max(0, 5 - r.rating));

            tr.innerHTML = `
                <td>#REV-${r.review_id}</td>
                <td><strong>${escapeHTML(r.product_name || 'Product #' + r.product_id)}</strong></td>
                <td>${escapeHTML(r.reviewer_name)}<br><small style="color:var(--text-light);">${escapeHTML(r.reviewer_email || '')}</small></td>
                <td><span style="color:#f59e0b; font-size:1.1rem;">${stars}</span> (${r.rating}/5)</td>
                <td><strong>${escapeHTML(r.review_title)}</strong><br><small>${escapeHTML(r.review_text)}</small></td>
                <td>${verifiedBadge}</td>
                <td>${(r.created_at || '').substring(0, 10)}</td>
                <td>
                    <button class="btn-sm btn-danger delete-review-btn" data-id="${r.review_id}">Delete</button>
                </td>
            `;
            adminReviewsTableBody.appendChild(tr);
        });

        // Delete Review Button Listeners
        adminReviewsTableBody.querySelectorAll('.delete-review-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const reviewId = parseInt(e.target.getAttribute('data-id'));
                if (!confirm(`Are you sure you want to permanently delete Review #REV-${reviewId}?`)) {
                    return;
                }

                const delRes = await apiFetch('/reviews/delete', 'POST', { review_id: reviewId }, true);
                if (delRes && delRes.success) {
                    showAlert('reviewAdminAlert', `Review #REV-${reviewId} successfully deleted from MySQL.`, 'success');
                    renderReviewsTable(searchInput ? searchInput.value : '');
                } else {
                    alert(delRes ? delRes.message : 'Failed to delete review.');
                }
            });
        });
    }

    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => renderReviewsTable(e.target.value), 300);
        });
    }

    renderReviewsTable();
}
