// 1. DATA & STATE
const products = [
    { id: "p1", name: "Hydrating Serum", price: "$35.00", image: "https://pamojaskincare.com/cdn/shop/files/STEP_2_REPLENISH_HYDRATING_SERUM_PAMOJA_ULTIMATE_RITUAL_1080x.jpg?v=1757400019", description: "Replenish and lock in moisture." },
    { id: "p2", name: "Vitamin C Cleanser", price: "$28.00", image: "https://id-test-11.slatic.net/p/ff70fe3768512bbbb2a07a81f72b4421.jpg", description: "Brighten and refresh your skin." },
    { id: "p3", name: "Night Cream", price: "$42.00", image: "https://static.independent.co.uk/2025/01/08/12/Anti-ageing-night-cream-hero-indybest.jpg?width=1200&height=1200&fit=crop", description: "Repair and rejuvenate overnight." }
];

let cart = [];

// 2. DOM ELEMENTS
const productGrid = document.getElementById('product-grid');
const cartCountEl = document.getElementById('cart-count');
const cartModal = document.getElementById('cart-modal');
const qrModal = document.getElementById('qr-modal');
const cartItemsContainer = document.getElementById('cart-items');
const totalAmountEl = document.getElementById('cart-total-amount');
const payTotalEl = document.getElementById('pay-total');
const checkoutBtn = document.querySelector('.pay-now-btn'); // Consolidated selector

// 3. PRODUCT RENDERING
function createProductCards() {
    if (!productGrid) return;
    productGrid.innerHTML = '';

    products.forEach((product, index) => {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.setAttribute('data-aos', 'fade-up');
        card.setAttribute('data-aos-delay', (index % 4) * 100);

        card.innerHTML = `
            <img src="${product.image}" alt="${product.name}">
            <h3>${product.name}</h3>
            <p>${product.description}</p>
            <span class="price">${product.price}</span>
            <button class="add-to-cart" onclick="addToCart('${product.id}')">Add to Cart</button>
        `;
        productGrid.appendChild(card);
    });
}

// 4. CART CORE FUNCTIONS
window.addToCart = (id) => {
    const item = products.find(p => p.id === id);
    if (item) {
        cart.push(item);
        updateCartUI();
    }
};

window.removeFromCart = (index) => {
    cart.splice(index, 1);
    updateCartUI();
};

function updateCartUI() {
    if (cartCountEl) cartCountEl.textContent = cart.length;
    renderCartModal();
}

function renderCartModal() {
    if (!cartItemsContainer) return;
    cartItemsContainer.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        cartItemsContainer.innerHTML = '<p style="text-align:center; padding:20px;">Your cart is empty.</p>';
    } else {
        cart.forEach((item, index) => {
            total += parseFloat(item.price.replace('$', ''));
            const div = document.createElement('div');
            div.className = 'cart-item';
            div.style.cssText = "display:flex; align-items:center; gap:10px; margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;";
            div.innerHTML = `
                <img src="${item.image}" width="50" style="border-radius: 5px;">
                <div style="flex-grow: 1;">
                    <p style="margin: 0; font-weight: bold; font-size:0.9rem;">${item.name}</p>
                    <p style="margin: 0; font-size:0.8rem;">${item.price}</p>
                </div>
                <span class="remove-btn" style="cursor: pointer; color: #d1787c; font-weight:bold;" onclick="removeFromCart(${index})">&times;</span>
            `;
            cartItemsContainer.appendChild(div);
        });
    }
    if (totalAmountEl) totalAmountEl.textContent = `$${total.toFixed(2)}`;
}

// 5. MODAL TOGGLES & TRANSITIONS
window.toggleCart = () => {
    if (cartModal) {
        cartModal.classList.toggle('visible');
        if (cartModal.classList.contains('visible')) renderCartModal();
    }
};

window.toggleQrModal = () => {
    if (qrModal) qrModal.classList.toggle('visible');
};

// Transition Logic: Cart -> Bank QR
if (checkoutBtn) {
    checkoutBtn.onclick = () => {
        if (cart.length === 0) return alert("Your cart is empty!");
        
        // Transfer the final total to the payment modal
        if (payTotalEl && totalAmountEl) {
            payTotalEl.textContent = totalAmountEl.textContent;
        }
        
        cartModal.classList.remove('visible'); // Close Cart
        qrModal.classList.add('visible');      // Open QR
    };
}

// Close listeners
const closeCartBtn = document.getElementById('close-cart');
const closeQrBtn = document.getElementById('close-qr');

if (closeCartBtn) closeCartBtn.onclick = () => cartModal.classList.remove('visible');
if (closeQrBtn) closeQrBtn.onclick = () => qrModal.classList.remove('visible');

// Header Cart Button
const headerCartBtn = document.getElementById('cart-btn');
if (headerCartBtn) headerCartBtn.onclick = toggleCart;

// Global Click-to-Close (Outside Modal)
window.onclick = (event) => {
    if (event.target == cartModal) cartModal.classList.remove('visible');
    if (event.target == qrModal) qrModal.classList.remove('visible');
};

// Initialize
document.addEventListener('DOMContentLoaded', createProductCards);