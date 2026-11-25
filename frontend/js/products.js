/**
 * ShopNow - Online Shopping System
 * Products Browsing, Advanced Filtering, Multi-Facet Search, Reviews & Details JavaScript
 * Phase 2: Wishlist controls, reviews with verified purchase badges, price/rating filters, pagination.
 */

document.addEventListener('DOMContentLoaded', () => {
    initHomePageProducts();
    initProductsCatalogPage();
    initProductDetailsPage();
});

/**
 * Render Home Page Product Lists (Featured, Deals, New Arrivals) from MySQL
 */
async function initHomePageProducts() {
    const featuredGrid = document.getElementById('featuredProductsGrid');
    if (!featuredGrid) return;

    featuredGrid.innerHTML = '<div class="loading-spinner">Loading featured products from database...</div>';

    const res = await apiFetch('/products?limit=12');
    if (!res || !res.success || !res.products) {
        featuredGrid.innerHTML = '<p class="error-text">Failed to load products from server. Please verify the Python backend is running.</p>';
        return;
    }

    const products = res.products;

    // 1. Featured Products (First 4)
    renderProductCards(featuredGrid, products.slice(0, 4));

    // 2. Discounted Deals
    const discountGrid = document.getElementById('discountProductsGrid');
    if (discountGrid) {
        const discounted = products.filter(p => p.discount > 0);
        renderProductCards(discountGrid, discounted.length ? discounted.slice(0, 4) : products.slice(0, 4));
    }

    // 3. New Arrivals (Last 4)
    const newGrid = document.getElementById('newProductsGrid');
    if (newGrid) {
        const reversed = [...products].reverse();
        renderProductCards(newGrid, reversed.slice(0, 4));
    }
}

/**
 * Render Catalog Page with Server-side Multi-Facet Filtering, Sorting & Pagination
 */
async function initProductsCatalogPage() {
    const productsGrid = document.getElementById('productsGrid');
    if (!productsGrid) return;

    const categoryFilter = document.getElementById('categoryFilter');
    const sortFilter = document.getElementById('sortFilter');
    const stockFilter = document.getElementById('stockFilter');
    const minRatingFilter = document.getElementById('minRatingFilter');
    const minPriceInput = document.getElementById('minPriceInput');
    const maxPriceInput = document.getElementById('maxPriceInput');
    const applyFilterBtn = document.getElementById('applyFilterBtn');
    const resetFilterBtn = document.getElementById('resetFilterBtn');
    const searchInput = document.getElementById('searchInput');
    const paginationContainer = document.getElementById('paginationControls');

    let currentPage = 1;

    // Pre-fill search input from URL param if present
    const urlSearch = getUrlParam('search');
    if (urlSearch && searchInput) {
        searchInput.value = urlSearch;
    }

    // Pre-select category filter from URL param if present
    const urlCategory = getUrlParam('category');
    if (urlCategory && categoryFilter) {
        for (let i = 0; i < categoryFilter.options.length; i++) {
            const opt = categoryFilter.options[i];
            if (opt.value === urlCategory || opt.text.toLowerCase().includes(urlCategory.toLowerCase())) {
                categoryFilter.selectedIndex = i;
                break;
            }
        }
    }

    async function loadFilteredProducts(page = 1) {
        currentPage = page;
        productsGrid.innerHTML = '<div class="loading-spinner">Loading products from MySQL...</div>';

        const categoryVal = categoryFilter ? categoryFilter.value : 'all';
        const sortVal = sortFilter ? sortFilter.value : 'default';
        const stockVal = stockFilter ? stockFilter.value : 'all';
        const minRatingVal = minRatingFilter ? minRatingFilter.value : 'all';
        const minP = minPriceInput ? minPriceInput.value.trim() : '';
        const maxP = maxPriceInput ? maxPriceInput.value.trim() : '';
        const queryVal = (searchInput ? searchInput.value : urlSearch || '').trim();

        const params = new URLSearchParams();
        if (categoryVal && categoryVal !== 'all') params.append('category', categoryVal);
        if (sortVal && sortVal !== 'default') params.append('sort', sortVal);
        if (stockVal === 'in-stock') params.append('in_stock', 'true');
        if (minRatingVal && minRatingVal !== 'all') params.append('min_rating', minRatingVal);
        if (minP) params.append('min_price', minP);
        if (maxP) params.append('max_price', maxP);
        if (queryVal) params.append('search', queryVal);
        params.append('page', currentPage);
        params.append('limit', 9);

        const res = await apiFetch(`/products?${params.toString()}`);
        const noProductsFound = document.getElementById('noProductsFound');
        const countInfo = document.getElementById('productCountInfo');

        if (!res || !res.success || !res.products || res.products.length === 0) {
            productsGrid.innerHTML = '';
            if (noProductsFound) noProductsFound.classList.remove('hidden');
            if (countInfo) countInfo.textContent = 'Showing 0 products';
            if (paginationContainer) paginationContainer.innerHTML = '';
            return;
        }

        if (noProductsFound) noProductsFound.classList.add('hidden');
        if (countInfo) countInfo.textContent = `Showing ${res.products.length} of ${res.total} product(s) (Page ${res.page} of ${res.total_pages})`;
        
        renderProductCards(productsGrid, res.products);
        renderPagination(res.page, res.total_pages);
    }

    function renderPagination(page, totalPages) {
        if (!paginationContainer) return;
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let html = '';
        html += `<button class="btn-sm btn-secondary page-btn" data-page="${page - 1}" ${page <= 1 ? 'disabled style="opacity:0.5;"' : ''}>&larr; Prev</button>`;
        
        for (let i = 1; i <= totalPages; i++) {
            if (i === page) {
                html += `<button class="btn-sm btn-primary" style="font-weight:700;">${i}</button>`;
            } else if (i === 1 || i === totalPages || (i >= page - 1 && i <= page + 1)) {
                html += `<button class="btn-sm btn-secondary page-btn" data-page="${i}">${i}</button>`;
            } else if (i === page - 2 || i === page + 2) {
                html += `<span style="padding:0 4px; color:var(--text-muted);">...</span>`;
            }
        }

        html += `<button class="btn-sm btn-secondary page-btn" data-page="${page + 1}" ${page >= totalPages ? 'disabled style="opacity:0.5;"' : ''}>Next &rarr;</button>`;

        paginationContainer.innerHTML = html;

        paginationContainer.querySelectorAll('.page-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetPage = parseInt(e.target.getAttribute('data-page'));
                if (targetPage >= 1 && targetPage <= totalPages) {
                    loadFilteredProducts(targetPage);
                    window.scrollTo({ top: 150, behavior: 'smooth' });
                }
            });
        });
    }

    if (applyFilterBtn) applyFilterBtn.addEventListener('click', () => loadFilteredProducts(1));

    if (resetFilterBtn) {
        resetFilterBtn.addEventListener('click', () => {
            if (categoryFilter) categoryFilter.value = 'all';
            if (sortFilter) sortFilter.value = 'default';
            if (stockFilter) stockFilter.value = 'all';
            if (minRatingFilter) minRatingFilter.value = 'all';
            if (minPriceInput) minPriceInput.value = '';
            if (maxPriceInput) maxPriceInput.value = '';
            if (searchInput) searchInput.value = '';
            loadFilteredProducts(1);
        });
    }

    const clearSearchBtn = document.getElementById('clearSearchBtn');
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            loadFilteredProducts(1);
        });
    }

    // Initial load
    loadFilteredProducts(1);
}

/**
 * Render Product Details Page View with Wishlist Button & Reviews Section
 */
async function initProductDetailsPage() {
    const detailsContainer = document.getElementById('productDetailsContainer');
    if (!detailsContainer) return;

    const productId = parseInt(getUrlParam('id')) || 1;
    detailsContainer.innerHTML = '<div class="loading-spinner">Loading product details...</div>';

    const res = await apiFetch(`/product?id=${productId}`);
    if (!res || !res.success || !res.product) {
        detailsContainer.innerHTML = `
            <div class="empty-state">
                <h2>Product Not Found</h2>
                <p>The requested product is not available in our store catalog.</p>
                <a href="products.html" class="btn-primary">Browse All Products</a>
            </div>
        `;
        return;
    }

    const product = res.product;
    const finalPrice = getDiscountedPrice(product.price, product.discount);
    const hasDiscount = product.discount > 0;
    const inStock = product.stock > 0;

    detailsContainer.innerHTML = `
        <div class="product-details-wrapper">
            <div class="product-gallery">
                <div class="main-image-box">
                    <img id="detailMainImage" src="${escapeHTML(product.image)}" alt="${escapeHTML(product.product_name)}" onerror="this.onerror=null; this.src='https://via.placeholder.com/450x350?text=Product';">
                    ${hasDiscount ? `<span class="product-badge badge-details">${product.discount}% OFF</span>` : ''}
                </div>
            </div>

            <div class="product-essential-info">
                <div class="details-category-tag">${escapeHTML(product.category_name || 'Electronics')}</div>
                <h1 class="details-title">${escapeHTML(product.product_name)}</h1>

                <div class="details-meta-row">
                    <div class="product-rating">
                        <span class="stars">★★★★★</span>
                        <span class="rating-val" id="detailRatingVal">(${product.rating})</span>
                    </div>
                    <span class="details-stock-badge ${inStock ? 'in-stock' : 'out-of-stock'}">
                        ${inStock ? `✓ ${product.stock} In Stock` : '✕ Out of Stock'}
                    </span>
                </div>

                <div class="details-price-box">
                    <span class="details-current-price">${formatCurrency(finalPrice)}</span>
                    ${hasDiscount ? `<span class="details-original-price">${formatCurrency(product.price)}</span>` : ''}
                    ${hasDiscount ? `<span class="details-savings-text">Save ${product.discount}%</span>` : ''}
                </div>

                <div class="details-description">
                    <h3>Product Overview</h3>
                    <p>${escapeHTML(product.description)}</p>
                </div>

                <div class="purchase-actions-box">
                    <div class="qty-selector">
                        <label for="detailQuantity">Quantity:</label>
                        <div class="qty-control">
                            <button type="button" class="btn-qty" id="detailQtyDec">-</button>
                            <input type="number" id="detailQuantity" value="1" min="1" max="${product.stock || 1}">
                            <button type="button" class="btn-qty" id="detailQtyInc">+</button>
                        </div>
                    </div>

                    <div class="action-buttons-group" style="display:flex; gap:12px; flex-wrap:wrap; margin-top:15px;">
                        <button type="button" id="detailAddToCartBtn" class="btn-primary btn-large" style="flex:2;" ${!inStock ? 'disabled' : ''}>
                            ${inStock ? '🛒 Add to Shopping Cart' : 'Out of Stock'}
                        </button>
                        <button type="button" id="detailAddToWishlistBtn" class="btn-secondary btn-large" style="flex:1;" title="Save to Wishlist">
                            ❤️ Save to Wishlist
                        </button>
                    </div>
                </div>

                <div class="details-perks">
                    <div class="perk-item">🚚 Standard Delivery Available</div>
                    <div class="perk-item">💵 Cash on Delivery (COD) Accepted</div>
                    <div class="perk-item">🔒 Verified University Production MVP</div>
                </div>
            </div>
        </div>
    `;

    // Quantity selector buttons
    const qtyInput = document.getElementById('detailQuantity');
    const decBtn = document.getElementById('detailQtyDec');
    const incBtn = document.getElementById('detailQtyInc');
    const addBtn = document.getElementById('detailAddToCartBtn');
    const wishlistBtn = document.getElementById('detailAddToWishlistBtn');

    if (decBtn && qtyInput) {
        decBtn.addEventListener('click', () => {
            let val = parseInt(qtyInput.value) || 1;
            if (val > 1) qtyInput.value = val - 1;
        });
    }

    if (incBtn && qtyInput) {
        incBtn.addEventListener('click', () => {
            let val = parseInt(qtyInput.value) || 1;
            if (val < product.stock) qtyInput.value = val + 1;
        });
    }

    if (addBtn && qtyInput) {
        addBtn.addEventListener('click', () => {
            const quantity = parseInt(qtyInput.value) || 1;
            if (typeof addToCart === 'function') {
                addToCart(product.product_id, quantity);
            }
        });
    }

    if (wishlistBtn) {
        wishlistBtn.addEventListener('click', async () => {
            if (!getAuthToken()) {
                alert('Please log in to save items to your wishlist.');
                window.location.href = 'login.html';
                return;
            }
            wishlistBtn.disabled = true;
            const wRes = await apiFetch('/wishlist/add', 'POST', { product_id: product.product_id });
            wishlistBtn.disabled = false;
            if (wRes && wRes.success) {
                showToast(wRes.message || 'Saved to wishlist!', 'success');
                updateHeaderWishlistCount();
            } else {
                alert(wRes ? wRes.message : 'Could not add to wishlist.');
            }
        });
    }

    // Initialize Reviews Section for this product
    initProductReviewsSection(productId);
}

/**
 * Initialize Reviews and Ratings Section on Product Details Page
 */
async function initProductReviewsSection(productId) {
    const listContainer = document.getElementById('reviewsListContainer');
    const avgStarsEl = document.getElementById('summaryAvgStars');
    const totalReviewsEl = document.getElementById('summaryTotalReviews');
    const reviewForm = document.getElementById('writeReviewForm');

    // 1. Fetch rating summary
    const summaryRes = await apiFetch(`/reviews/summary?product_id=${productId}`);
    if (summaryRes && summaryRes.success && summaryRes.summary) {
        const s = summaryRes.summary;
        if (avgStarsEl) avgStarsEl.textContent = `★ ${s.average_rating}`;
        if (totalReviewsEl) totalReviewsEl.textContent = `Based on ${s.total_reviews} customer review(s)`;
    }

    // 2. Fetch list of reviews
    async function loadReviews() {
        if (!listContainer) return;
        const revRes = await apiFetch(`/reviews?product_id=${productId}`);

        if (!revRes || !revRes.success || !revRes.reviews || revRes.reviews.length === 0) {
            listContainer.innerHTML = `
                <div style="background:var(--bg-secondary); padding:25px; border-radius:var(--radius-md); text-align:center;">
                    <p style="margin:0; color:var(--text-muted); font-size:1rem;">No reviews yet for this product. Be the first to share your experience!</p>
                </div>
            `;
            return;
        }

        const currentUser = getCurrentUser();
        listContainer.innerHTML = '';

        revRes.reviews.forEach(r => {
            const card = document.createElement('div');
            card.className = 'review-card';
            card.style.cssText = 'background:#fff; border:1px solid var(--border-color); padding:18px; border-radius:var(--radius-md); margin-bottom:15px;';

            const isOwner = currentUser && (currentUser.user_id === r.user_id);
            const starsText = '★'.repeat(r.rating) + '☆'.repeat(5 - r.rating);

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                    <div>
                        <span style="color:#f59e0b; font-size:1.1rem; letter-spacing:1px;">${starsText}</span>
                        <strong style="margin-left:8px; font-size:1rem;">${escapeHTML(r.review_title)}</strong>
                    </div>
                    ${r.is_verified_purchase ? '<span class="badge-status status-delivered" style="font-size:0.75rem;">Verified Purchase ✓</span>' : ''}
                </div>
                <p style="margin:8px 0; font-size:0.95rem; line-height:1.5; color:var(--text-main);">${escapeHTML(r.review_text)}</p>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.8rem; color:var(--text-muted); margin-top:10px;">
                    <span>By <strong>${escapeHTML(r.reviewer_name)}</strong> on ${r.created_at}</span>
                    ${isOwner ? `<button class="btn-sm btn-danger-outline delete-rev-btn" data-id="${r.review_id}" style="padding:2px 8px; font-size:0.75rem;">Delete My Review</button>` : ''}
                </div>
            `;
            listContainer.appendChild(card);
        });

        // Delete button listener for review owner
        listContainer.querySelectorAll('.delete-rev-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const rId = parseInt(e.target.getAttribute('data-id'));
                if (confirm('Are you sure you want to delete your review?')) {
                    const delRes = await apiFetch('/reviews/delete', 'POST', { review_id: rId });
                    if (delRes && delRes.success) {
                        showToast('Review deleted', 'info');
                        loadReviews();
                    } else {
                        alert(delRes ? delRes.message : 'Could not delete review.');
                    }
                }
            });
        });
    }

    loadReviews();

    // 3. Handle review form submission
    if (reviewForm) {
        reviewForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (!getAuthToken()) {
                alert('Please sign in to submit a review.');
                window.location.href = 'login.html';
                return;
            }

            const rating = parseInt(document.getElementById('reviewRating').value) || 5;
            const title = document.getElementById('reviewTitle').value.trim();
            const text = document.getElementById('reviewText').value.trim();

            if (!title || title.length < 3) {
                showAlert('reviewAlert', 'Review title must be at least 3 characters.', 'error');
                return;
            }

            if (!text || text.length < 10) {
                showAlert('reviewAlert', 'Review text must be at least 10 characters long.', 'error');
                return;
            }

            const submitBtn = document.getElementById('submitReviewBtn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Submitting Review...';
            }

            const res = await apiFetch('/reviews/add', 'POST', {
                product_id: productId,
                rating: rating,
                review_title: title,
                review_text: text
            });

            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Review';
            }

            if (res && res.success) {
                showAlert('reviewAlert', res.message, 'success');
                reviewForm.reset();
                loadReviews();
            } else {
                showAlert('reviewAlert', res ? res.message : 'Failed to submit review.', 'error');
            }
        });
    }
}

/**
 * Universal Product Cards Grid Renderer with HTML escaping & Wishlist heart button
 */
function renderProductCards(container, productsList) {
    container.innerHTML = '';

    productsList.forEach(p => {
        const pId = p.product_id || p.id;
        const pName = p.product_name || p.name;
        const finalPrice = getDiscountedPrice(p.price, p.discount);
        const hasDiscount = p.discount > 0;
        const inStock = p.stock > 0;

        const card = document.createElement('div');
        card.className = 'product-card';
        card.innerHTML = `
            ${hasDiscount ? `<div class="product-badge">${p.discount}% OFF</div>` : ''}
            <div class="product-image-box">
                <a href="product-details.html?id=${pId}">
                    <img src="${escapeHTML(p.image)}" alt="${escapeHTML(pName)}" onerror="this.onerror=null; this.src='https://via.placeholder.com/250x200?text=Product';">
                </a>
                <button class="btn-card-wishlist" data-id="${pId}" title="Save to Wishlist" style="position:absolute; top:8px; right:8px; background:rgba(255,255,255,0.85); border:none; border-radius:50%; width:32px; height:32px; font-size:16px; cursor:pointer; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                    ❤️
                </button>
            </div>
            <div class="product-info">
                <span class="product-category">${escapeHTML(p.category_name || 'General')}</span>
                <h3 class="product-title"><a href="product-details.html?id=${pId}">${escapeHTML(pName)}</a></h3>
                <div class="product-rating">
                    <span class="stars">★★★★★</span>
                    <span class="rating-val">(${p.rating})</span>
                </div>
                <div class="product-price-box">
                    <span class="current-price">${formatCurrency(finalPrice)}</span>
                    ${hasDiscount ? `<span class="original-price">${formatCurrency(p.price)}</span>` : ''}
                </div>
                <div class="product-actions">
                    <a href="product-details.html?id=${pId}" class="btn-secondary">Details</a>
                    <button class="btn-add-cart btn-add-cart-action" data-id="${pId}" ${!inStock ? 'disabled style="opacity:0.6;"' : ''}>
                        ${inStock ? 'Add to Cart' : 'Out of Stock'}
                    </button>
                </div>
            </div>
        `;
        container.appendChild(card);
    });

    // Add to Cart click listeners
    container.querySelectorAll('.btn-add-cart-action').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const prodId = parseInt(e.target.getAttribute('data-id'));
            if (typeof addToCart === 'function') {
                addToCart(prodId, 1);
            }
        });
    });

    // Wishlist click listeners
    container.querySelectorAll('.btn-card-wishlist').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (!getAuthToken()) {
                alert('Please sign in to save items to your wishlist.');
                window.location.href = 'login.html';
                return;
            }
            const prodId = parseInt(btn.getAttribute('data-id'));
            btn.style.transform = 'scale(1.2)';
            const wRes = await apiFetch('/wishlist/add', 'POST', { product_id: prodId });
            setTimeout(() => { btn.style.transform = 'scale(1)'; }, 200);

            if (wRes && wRes.success) {
                showToast(wRes.message || 'Saved to wishlist!', 'success');
                updateHeaderWishlistCount();
            } else {
                alert(wRes ? wRes.message : 'Could not add to wishlist.');
            }
        });
    });
}
