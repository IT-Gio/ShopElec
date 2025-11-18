// ---------------- CSRF HELPER ----------------
function getCSRFToken() {
    const name = 'csrftoken=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookies = decodedCookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name)) {
            return cookie.substring(name.length, cookie.length);
        }
    }
    return '';
}

// ---------------- ADD TO CART (SECURE) ----------------
document.addEventListener('click', async function (event) {
    const toCartButton = event.target.closest('.toCart');
    if (!toCartButton) return;

    event.preventDefault(); // stop any unwanted navigation

    const productId = toCartButton.dataset.product
        ? JSON.parse(toCartButton.dataset.product).id
        : null;
    if (!productId) return;

    try {
        const response = await fetch('/api/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({
                item_id: productId,
                quantity: 1,
            }),
        });

        if (response.ok) {
            showCartMessage("Added to cart!");
        } else {
            const data = await response.json();
            showCartMessage(data.error || "Failed to add to cart", true);
        }
    } catch (error) {
        showCartMessage("Network error while adding to cart", true);
    }
});

// ---------------- SMALL CART MESSAGE POPUP ----------------
function showCartMessage(text, isError = false) {
    const msg = document.createElement("div");
    msg.className = "message";
    msg.textContent = text;
    msg.classList.add(isError ? "error" : "success");
    document.body.appendChild(msg);

    setTimeout(() => {
        msg.style.opacity = "0";
        msg.style.transform = "translateY(20px)";
        setTimeout(() => msg.remove(), 500);
    }, 2000);
}

// ---------------- VIEW MORE BUTTONS ----------------
document.addEventListener("click", e => {
    const btn = e.target.closest(".cardButton");
    if (!btn) return;

    // Only handle product view buttons, not sidebar or pagination links
    if (btn.classList.contains("toCart")) return;

    e.preventDefault();
    const productDiv = btn.closest(".product");
    if (productDiv) {
        const link = productDiv.querySelector(".cardName a");
        if (link) {
            window.location.href = link.href;
        }
    }
});
