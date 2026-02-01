// 1. DATA & STATE
// const products = [
//     { id: "serums", name: "Hydrating Serum", category: "Serum (Hydrating)", description: "Replenish and lock in moisture.", price: "$35", image: "https://pamojaskincare.com/cdn/shop/files/STEP_2_REPLENISH_HYDRATING_SERUM_PAMOJA_ULTIMATE_RITUAL_1080x.jpg?v=1757400019" },
//     { id: "cleansers", name: "Vitamin C Cleanser", category: "Cleanser (Vitamin C)", description: "Brighten and refresh your skin.", price: "$28", image: "https://id-test-11.slatic.net/p/ff70fe3768512bbbb2a07a81f72b4421.jpg" },
//     { id: "moisturizers", name: "Night Cream", category: "Moisturizer (Night)", description: "Repair and rejuvenate overnight.", price: "$42", image: "https://static.independent.co.uk/2025/01/08/12/Anti-ageing-night-cream-hero-indybest.jpg?width=1200&height=1200&fit=crop" },
//     { id: "treatment_hero", name: "Mighty Patch Original", category: "Treatment", description: "Hydrocolloid patches to absorb oil and flatten.", price: "$13.00", image: "https://m.media-amazon.com/images/I/61hG5XYbHsL._UF1000,1000_QL80_.jpg" },
//     { id: "serum_lrp_ha", name: "Hyalu B5 Pure Hyaluronic", category: "Serum (Hyaluronic Acid)", description: "Plumps and hydrates the skin deeply.", price: "$30.00", image: "https://cosmetis.com/media/catalog/product/s/u/suractivatedserum4.jpg" },
//     { id: "cleanser_niacinamide", name: "Niacinamide Cleanser", category: "Cleanser (Niacinamide)", description: "Control oil and minimize pores.", price: "$25.00", image: "https://www.dermstore.com/blog/wp-content/uploads/2020/06/Niacinamide-Cleanser-Dermstore.jpg" },
//     { id: "moisturizer_spf", name: "Daily Moisturizer SPF 30", category: "Moisturizer (SPF)", description: "Hydrate and protect from UV rays.", price: "$38.00", image: "https://www.paulaschoice.com/on/demandware.static/-/Sites-PCUS-Library/default/dw5b6e1f9c6/images/product-images/pc/pc_resist_super_light_spf_30_moisturizer_1.jpg" }
// ];
let cart = JSON.parse(localStorage.getItem('cart')) || [];
// 2. DOM ELEMENTS
const productGrid = document.getElementById('product-grid');
const cartCountEl = document.getElementById('cart-count');
const cartModal = document.getElementById('cart-modal');
const qrModal = document.getElementById('qr-modal');
const cartItemsContainer = document.getElementById('cart-items');
const totalAmountEl = document.getElementById('cart-total-amount');
const payTotalEl = document.getElementById('pay-total');
const checkoutBtn = document.querySelector('.pay-now-btn');


function createProductCards() {
    if (!productGrid) return;
    productGrid.innerHTML = '';

    products.forEach((product, index) => {
        const card = document.createElement('div');
        card.className = 'product-card';
        
        // CRITICAL: The filter logic depends on this attribute
        card.setAttribute('data-category', product.category); 
        
        card.setAttribute('data-aos', 'fade-up');
        card.setAttribute('data-aos-delay', (index % 4) * 100);

        card.innerHTML = `
            <div class="product-img">
                <img src="${product.image}" alt="${product.name}">
            </div>
            <h3>${product.name}</h3>
            <p>${product.description}</p>
            <span class="price">${product.price}</span>
            <button class="add-to-cart" onclick="addToCart('${product.id}')">Add to Cart</button>

        `;
        productGrid.appendChild(card);
    });
}
// 4. CART CORE FUNCTIONS
function addToCart(id, name, price, image) {
    // 1. Create product object
    const product = {
        id: id,
        name: name,
        price: parseFloat(price),
        image: image,
        quantity: 1
    };

    // 2. Check if product already in cart
    const existingItem = cart.find(item => item.id === id);

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push(product);
    }

    // 3. Save and Update
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartUI();
    
    // Optional: Show a success message
    alert("បន្ថែមទៅក្នុងកន្ត្រកបានជោគជ័យ!"); 
}
window.removeFromCart = (index) => {
    // 1. Remove the item from the array
    cart.splice(index, 1);
    
    // 2. Save the updated cart to localStorage
    localStorage.setItem('cart', JSON.stringify(cart));
    
    // 3. Refresh the UI to show the changes immediately
    updateCartUI();
};

function updateCartUI() {
    // 1. Correct the ID names to match your HTML exactly
    const cartCountElement = document.getElementById('cart-count'); 
    const cartItemsElement = document.getElementById('cart-items'); // Changed from 'cart-items-list'
    const totalElement = document.getElementById('cart-total-amount'); // Changed from 'cart-total'

    // Update the red badge number (if you have one in your nav)
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    if(cartCountElement) cartCountElement.innerText = totalItems;

    // Clear and rebuild the modal list
    if(cartItemsElement) {
        cartItemsElement.innerHTML = '';
        let totalPrice = 0;

        if (cart.length === 0) {
            cartItemsElement.innerHTML = '<p style="text-align:center; padding:20px;">កន្ត្រករបស់អ្នកទទេ</p>';
        } else {
            cart.forEach((item, index) => {
                totalPrice += item.price * item.quantity;
                cartItemsElement.innerHTML += `
                    <div class="cart-item" style="display:flex; align-items:center; gap:15px; margin-bottom:15px; border-bottom:1px solid #eee; padding-bottom:10px;">
                        <img src="/static/image/products/${item.image}" style="width:60px; height:60px; object-fit:cover; border-radius:5px;">
                        <div style="flex-grow:1;">
                            <p style="margin:0; font-weight:600;">${item.name}</p>
                            <p style="margin:0; color:#6a0dad;">${item.quantity} x $${item.price.toFixed(2)}</p>
                        </div>
                        <button onclick="removeFromCart(${index})" style="background:none; border:none; color:red; cursor:pointer;">&times;</button>
                    </div>
                `;
            });
        }
        
        // Update the total amount display
        if(totalElement) totalElement.innerText = `$${totalPrice.toFixed(2)}`;
    }
}
// Add this at the bottom of your Style-js.js file
document.addEventListener('DOMContentLoaded', () => {
    updateCartUI();
});
// Run this on page load to show existing items
document.addEventListener('DOMContentLoaded', updateCartUI);

function renderCartModal() {
    if (!cartItemsContainer) return;
    cartItemsContainer.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        cartItemsContainer.innerHTML = '<p style="text-align:center; padding:20px;">Your cart is empty.</p>';
    } else {
        cart.forEach((item, index) => {
            // Ensure price is treated as a number for calculation
            const itemPrice = typeof item.price === 'string' ? 
                              parseFloat(item.price.replace('$', '')) : item.price;
            total += itemPrice * (item.quantity || 1);

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

    // Update the total display in the modal
    if (totalAmountEl) totalAmountEl.textContent = `$${total.toFixed(2)}`;
}

// Separate Checkout Logic to keep code clean
if (checkoutBtn) {
    checkoutBtn.onclick = () => {
        if (cart.length === 0) return alert("កន្ត្រករបស់អ្នកទទេ! Your cart is empty.");

        // Sync the total price to the payment (QR) modal
        if (payTotalEl && totalAmountEl) {
            payTotalEl.textContent = totalAmountEl.textContent;
        }

        // Send the Order to the Backend (MySQL)
        fetch('/place-order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: cart })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Success: Clear storage and switch modals
                localStorage.removeItem('cart');
                cart = []; 
                updateCartUI(); // Updates the nav badge
                
                if (cartModal) cartModal.classList.remove('visible');
                if (qrModal) qrModal.classList.add('visible');
            } else {
                alert("Error placing order: " + data.message);
            }
        });
    };
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

products.forEach((product, index) => {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.setAttribute('data-category', product.category); // CRITICAL for filtering
    card.setAttribute('data-aos', 'fade-up');
    
    card.innerHTML = `
        <div class="product-img">
            <img src="${product.image}" alt="${product.name}">
        </div>
        <h3>${product.name}</h3>
        <p>${product.description}</p>
        <span class="price">${product.price}</span>
        <button class="add-to-cart" onclick="addToCart('${product.id}')">Add to Cart</button>
    `;
    productGrid.appendChild(card);
});
/**
 * Filters the product cards based on both search text and category selection.
 */
window.filterProducts = () => {
    // 1. Get current values from both controls
    const searchInput = document.getElementById('productSearch').value.toLowerCase();
    const categorySelect = document.getElementById('category-filter').value.toLowerCase();
    
    // 2. Select all product cards generated by createProductCards()
    const cards = document.querySelectorAll('.product-card');

    cards.forEach(card => {
        // 3. Extract card details
        const name = card.querySelector('h3').innerText.toLowerCase();
        const categoryAttr = card.getAttribute('data-category').toLowerCase();

        // 4. Run dual-check logic
        const matchesSearch = name.includes(searchInput);
        
        // Match if 'all' is selected OR if the card's category contains the search string
        const matchesCategory = (categorySelect === 'all' || categoryAttr.includes(categorySelect));

        // 5. Apply visibility based on BOTH conditions
        if (matchesSearch && matchesCategory) {
            card.style.display = "flex"; // Restores Mighty Patch layout
        } else {
            card.style.display = "none";
        }
    });
};
document.getElementById('checkout-btn').addEventListener('click', function() {
    if (cart.length === 0) {
        alert("កន្ត្រករបស់អ្នកទទេ!");
        return;
    }

    // Send the cart data to Flask
    fetch('/place-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ items: cart })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            localStorage.removeItem('cart'); // Clear cart on success
            window.location.href = `/order/${data.order_id}`; // Redirect to details
        } else {
            alert("Error: " + data.message);
        }
    });
});
/**
 * Validates and handles the registration form submission.
 */
function handleRegister(event) {
    event.preventDefault();

    const name = document.getElementById('reg-name').value;
    const email = document.getElementById('reg-email').value;
    const pass = document.getElementById('reg-password').value;
    const confirmPass = document.getElementById('reg-confirm').value;

    // Basic password match check
    if (pass !== confirmPass) {
        return alert("Passwords do not match!");
    }

    if (pass.length < 8) {
        return alert("Password must be at least 8 characters long.");
    }

    console.log("Registering User:", { name, email });
    alert("Registration successful! Please login.");
    window.location.href = "/login"; // Redirect after success
}

// Initialize
document.addEventListener('DOMContentLoaded', createProductCards);