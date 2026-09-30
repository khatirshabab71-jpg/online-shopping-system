/**
 * ShopNow - Online Shopping System
 * Products Browsing, Filtering, Search & Details JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    initHomePageProducts();
    initProductsCatalogPage();
    initProductDetailsPage();
});

/**
 * Render Home Page Product Lists (Featured, Deals, New Arrivals)
 */
function initHomePageProducts() {
    const featuredGrid = document.getElementById('featuredProductsGrid');
    if (!featuredGrid) return;

    const products = getProducts();

    // Featured Products (First 4)
    renderProductCards(featuredGrid, products.slice(0, 4));

    // Discounted Products
    const discountGrid = document.getElementById('discountProductsGrid');
    if (discountGrid) {
        const discounted = products.filter(p => p.discount > 0);
        renderProductCards(discountGrid, discounted.length ? discounted : products.slice(0, 4));
    }

    // New Arrivals
    const newGrid = document.getElementById('newProductsGrid');
    if (newGrid) {
        renderProductCards(newGrid, [...products].reverse().slice(0, 4));
    }
}

/**
 * Render Catalog Page with Search, Category Filter, and Sorting
 */
function initProductsCatalogPage() {
    const productsGrid = document.getElementById('productsGrid');
    if (!productsGrid) return;

    let allProducts = getProducts();

    const categoryFilter = document.getElementById('categoryFilter');
    const sortFilter = document.getElementById('sortFilter');
    const stockFilter = document.getElementById('stockFilter');
    const applyFilterBtn = document.getElementById('applyFilterBtn');
    const resetFilterBtn = document.getElementById('resetFilterBtn');

    // Handle URL search parameter
    const searchQuery = getUrlParam('search');
    const searchInput = document.getElementById('searchInput');
    if (searchQuery && searchInput) {
        searchInput.value = searchQuery;
    }

    // Handle Category parameter
    const urlCategory = getUrlParam('category');
    if (urlCategory && categoryFilter) {
        // Match by id or category name string
        for (let i = 0; i < categoryFilter.options.length; i++) {
            const opt = categoryFilter.options[i];
            if (opt.value === urlCategory || opt.text.toLowerCase().includes(urlCategory.toLowerCase())) {
                categoryFilter.selectedIndex = i;
                break;
            }
        }
    }

    // Filter & Render Function
    function filterAndRender() {
        let filtered = [...allProducts];

        // 1. Search Query Filter
        const query = (searchInput ? searchInput.value : searchQuery || '').trim().toLowerCase();
        if (query) {
            filtered = filtered.filter(p => 
                p.name.toLowerCase().includes(query) || 
                p.description.toLowerCase().includes(query) ||
                (p.category_name && p.category_name.toLowerCase().includes(query))
            );
        }

        // 2. Category Filter
        const selectedCategory = categoryFilter ? categoryFilter.value : 'all';
        if (selectedCategory !== 'all') {
            filtered = filtered.filter(p => p.category_id.toString() === selectedCategory || p.category_name.toLowerCase() === selectedCategory.toLowerCase());
        }

        // 3. Stock Filter
        const selectedStock = stockFilter ? stockFilter.value : 'all';
        if (selectedStock === 'in-stock') {
            filtered = filtered.filter(p => p.stock > 0);
        }

        // 4. Sorting
        const selectedSort = sortFilter ? sortFilter.value : 'default';
        if (selectedSort === 'price-low') {
            filtered.sort((a, b) => getDiscountedPrice(a.price, a.discount) - getDiscountedPrice(b.price, b.discount));
        } else if (selectedSort === 'price-high') {
            filtered.sort((a, b) => getDiscountedPrice(b.price, b.discount) - getDiscountedPrice(a.price, a.discount));
        } else if (selectedSort === 'rating') {
            filtered.sort((a, b) => b.rating - a.rating);
        } else if (selectedSort === 'newest') {
            filtered.sort((a, b) => b.id - a.id);
        }

        // Render UI Results
        const noProductsFound = document.getElementById('noProductsFound');
        const countInfo = document.getElementById('productCountInfo');

        if (filtered.length === 0) {
            productsGrid.innerHTML = '';
            if (noProductsFound) noProductsFound.classList.remove('hidden');
            if (countInfo) countInfo.textContent = 'Showing 0 products';
        } else {
            if (noProductsFound) noProductsFound.classList.add('hidden');
            if (countInfo) countInfo.textContent = `Showing ${filtered.length} product(s)`;
            renderProductCards(productsGrid, filtered);
        }
    }

    // Event Listeners for Filters
    if (applyFilterBtn) applyFilterBtn.addEventListener('click', filterAndRender);
    if (resetFilterBtn) {
        resetFilterBtn.addEventListener('click', () => {
            if (categoryFilter) categoryFilter.value = 'all';
            if (sortFilter) sortFilter.value = 'default';
            if (stockFilter) stockFilter.value = 'all';
            if (searchInput) searchInput.value = '';
            filterAndRender();
        });
    }

    // Initial render
    filterAndRender();
}

/**
 * Render Product Details Page View
 */
function initProductDetailsPage() {
    const detailsContainer = document.getElementById('productDetailsContainer');
    if (!detailsContainer) return;

    const productId = parseInt(getUrlParam('id')) || 1;
    const products = getProducts();
    const product = products.find(p => p.id === productId) || products[0];

    if (!product) return;

    // Update Page Elements
    document.title = `${product.name} - ShopNow`;
    document.getElementById('breadcrumbProductName').textContent = product.name;
    document.getElementById('productTitle').textContent = product.name;
    document.getElementById('productCategory').textContent = product.category_name || 'Category';
    document.getElementById('productDescription').textContent = product.description;
    
    // Ratings
    document.getElementById('productStars').textContent = getStarRating(product.rating);
    document.getElementById('productRatingVal').textContent = `${product.rating} Rating`;

    // Pricing
    const finalPrice = getDiscountedPrice(product.price, product.discount);
    document.getElementById('productPrice').textContent = formatCurrency(finalPrice);
    
    const originalPriceElem = document.getElementById('productOriginalPrice');
    const discountBadgeElem = document.getElementById('productDiscountBadge');

    if (product.discount > 0) {
        if (originalPriceElem) {
            originalPriceElem.textContent = formatCurrency(product.price);
            originalPriceElem.classList.remove('hidden');
        }
        if (discountBadgeElem) {
            discountBadgeElem.textContent = `-${product.discount}% OFF`;
            discountBadgeElem.classList.remove('hidden');
        }
    }

    // Stock Status
    const stockElem = document.getElementById('productStockStatus');
    if (stockElem) {
        if (product.stock > 0) {
            stockElem.className = 'stock-status in-stock';
            stockElem.textContent = `In Stock (${product.stock} items left)`;
        } else {
            stockElem.className = 'stock-status out-stock';
            stockElem.textContent = 'Out of Stock';
        }
    }

    // Image
    const imgElem = document.getElementById('productImage');
    if (imgElem) {
        imgElem.src = product.image;
        imgElem.alt = product.name;
    }

    // Quantity Picker Controls
    const qtyInput = document.getElementById('quantityInput');
    const decreaseBtn = document.getElementById('decreaseQtyBtn');
    const increaseBtn = document.getElementById('increaseQtyBtn');

    if (qtyInput && decreaseBtn && increaseBtn) {
        decreaseBtn.addEventListener('click', () => {
            let current = parseInt(qtyInput.value) || 1;
            if (current > 1) qtyInput.value = current - 1;
        });

        increaseBtn.addEventListener('click', () => {
            let current = parseInt(qtyInput.value) || 1;
            if (current < product.stock) qtyInput.value = current + 1;
        });
    }

    // Add to Cart Button
    const addToCartBtn = document.getElementById('addToCartBtn');
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', () => {
            const qty = parseInt(qtyInput ? qtyInput.value : 1) || 1;
            addToCart(product.id, qty);
        });
    }

    // Buy Now Button
    const buyNowBtn = document.getElementById('buyNowBtn');
    if (buyNowBtn) {
        buyNowBtn.addEventListener('click', () => {
            const qty = parseInt(qtyInput ? qtyInput.value : 1) || 1;
            addToCart(product.id, qty);
            window.location.href = 'checkout.html';
        });
    }

    // Render Related Products
    const relatedGrid = document.getElementById('relatedProductsGrid');
    if (relatedGrid) {
        const related = products.filter(p => p.id !== product.id).slice(0, 4);
        renderProductCards(relatedGrid, related);
    }
}

/**
 * Render Product Cards HTML Array
 */
function renderProductCards(container, productsList) {
    if (!container) return;
    container.innerHTML = '';

    productsList.forEach(p => {
        const finalPrice = getDiscountedPrice(p.price, p.discount);
        const card = document.createElement('div');
        card.className = 'product-card';

        card.innerHTML = `
            ${p.discount > 0 ? `<div class="product-badge">${p.discount}% OFF</div>` : ''}
            <div class="product-image-box">
                <img src="${p.image}" alt="${p.name}" onerror="this.onerror=null; this.src='https://via.placeholder.com/250x200?text=${encodeURIComponent(p.name)}';">
            </div>
            <div class="product-info">
                <span class="product-category">${p.category_name || 'General'}</span>
                <h3 class="product-title"><a href="product-details.html?id=${p.id}">${p.name}</a></h3>
                <div class="product-rating">
                    <span class="stars">${getStarRating(p.rating)}</span>
                    <span class="rating-val">(${p.rating})</span>
                </div>
                <div class="product-price-box">
                    <span class="current-price">${formatCurrency(finalPrice)}</span>
                    ${p.discount > 0 ? `<span class="original-price">${formatCurrency(p.price)}</span>` : ''}
                </div>
                <div class="product-actions">
                    <a href="product-details.html?id=${p.id}" class="btn-secondary">Details</a>
                    <button class="btn-add-cart" data-id="${p.id}">Add to Cart</button>
                </div>
            </div>
        `;

        container.appendChild(card);
    });

    // Attach event listeners for Add to Cart buttons
    container.querySelectorAll('.btn-add-cart').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pId = parseInt(e.target.getAttribute('data-id'));
            addToCart(pId, 1);
        });
    });
}

/**
 * Convert Numerical Rating to Star Strings
 */
function getStarRating(rating) {
    const fullStars = Math.floor(rating);
    const halfStar = rating % 1 >= 0.5 ? '★' : '';
    const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
    return '★'.repeat(fullStars) + halfStar + '☆'.repeat(emptyStars);
}
