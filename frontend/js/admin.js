/**
 * ShopNow - Online Shopping System
 * Admin Panel Interactive Operations JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    initAdminLogin();
    initAdminDashboard();
    initAdminProductsPage();
    initAdminUsersPage();
    initAdminOrdersPage();
});

/**
 * Handle Admin Authentication Login
 */
function initAdminLogin() {
    const adminLoginForm = document.getElementById('adminLoginForm');
    if (!adminLoginForm) return;

    adminLoginForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const username = document.getElementById('adminUsername').value.trim();
        const password = document.getElementById('adminPassword').value;

        if (!username || !password) {
            showAlert('adminAlert', 'Please enter admin username and password.', 'error');
            return;
        }

        // Demo Admin Credentials Validation (Will be verified by Python backend later)
        if (username === 'admin' && password === 'admin123') {
            setAdminSession({ username: 'admin', role: 'Administrator' });
            showAlert('adminAlert', 'Login successful! Opening dashboard...', 'success');
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1000);
        } else {
            showAlert('adminAlert', 'Invalid administrator credentials. Try: admin / admin123', 'error');
        }
    });
}

/**
 * Admin Session Guard & Logout Listener
 */
function checkAdminAuth() {
    const adminSessionUsername = document.getElementById('adminSessionUsername');
    if (!adminSessionUsername) return; // Not an admin page

    const session = getAdminSession();
    if (!session && !window.location.href.includes('login.html')) {
        window.location.href = 'login.html';
        return;
    }

    if (session && adminSessionUsername) {
        adminSessionUsername.textContent = session.username;
    }

    const adminLogoutBtn = document.getElementById('adminLogoutBtn');
    if (adminLogoutBtn) {
        adminLogoutBtn.addEventListener('click', () => {
            localStorage.removeItem(STORAGE_KEYS.ADMIN);
            window.location.href = 'login.html';
        });
    }
}

/**
 * Calculate & Render Admin Dashboard Metric Statistics
 */
function initAdminDashboard() {
    const statTotalProducts = document.getElementById('statTotalProducts');
    if (!statTotalProducts) return;

    checkAdminAuth();

    const products = getProducts();
    const registeredUsers = JSON.parse(localStorage.getItem('shopnow_registered_users')) || [
        { user_id: 'USR-101', name: 'John Doe', email: 'john@example.com', phone: '+1 555-0192', created_at: '2026-09-01' },
        { user_id: 'USR-102', name: 'Jane Smith', email: 'jane@example.com', phone: '+1 555-0144', created_at: '2026-09-05' }
    ];
    const ordersHistory = JSON.parse(localStorage.getItem(STORAGE_KEYS.ORDERS)) || [];

    // Calculate Totals
    const totalProducts = products.length;
    const totalUsers = registeredUsers.length;
    const totalOrders = ordersHistory.length;
    
    const totalSales = ordersHistory.reduce((sum, order) => sum + parseFloat(order.total_amount || 0), 0);
    const pendingOrders = ordersHistory.filter(o => o.order_status === 'Pending').length;
    const lowStockCount = products.filter(p => p.stock < 5).length;

    // Populate DOM Metric Cards
    statTotalProducts.textContent = totalProducts;
    document.getElementById('statTotalUsers').textContent = totalUsers;
    document.getElementById('statTotalOrders').textContent = totalOrders;
    document.getElementById('statTotalSales').textContent = formatCurrency(totalSales);
    document.getElementById('statPendingOrders').textContent = pendingOrders;
    document.getElementById('statLowStock').textContent = lowStockCount;
}

/**
 * Admin Product Management Page (CRUD Operations)
 */
function initAdminProductsPage() {
    const adminProductsTableBody = document.getElementById('adminProductsTableBody');
    if (!adminProductsTableBody) return;

    checkAdminAuth();

    const modal = document.getElementById('productModal');
    const openModalBtn = document.getElementById('openAddProductModalBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const cancelModalBtn = document.getElementById('cancelModalBtn');
    const productForm = document.getElementById('productForm');
    const modalTitle = document.getElementById('modalTitle');
    const searchInput = document.getElementById('adminProductSearch');

    function renderAdminProductsTable(filterQuery = '') {
        const products = getProducts();
        adminProductsTableBody.innerHTML = '';

        let filtered = products;
        if (filterQuery.trim()) {
            const q = filterQuery.toLowerCase();
            filtered = products.filter(p => p.name.toLowerCase().includes(q) || (p.category_name && p.category_name.toLowerCase().includes(q)));
        }

        filtered.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${p.id}</td>
                <td><img src="../${p.image}" alt="${p.name}" class="table-thumb" onerror="this.onerror=null; this.src='https://via.placeholder.com/40';"></td>
                <td><strong>${p.name}</strong></td>
                <td>${p.category_name || 'General'}</td>
                <td>${formatCurrency(p.price)}</td>
                <td>${p.discount}%</td>
                <td><span class="badge-status ${p.stock < 5 ? 'status-cancelled' : 'status-delivered'}">${p.stock} In Stock</span></td>
                <td>★ ${p.rating}</td>
                <td class="table-actions-cell">
                    <button class="btn-sm btn-secondary edit-product-btn" data-id="${p.id}">Edit</button>
                    <button class="btn-sm btn-danger-outline delete-product-btn" data-id="${p.id}">Delete</button>
                </td>
            `;
            adminProductsTableBody.appendChild(tr);
        });

        // Edit Button Event Listeners
        adminProductsTableBody.querySelectorAll('.edit-product-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = parseInt(e.target.getAttribute('data-id'));
                openEditModal(id);
            });
        });

        // Delete Button Event Listeners with Confirmation
        adminProductsTableBody.querySelectorAll('.delete-product-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = parseInt(e.target.getAttribute('data-id'));
                const prod = products.find(p => p.id === id);

                if (confirm(`Are you sure you want to delete "${prod ? prod.name : 'this product'}"?`)) {
                    const updated = products.filter(p => p.id !== id);
                    saveProducts(updated);
                    renderAdminProductsTable(searchInput ? searchInput.value : '');
                    showAlert('productAdminAlert', 'Product deleted successfully.', 'success');
                }
            });
        });
    }

    // Modal Control Functions
    function openAddModal() {
        productForm.reset();
        document.getElementById('productId').value = '';
        modalTitle.textContent = 'Add New Product';
        modal.classList.remove('hidden');
    }

    function openEditModal(productId) {
        const products = getProducts();
        const product = products.find(p => p.id === productId);
        if (!product) return;

        document.getElementById('productId').value = product.id;
        document.getElementById('productName').value = product.name;
        document.getElementById('productCategorySelect').value = product.category_id || 1;
        document.getElementById('productPrice').value = product.price;
        document.getElementById('productDiscount').value = product.discount;
        document.getElementById('productStock').value = product.stock;
        document.getElementById('productRating').value = product.rating;
        document.getElementById('productImagePath').value = product.image;
        document.getElementById('productDescription').value = product.description;

        modalTitle.textContent = 'Edit Product #' + product.id;
        modal.classList.remove('hidden');
    }

    function closeModal() {
        modal.classList.add('hidden');
    }

    // Modal Listeners
    if (openModalBtn) openModalBtn.addEventListener('click', openAddModal);
    if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
    if (cancelModalBtn) cancelModalBtn.addEventListener('click', closeModal);
    if (searchInput) searchInput.addEventListener('input', (e) => renderAdminProductsTable(e.target.value));

    // Handle Add/Edit Form Submit
    productForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const idVal = document.getElementById('productId').value;
        const name = document.getElementById('productName').value.trim();
        const categoryId = parseInt(document.getElementById('productCategorySelect').value);
        const categoryName = document.getElementById('productCategorySelect').options[document.getElementById('productCategorySelect').selectedIndex].text;
        const price = parseFloat(document.getElementById('productPrice').value);
        const discount = parseInt(document.getElementById('productDiscount').value) || 0;
        const stock = parseInt(document.getElementById('productStock').value);
        const rating = parseFloat(document.getElementById('productRating').value) || 4.5;
        const image = document.getElementById('productImagePath').value.trim();
        const description = document.getElementById('productDescription').value.trim();

        if (!name || isNaN(price) || isNaN(stock) || !image || !description) {
            alert('Please fill out all required product fields correctly.');
            return;
        }

        let products = getProducts();

        if (idVal) {
            // Edit existing product
            const pId = parseInt(idVal);
            const index = products.findIndex(p => p.id === pId);
            if (index > -1) {
                products[index] = { id: pId, name, category_id: categoryId, category_name: categoryName, price, discount, stock, rating, image, description };
            }
        } else {
            // Add new product
            const newId = products.length ? Math.max(...products.map(p => p.id)) + 1 : 1;
            products.push({ id: newId, name, category_id: categoryId, category_name: categoryName, price, discount, stock, rating, image, description });
        }

        saveProducts(products);
        closeModal();
        renderAdminProductsTable();
        showAlert('productAdminAlert', 'Product saved successfully!', 'success');
    });

    renderAdminProductsTable();
}

/**
 * Admin User Management Page
 */
function initAdminUsersPage() {
    const adminUsersTableBody = document.getElementById('adminUsersTableBody');
    if (!adminUsersTableBody) return;

    checkAdminAuth();

    const registeredUsers = JSON.parse(localStorage.getItem('shopnow_registered_users')) || [
        { user_id: 'USR-101', name: 'John Doe', email: 'john@example.com', phone: '+1 555-0192', address: '123 University Campus St', created_at: '2026-09-01 10:15' },
        { user_id: 'USR-102', name: 'Jane Smith', email: 'jane@example.com', phone: '+1 555-0144', address: '456 Tech Park Boulevard', created_at: '2026-09-05 14:30' }
    ];

    const searchInput = document.getElementById('adminUserSearch');

    function renderUsersTable(filter = '') {
        adminUsersTableBody.innerHTML = '';
        let filtered = registeredUsers;

        if (filter.trim()) {
            const q = filter.toLowerCase();
            filtered = registeredUsers.filter(u => u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q));
        }

        filtered.forEach(u => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>#${u.user_id}</td>
                <td><strong>${u.name}</strong></td>
                <td>${u.email}</td>
                <td>${u.phone}</td>
                <td>${u.address || 'N/A'}</td>
                <td>${u.created_at || '2026-09-01'}</td>
            `;
            adminUsersTableBody.appendChild(tr);
        });
    }

    if (searchInput) searchInput.addEventListener('input', (e) => renderUsersTable(e.target.value));
    renderUsersTable();
}

/**
 * Admin Order Management Page & Status Updates
 */
function initAdminOrdersPage() {
    const adminOrdersTableBody = document.getElementById('adminOrdersTableBody');
    if (!adminOrdersTableBody) return;

    checkAdminAuth();

    const orderStatusFilter = document.getElementById('adminOrderStatusFilter');
    const orderSearchInput = document.getElementById('adminOrderSearch');

    function renderOrdersTable() {
        const ordersHistory = JSON.parse(localStorage.getItem(STORAGE_KEYS.ORDERS)) || [
            {
                order_id: 'ORD-10024',
                customer_name: 'John Doe',
                customer_email: 'john@example.com',
                customer_phone: '+1 555-0192',
                shipping_address: '123 University Campus St, Apt 4B',
                total_amount: 714.99,
                payment_method: 'Cash on Delivery',
                order_status: 'Pending',
                order_date: '2026-09-13',
                items: [{ product_name: 'Pro Wireless Smartphone 128GB', quantity: 1, price: 699.99 }]
            }
        ];

        adminOrdersTableBody.innerHTML = '';
        let filtered = ordersHistory;

        // Status Filter
        if (orderStatusFilter && orderStatusFilter.value !== 'all') {
            filtered = filtered.filter(o => o.order_status === orderStatusFilter.value);
        }

        // Text Search Filter
        if (orderSearchInput && orderSearchInput.value.trim()) {
            const q = orderSearchInput.value.trim().toLowerCase();
            filtered = filtered.filter(o => o.order_id.toLowerCase().includes(q) || o.customer_name.toLowerCase().includes(q));
        }

        filtered.forEach(o => {
            const statusClass = 'status-' + o.order_status.toLowerCase();
            const tr = document.createElement('tr');

            tr.innerHTML = `
                <td><strong>#${o.order_id}</strong></td>
                <td>${o.customer_name}</td>
                <td>${o.order_date}</td>
                <td>${formatCurrency(o.total_amount)}</td>
                <td>${o.payment_method}</td>
                <td><span class="badge-status ${statusClass}">${o.order_status}</span></td>
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
            select.addEventListener('change', (e) => {
                const orderId = e.target.getAttribute('data-id');
                const newStatus = e.target.value;

                let orders = JSON.parse(localStorage.getItem(STORAGE_KEYS.ORDERS)) || ordersHistory;
                const order = orders.find(o => o.order_id === orderId);
                if (order) {
                    order.order_status = newStatus;
                    localStorage.setItem(STORAGE_KEYS.ORDERS, JSON.stringify(orders));
                    showAlert('orderAdminAlert', `Order #${orderId} status updated to "${newStatus}".`, 'success');
                    renderOrdersTable();
                }
            });
        });

        // Details Modal Listener
        adminOrdersTableBody.querySelectorAll('.view-order-details-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const orderId = e.target.getAttribute('data-id');
                openOrderModal(orderId);
            });
        });
    }

    // Modal Control Functions
    const modal = document.getElementById('orderDetailsModal');
    const closeBtn = document.getElementById('closeOrderModalBtn');
    const closeBottomBtn = document.getElementById('closeOrderModalBottomBtn');

    function openOrderModal(orderId) {
        const ordersHistory = JSON.parse(localStorage.getItem(STORAGE_KEYS.ORDERS)) || [];
        const order = ordersHistory.find(o => o.order_id === orderId);
        if (!order || !modal) return;

        document.getElementById('modalOrderId').textContent = `#${order.order_id}`;
        document.getElementById('modalCustomerName').textContent = order.customer_name;
        document.getElementById('modalCustomerEmail').textContent = order.customer_email || 'N/A';
        document.getElementById('modalCustomerPhone').textContent = order.customer_phone || 'N/A';
        document.getElementById('modalShippingAddress').textContent = order.shipping_address;
        document.getElementById('modalPaymentMethod').textContent = order.payment_method;

        const statusBadge = document.getElementById('modalOrderStatus');
        statusBadge.textContent = order.order_status;
        statusBadge.className = `badge-status status-${order.order_status.toLowerCase()}`;

        const itemsBody = document.getElementById('modalOrderItemsBody');
        itemsBody.innerHTML = '';
        if (order.items) {
            order.items.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${item.product_name}</td>
                    <td>${item.quantity}</td>
                    <td>${formatCurrency(item.price)}</td>
                    <td>${formatCurrency(item.price * item.quantity)}</td>
                `;
                itemsBody.appendChild(tr);
            });
        }

        modal.classList.remove('hidden');
    }

    if (closeBtn) closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
    if (closeBottomBtn) closeBottomBtn.addEventListener('click', () => modal.classList.add('hidden'));

    if (orderStatusFilter) orderStatusFilter.addEventListener('change', renderOrdersTable);
    if (orderSearchInput) orderSearchInput.addEventListener('input', renderOrdersTable);

    renderOrdersTable();
}
