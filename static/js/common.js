
// Cart state
let cart = [];
const cartCountSpan = document.getElementById('cart-count');

// Helper: Get CSRF token for Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";").map(c => c.trim());
        for (const cookie of cookies) {
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ---------------- CART COUNT ----------------
function updateCartCount() {
    if (!cartCountSpan) return;
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    if (count > 0) {
        cartCountSpan.style.display = "inline-block";
        cartCountSpan.textContent = count;
    } else {
        cartCountSpan.style.display = "none";
    }
}

// ---------------- FETCH CART FROM BACKEND ----------------
async function fetchCart() {
    try {
        const resp = await fetch("/api/cart/", {
            headers: { "X-CSRFToken": getCookie("csrftoken") }
        });
        if (!resp.ok) throw new Error("Failed to load cart");
        cart = await resp.json();
        updateCartCount();
    } catch (err) {
        console.error("Error loading cart:", err);
        cart = [];
        updateCartCount();
    }
}

// ---------------- ADD TO CART ----------------
async function addToCart(product) {
    if (!product.id) {
        console.error("Product ID missing:", product);
        alert("Cannot add product to cart: missing ID.");
        return;
    }

    try {
        const resp = await fetch("/api/cart/add/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({
                item_id: parseInt(product.id),
                quantity: 1 // default quantity
            })
        });

        if (!resp.ok) throw new Error(`Failed to add item to cart (status ${resp.status})`);
        const data = await resp.json();
        cart = data; // assuming backend returns list of cart items
        updateCartCount();
    } catch (err) {
        console.error("Add to cart failed:", err);
        alert("Could not add to cart. Try again.");
    }
}

// ---------------- HANDLE ADD-TO-CART BUTTONS ----------------
document.addEventListener("click", e => {
    const btn = e.target.closest(".toCart");
    if (!btn || btn.disabled) return;

    // Parse JSON from data-product safely
    let product;
    try {
        product = JSON.parse(btn.dataset.product);
    } catch (err) {
        console.error("Failed to parse product data:", err, btn.dataset.product);
        alert("Invalid product data");
        return;
    }

    addToCart(product);
});

// ---------------- INITIALIZE ----------------
document.addEventListener("DOMContentLoaded", fetchCart);


// ---------------- LOGOUT POPUP ----------------
document.addEventListener("DOMContentLoaded", () => {
    const logoutBtn = document.getElementById("logout-btn");
    const logoutPopup = document.getElementById("logout-popup");
    const confirmLogout = document.getElementById("confirm-logout");
    const cancelLogout = document.getElementById("cancel-logout");

    if (!logoutBtn) return; // user not logged in

    // Show popup when clicking Logout
    logoutBtn.addEventListener("click", () => {
        if (logoutPopup) logoutPopup.style.display = "flex";
    });

    // Cancel logout
    if (cancelLogout) {
        cancelLogout.addEventListener("click", () => {
            if (logoutPopup) logoutPopup.style.display = "none";
        });
    }

    // Confirm logout
    if (confirmLogout) {
        confirmLogout.addEventListener("click", () => {
            const url = confirmLogout.dataset.logoutUrl;
            if (url) {
                window.location.href = url;
            } else {
                console.error("Logout URL not found!");
            }
        });
    }
});
