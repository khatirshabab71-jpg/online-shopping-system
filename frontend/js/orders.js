/**
 * ShopNow - Online Shopping System
 * Customer Order History JavaScript
 * Fetches authenticated customer's real orders from Python API & MySQL.
 */

document.addEventListener('DOMContentLoaded', () => {
    initOrdersHistoryPage();
});

async function initOrdersHistoryPage() {
    const ordersTableBody = document.getElementById('ordersTableBody');
    const ordersTable = document.getElementById('ordersTable');
    const noOrdersMessage = document.getElementById('noOrdersMessage');

    if (!ordersTableBody) return;

    if (!getAuthToken()) {
        window.location.href = 'login.html';
        return;
    }

    ordersTableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 20px;">Loading your orders from database...</td></tr>';

    const res = await apiFetch('/orders');

    if (!res || !res.success || !res.orders || res.orders.length === 0) {
        if (ordersTable) ordersTable.classList.add('hidden');
        if (noOrdersMessage) noOrdersMessage.classList.remove('hidden');
        return;
    }

    if (ordersTable) ordersTable.classList.remove('hidden');
    if (noOrdersMessage) noOrdersMessage.classList.add('hidden');

    ordersTableBody.innerHTML = '';

    res.orders.forEach(order => {
        const tr = document.createElement('tr');
        const statusClass = 'status-' + (order.order_status || 'pending').toLowerCase();
        const dateStr = (order.order_date || '').substring(0, 10);

        tr.innerHTML = `
            <td><strong>#ORD-${order.order_id}</strong></td>
            <td>${dateStr}</td>
            <td>${formatCurrency(order.total_amount)}</td>
            <td>${escapeHTML(order.payment_method)}</td>
            <td><span class="badge-status ${statusClass}">${escapeHTML(order.order_status)}</span></td>
            <td>
                <a href="order-confirmation.html?id=${order.order_id}" class="btn-secondary btn-sm">View Details</a>
            </td>
        `;
        ordersTableBody.appendChild(tr);
    });
}
