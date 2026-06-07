// API Configuration
const API_BASE = `${window.location.origin}/api/v1`;
let cart = JSON.parse(localStorage.getItem('cart')) || [];
let currentProduct = null;
let userId = localStorage.getItem('userId') || 1;
let allProducts = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    loadRecommendations();
    loadTrendingProducts();
    updateCartCount();
    setupEventListeners();
    loadThemePreference();
});

// Event Listeners
function setupEventListeners() {
    document.getElementById('cartBtn').addEventListener('click', openCart);
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.getElementById('searchInput').addEventListener('input', filterProducts);
    document.getElementById('sortSelect').addEventListener('change', sortProducts);
    document.addEventListener('click', handleProductClick);
    
    // Modal close
    document.querySelector('.close').addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('productModal');
        if (e.target === modal) closeModal();
    });
}

// ==================== PRODUCTS ====================
async function loadProducts() {
    try {
        const response = await fetch(`${API_BASE}/products/?limit=20`);
        if (!response.ok) throw new Error(`Products request failed: ${response.status}`);
        const products = await response.json();
        allProducts = products;
        displayProducts(allProducts, 'productsGrid');
    } catch (error) {
        console.error('Error loading products:', error);
        document.getElementById('productsGrid').innerHTML = emptyState('Failed to load products from the API.');
        showError('Failed to load products');
    }
}

async function loadRecommendations() {
    try {
        const response = await fetch(`${API_BASE}/recommendations/personalized?user_id=${userId}&limit=6`);
        const recommendations = await response.json();
        if (recommendations && recommendations.length > 0) {
            displayRecommendations(recommendations, 'recommendationsGrid');
        } else {
            document.getElementById('recommendationsGrid').innerHTML = emptyState('Browse products to build recommendations.');
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
        // Fallback to trending
        loadTrendingProducts();
    }
}

async function loadTrendingProducts() {
    try {
        const response = await fetch(`${API_BASE}/recommendations/trending?limit=6`);
        const trending = await response.json();
        displayRecommendations(trending, 'trendingGrid');
    } catch (error) {
        console.error('Error loading trending products:', error);
    }
}

function handleProductClick(event) {
    const addButton = event.target.closest('[data-add-id]');
    if (addButton) {
        event.stopPropagation();
        addToCartById(Number(addButton.dataset.addId));
        return;
    }

    const productCard = event.target.closest('[data-product-id]');
    if (productCard) {
        openProductModal(Number(productCard.dataset.productId));
    }
}

function formatPrice(price) {
    return `$${Number(price || 0).toFixed(2)}`;
}

function imageUrl(value) {
    return value || 'https://via.placeholder.com/300x240?text=No+Image';
}

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (char) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[char]));
}

function emptyState(message) {
    return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function displayProducts(products, gridId) {
    const grid = document.getElementById(gridId);
    if (!products || products.length === 0) {
        grid.innerHTML = emptyState('No products found');
        return;
    }

    grid.innerHTML = products.map(product => `
        <article class="product-card" data-product-id="${product.id}">
            <div class="product-media">
                <img src="${imageUrl(product.image_url)}" alt="${escapeHtml(product.name)}" class="product-image" loading="lazy">
            </div>
            <div class="product-info">
                <h3 class="product-name">${escapeHtml(product.name)}</h3>
                <div class="product-rating">
                    <span class="stars">${renderStars(product.rating || 0)}</span>
                    <span>(${product.rating || 0})</span>
                </div>
                <p class="product-description">${escapeHtml(product.description || '')}</p>
                <div class="product-price">${formatPrice(product.price)}</div>
                <div class="product-actions">
                    <button class="btn-view">View Details</button>
                    <button class="btn-cart" data-add-id="${product.id}" aria-label="Add ${escapeHtml(product.name)} to cart">
                        <i class="fas fa-cart-plus"></i>
                    </button>
                </div>
            </div>
        </article>
    `).join('');
}

function displayRecommendations(recommendations, gridId) {
    const grid = document.getElementById(gridId);
    if (!recommendations || recommendations.length === 0) {
        grid.innerHTML = emptyState('No recommendations available yet');
        return;
    }

    grid.innerHTML = recommendations.map(rec => `
        <article class="product-card" data-product-id="${rec.id || rec.product_id}">
            <div class="product-media">
                <img src="${imageUrl(rec.image_url)}" alt="${escapeHtml(rec.name)}" class="product-image" loading="lazy">
                <div class="product-badge ${rec.reason?.includes('Trending') ? 'warning' : ''}">${escapeHtml(rec.reason || 'Recommended')}</div>
            </div>
            <div class="product-info">
                <h3 class="product-name">${escapeHtml(rec.name)}</h3>
                <div class="product-rating">
                    <span class="stars">${renderStars(rec.rating || 0)}</span>
                    <span>(${rec.rating || 0})</span>
                </div>
                <div class="product-price">${formatPrice(rec.price)}</div>
                ${rec.confidence ? `<div class="product-confidence">Confidence: ${(rec.confidence * 100).toFixed(0)}%</div>` : ''}
                <div class="product-actions">
                    <button class="btn-view">View Details</button>
                    <button class="btn-cart" data-add-id="${rec.id || rec.product_id}" aria-label="Add ${escapeHtml(rec.name)} to cart">
                        <i class="fas fa-cart-plus"></i>
                    </button>
                </div>
            </div>
        </article>
    `).join('');
}

function renderStars(rating) {
    const fullStars = Math.floor(rating);
    const hasHalf = rating % 1 >= 0.5;
    let stars = '★'.repeat(fullStars);
    if (hasHalf) stars += '½';
    stars += '☆'.repeat(5 - Math.ceil(rating));
    return stars;
}

// ==================== MODAL ====================
async function openProductModal(productId) {
    try {
        const response = await fetch(`${API_BASE}/products/${productId}`);
        if (!response.ok) throw new Error(`Product request failed: ${response.status}`);
        const product = await response.json();
        currentProduct = product;

        document.getElementById('modalTitle').textContent = product.name;
        document.getElementById('modalImage').src = imageUrl(product.image_url);
        document.getElementById('modalDescription').textContent = product.description || 'No description available';
        document.getElementById('modalPrice').textContent = formatPrice(product.price);
        document.getElementById('modalRating').textContent = renderStars(product.rating || 0);
        document.getElementById('modalRatingText').textContent = `${product.rating || 0} / 5`;
        document.getElementById('quantity').value = 1;
        document.getElementById('similarProducts').innerHTML = '';

        // Load similar products
        loadSimilarProducts(productId);

        // Record view interaction
        recordInteraction(productId, 'view');

        // Show modal
        document.getElementById('productModal').classList.add('active');
    } catch (error) {
        console.error('Error loading product:', error);
        showError('Failed to load product details');
    }
}

async function loadSimilarProducts(productId) {
    try {
        const response = await fetch(`${API_BASE}/recommendations/similar/${productId}?limit=4`);
        const similar = await response.json();

        if (similar && similar.length > 0) {
            const html = `
                <h4>Similar Products</h4>
                <div class="similar-items">
                    ${similar.map(item => `
                        <div class="similar-item" onclick="openProductModal(${item.id})">
                            <img src="${imageUrl(item.image_url)}" alt="${escapeHtml(item.name)}">
                            <div class="similar-item-name">${escapeHtml(item.name)}</div>
                            <div class="similar-item-price">${formatPrice(item.price)}</div>
                        </div>
                    `).join('')}
                </div>
            `;
            document.getElementById('similarProducts').innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading similar products:', error);
    }
}

function closeModal() {
    document.getElementById('productModal').classList.remove('active');
}

// ==================== CART ====================
function openCart() {
    document.getElementById('cartSidebar').classList.add('active');
    updateCartDisplay();
}

function closeCart() {
    document.getElementById('cartSidebar').classList.remove('active');
}

function addToCartById(productId) {
    const product = allProducts.find(item => item.id === productId) || currentProduct;
    if (!product || product.id !== productId) {
        showError('Product is not ready yet');
        return;
    }
    addToCartQuick(product.id, product.name, product.price, product.image_url);
}

function addToCartQuick(productId, name, price, image, quantity = 1) {
    const existingItem = cart.find(item => item.id === productId);
    
    if (existingItem) {
        existingItem.quantity += quantity;
    } else {
        cart.push({
            id: productId,
            name,
            price,
            image,
            quantity
        });
    }

    saveCart();
    updateCartCount();
    showNotification(`${name} added to cart!`);
    recordInteraction(productId, 'add_to_cart');
}

function addToCart() {
    if (!currentProduct) return;
    
    const quantity = parseInt(document.getElementById('quantity').value);
    addToCartQuick(currentProduct.id, currentProduct.name, currentProduct.price, currentProduct.image_url, quantity);
    
    closeModal();
}

function updateCartDisplay() {
    const cartItemsContainer = document.getElementById('cartItems');
    
    if (cart.length === 0) {
        cartItemsContainer.innerHTML = '<div class="empty-cart"><p>Your cart is empty</p></div>';
        document.getElementById('cartTotal').textContent = '$0.00';
        return;
    }

    let total = 0;
    cartItemsContainer.innerHTML = cart.map((item, index) => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        return `
            <div class="cart-item">
                <img src="${imageUrl(item.image)}" alt="${escapeHtml(item.name)}" class="cart-item-image">
                <div class="cart-item-content">
                    <div class="cart-item-name">${escapeHtml(item.name)}</div>
                    <div class="cart-item-price">${formatPrice(item.price)}</div>
                    <div class="cart-item-quantity">
                        <button onclick="updateQuantity(${index}, -1)">-</button>
                        <span>${item.quantity}</span>
                        <button onclick="updateQuantity(${index}, 1)">+</button>
                    </div>
                    <button class="cart-item-remove" onclick="removeFromCart(${index})">Remove</button>
                </div>
            </div>
        `;
    }).join('');

    document.getElementById('cartTotal').textContent = `$${total.toFixed(2)}`;
}

function updateQuantity(index, change) {
    cart[index].quantity += change;
    if (cart[index].quantity <= 0) {
        cart.splice(index, 1);
    }
    saveCart();
    updateCartDisplay();
    updateCartCount();
}

function removeFromCart(index) {
    cart.splice(index, 1);
    saveCart();
    updateCartDisplay();
    updateCartCount();
}

function updateCartCount() {
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    document.getElementById('cartCount').textContent = count;
}

function saveCart() {
    localStorage.setItem('cart', JSON.stringify(cart));
}

function checkout() {
    if (cart.length === 0) {
        showError('Cart is empty');
        return;
    }
    
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    showNotification(`Order placed! Total: $${total.toFixed(2)}`);
    
    // Record purchase interactions
    cart.forEach(item => {
        recordInteraction(item.id, 'purchase');
    });
    
    cart = [];
    saveCart();
    updateCartCount();
    updateCartDisplay();
    closeCart();
}

// ==================== INTERACTIONS ====================
async function recordInteraction(productId, interactionType, rating = null) {
    try {
        await fetch(`${API_BASE}/recommendations/record-interaction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                product_id: productId,
                interaction_type: interactionType,
                rating: rating
            })
        });
    } catch (error) {
        console.error('Error recording interaction:', error);
    }
}

// ==================== FILTERING & SORTING ====================
function filterProducts() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const filtered = allProducts.filter(p => 
        p.name.toLowerCase().includes(searchTerm) || 
        (p.description && p.description.toLowerCase().includes(searchTerm))
    );
    displayProducts(filtered, 'productsGrid');
}

function sortProducts() {
    const sortType = document.getElementById('sortSelect').value;
    let sorted = [...allProducts];

    switch(sortType) {
        case 'price-low':
            sorted.sort((a, b) => a.price - b.price);
            break;
        case 'price-high':
            sorted.sort((a, b) => b.price - a.price);
            break;
        case 'rating':
            sorted.sort((a, b) => (b.rating || 0) - (a.rating || 0));
            break;
        default:
            sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }

    displayProducts(sorted, 'productsGrid');
}

function scrollToProducts() {
    document.getElementById('products').scrollIntoView({ behavior: 'smooth' });
}

// ==================== QUANTITY CONTROLS ====================
function increaseQty() {
    const qty = document.getElementById('quantity');
    qty.value = parseInt(qty.value) + 1;
}

function decreaseQty() {
    const qty = document.getElementById('quantity');
    if (parseInt(qty.value) > 1) {
        qty.value = parseInt(qty.value) - 1;
    }
}

// ==================== THEME ====================
function toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateThemeIcon();
}

function loadThemePreference() {
    const theme = localStorage.getItem('theme') || 'light';
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    }
    updateThemeIcon();
}

function updateThemeIcon() {
    const icon = document.getElementById('themeToggle').querySelector('i');
    const isDark = document.body.classList.contains('dark-mode');
    icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
}

// ==================== NOTIFICATIONS ====================
function showNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function showError(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ef4444;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
