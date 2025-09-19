document.addEventListener("DOMContentLoaded", () => {
    const cartContainer = document.getElementById("cart-container");
    const totalItemsEl = document.getElementById("total-items");
    const totalPriceEl = document.getElementById("total-price");
    const checkoutBtn = document.getElementById("checkout-btn");

    let cart = JSON.parse(localStorage.getItem("cart")) || [];

    function renderCart() {
        cartContainer.innerHTML = "";

        if (cart.length === 0) {
            cartContainer.innerHTML = "<p>Your cart is empty.</p>";
            checkoutBtn.disabled = true;
            totalItemsEl.textContent = "0";
            totalPriceEl.textContent = "0.00";

            localStorage.removeItem("cart");
            return;
        }

        checkoutBtn.disabled = false;

        let totalItems = 0;
        let totalPrice = 0;

        cart.forEach((item, index) => {
            totalItems += item.quantity;
            totalPrice += item.price * item.quantity;

            const div = document.createElement("div");
            div.classList.add("cart-item");
            div.innerHTML = `
                ${item.image ? `<img src="${item.image}" class="cart-item-image">` : ""}
                <h3>${item.name}</h3>
                <p>Brand: ${item.brand}</p>
                <p>Category: ${item.category}</p>
                <p>Price: $${item.price}</p>
                <p>Quantity: <input type="number" value="${item.quantity}" min="1" data-index="${index}" class="qty-input"></p>
                <button class="remove-btn" data-index="${index}">Remove</button>
            `;
            cartContainer.appendChild(div);
        });

        totalItemsEl.textContent = totalItems;
        totalPriceEl.textContent = totalPrice.toFixed(2);

        // Save only if not empty
        localStorage.setItem("cart", JSON.stringify(cart));
    }


    // Handle quantity change
    cartContainer.addEventListener("input", (e) => {
        if (e.target.classList.contains("qty-input")) {
            const index = e.target.dataset.index;
            cart[index].quantity = parseInt(e.target.value);
            renderCart();
        }
    });

    // Handle remove
    cartContainer.addEventListener("click", (e) => {
        if (e.target.classList.contains("remove-btn")) {
            const index = e.target.dataset.index;
            cart.splice(index, 1);
            renderCart();
        }
    });

    // Checkout
    checkoutBtn.addEventListener("click", () => {
        alert("Proceeding to checkout...");
        // TODO: Send cart to Django backend
    });

    renderCart();
});
