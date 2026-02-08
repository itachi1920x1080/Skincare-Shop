// ១. ការប្រកាសអថេរសកល និងការចាប់យក DOM Elements
let cart = JSON.parse(localStorage.getItem('cart')) || [];
const productGrid = document.getElementById('product-grid');
const cartModal = document.getElementById('cart-modal');
const qrModal = document.getElementById('qr-modal');
const cartItemsContainer = document.getElementById('cart-items');
const totalAmountEl = document.getElementById('cart-total-amount');
const payTotalEl = document.getElementById('pay-total');
const checkoutBtn = document.getElementById('checkout-btn');

// ២. មុខងារបន្ថែមទៅកន្ត្រក (Global Scope)
window.addToCart = function(id, name, price, image) {
    const product = {
        id: id,
        name: name,
        price: parseFloat(price),
        image: image,
        quantity: 1
    };

    const existingItem = cart.find(item => item.id === id);
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push(product);
    }

    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartUI();
    showFlashMessage(`${name} បន្ថែមជោគជ័យ!`, "success");
};

// ៣. មុខងារលុបទំនិញ និង Update UI
window.removeFromCart = function(index) {
    cart.splice(index, 1);
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartUI();
};

function updateCartUI() {
    const cartCountEl = document.getElementById('cart-count');
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    if (cartCountEl) cartCountEl.innerText = totalItems;
    
    // បើ Modal កំពុងបើក ត្រូវ Update វាដែរ
    if (cartModal && cartModal.classList.contains('visible')) renderCartModal();
}

// ៤. មុខងារបង្ហាញផ្ទាំងកន្ត្រក (Render Modal)
function renderCartModal() {
    if (!cartItemsContainer) return;
    cartItemsContainer.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        cartItemsContainer.innerHTML = '<p style="text-align:center; padding:20px;">កន្ត្រករបស់អ្នកទទេ</p>';
    } else {
        cart.forEach((item, index) => {
            const itemPrice = typeof item.price === 'string' ? parseFloat(item.price.replace('$', '')) : item.price;
            total += itemPrice * item.quantity;

            const div = document.createElement('div');
            div.className = 'cart-item';
            div.style.cssText = "display:flex; align-items:center; gap:10px; margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;";
            div.innerHTML = `
                <img src="/static/image/products/${item.image}" width="50" style="border-radius: 5px; height:50px; object-fit:cover;">
                <div style="flex-grow: 1;">
                    <p style="margin: 0; font-weight: bold; font-size:0.9rem;">${item.name}</p>
                    <p style="margin: 0; font-size:0.8rem;">${item.quantity} x $${itemPrice.toFixed(2)}</p>
                </div>
                <span class="remove-btn" style="cursor: pointer; color: #d1787c; font-weight:bold; font-size:1.2rem;" onclick="removeFromCart(${index})">&times;</span>
            `;
            cartItemsContainer.appendChild(div);
        });
    }
    if (totalAmountEl) totalAmountEl.textContent = `$${total.toFixed(2)}`;
}

// ៥. មុខងារស្វែងរក និង Filter ផលិតផល (Global Function)
window.filterProducts = () => {
    const searchInput = document.getElementById('productSearch');
    const categoryFilter = document.getElementById('category-filter');
    if (!searchInput || !categoryFilter) return;

    const searchValue = searchInput.value.toLowerCase().trim();
    const categoryValue = categoryFilter.value.toLowerCase();
    const cards = document.querySelectorAll('.product-card');
    let visibleCount = 0;

    cards.forEach(card => {
        const nameEl = card.querySelector('.p-name');
        const name = nameEl ? nameEl.innerText.toLowerCase() : "";
        const categoryAttr = (card.getAttribute('data-category') || "").toLowerCase().trim().replace(/\s+/g, '-');

        const matchesSearch = name.includes(searchValue);
        const matchesCategory = (categoryValue === 'all' || categoryAttr === categoryValue);

        if (matchesSearch && matchesCategory) {
            card.style.display = "flex"; 
            visibleCount++;
        } else {
            card.style.display = "none";
        }
    });

    const noResultsMsg = document.querySelector('.no-products');
    if (noResultsMsg) noResultsMsg.style.display = (visibleCount === 0) ? "block" : "none";
};

// ៦. មុខងាររៀបលំដាប់តាមតម្លៃ (Global Function)
window.sortProducts = () => {
    const grid = document.getElementById('product-grid');
    const sortValue = document.getElementById('price-sort').value;
    if (!grid || sortValue === "default") return;

    const cards = Array.from(grid.querySelectorAll('.product-card'));
    cards.sort((a, b) => {
        const priceA = parseFloat(a.querySelector('.p-price').innerText.replace(/[^0-9.]/g, ''));
        const priceB = parseFloat(b.querySelector('.p-price').innerText.replace(/[^0-9.]/g, ''));
        return sortValue === 'low-high' ? priceA - priceB : priceB - priceA;
    });
    cards.forEach(card => grid.appendChild(card));
};

// ៧. មុខងារ Modal Toggles & Checkout
window.toggleCart = () => {
    if (cartModal) {
        cartModal.classList.toggle('visible');
        if (cartModal.classList.contains('visible')) renderCartModal();
    }
};

window.toggleQrModal = () => {
    if (qrModal) qrModal.classList.toggle('visible');
};
if (checkoutBtn) {
    checkoutBtn.onclick = () => {
        if (cart.length === 0) return alert("កន្ត្រករបស់អ្នកទទេ!");

        fetch('/place-order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: cart })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // ✅ ជំហានទី ១៖ ចម្លងតម្លៃសរុបទៅផ្ទាំង QR ជាមុនសិន
                if (payTotalEl && totalAmountEl) {
                    payTotalEl.textContent = totalAmountEl.textContent;
                }

                // ✅ ជំហានទី ២៖ ទើបសម្អាតកន្ត្រកតាមក្រោយ
                localStorage.removeItem('cart');
                cart = [];
                updateCartUI(); 
                
                // ✅ ជំហានទី ៣៖ ប្តូរផ្ទាំង Modal
                if (cartModal) cartModal.classList.remove('visible');
                if (qrModal) qrModal.classList.add('visible');
            } else {
                alert("Error: " + data.message);
            }
        })
        .catch(err => console.error("Checkout Error:", err));
    };
}
// ៨. មុខងារជំនួយ (Flash Message)
function showFlashMessage(message, category) {
    const container = document.querySelector('.flash-container');
    if (!container) return;
    const flashDiv = document.createElement('div');
    flashDiv.className = `flash-message flash-${category}`;
    flashDiv.innerHTML = `<span><i class="fas fa-check-circle"></i> ${message}</span>`;
    container.appendChild(flashDiv);
    setTimeout(() => {
        flashDiv.style.opacity = '0';
        setTimeout(() => flashDiv.remove(), 500);
    }, 4000);
}

// ៩. Event Listeners ពេល Load ទំព័រ
window.onclick = (event) => {
    if (event.target == cartModal) cartModal.classList.remove('visible');
    if (event.target == qrModal) qrModal.classList.remove('visible');
};

document.addEventListener('DOMContentLoaded', () => {
    updateCartUI();
    const cartIconBtn = document.getElementById('cart-btn');
    if (cartIconBtn) cartIconBtn.onclick = toggleCart;
    if (typeof window.filterProducts === "function") window.filterProducts();
});