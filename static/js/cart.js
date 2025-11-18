document.addEventListener("DOMContentLoaded", () => {
  const cartContainer = document.getElementById("cart-container");
  const totalItemsEl = document.getElementById("total-items");
  const totalPriceEl = document.getElementById("total-price");
  const checkoutBtn = document.getElementById("checkout-btn");
  const paymentPopup = document.getElementById("payment-popup");
  const paymentForm = document.getElementById("payment-form");
  const addressInput = document.getElementById("address");
  const emailInput = document.getElementById("email");
  const cardErrors = document.getElementById("card-errors");
  const closeBtn = document.getElementById("close-payment-popup");
  const cartCountSpan = document.getElementById("cart-count");
  const couponForm = document.getElementById("coupon-form");
  const couponMessage = document.getElementById("coupon-message");

  let cart = [];
  let stripe, cardElementMounted = false, cardElement;
  let isProcessing = false;

  // ---------------- CSRF HELPER ----------------
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

  // ---------------- FETCH CART ----------------
  async function fetchCart() {
    try {
      const resp = await fetch("/api/cart/", {
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        credentials: "include",
      });
      const data = await resp.json();
      cart = data;
      renderCart();
      await fetchDiscountedTotal();
    } catch (err) {
      console.error("Error loading cart:", err);
      cartContainer.innerHTML = "<p>Failed to load cart.</p>";
    }
  }

  // ---------------- FETCH DISCOUNTED TOTAL ----------------
  async function fetchDiscountedTotal() {
    if (!cart.length) return;

    try {
      const resp = await fetch("/orders/create-payment-intent/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        credentials: "include",
        body: JSON.stringify({ cart }),
      });

      const data = await resp.json();

      const subtotalEl = document.getElementById("subtotal-price");
      const discountEl = document.getElementById("discount-amount");
      const totalEl = document.getElementById("total-price");
      const couponEl = document.getElementById("coupon-applied");

      if (!subtotalEl) return;

      subtotalEl.textContent = Number(data.subtotal).toFixed(2);
      discountEl.textContent = Number(data.discount || 0).toFixed(2);
      totalEl.textContent = Number(data.final_total).toFixed(2);
      couponEl.textContent = data.coupon_code ? `Coupon applied: ${data.coupon_code}` : "";

    } catch (err) {
      console.error("Discount fetch failed:", err);
    }
  }

  // ---------------- RENDER CART ----------------
  function renderCart() {
    cartContainer.innerHTML = "";

    if (!cart.length) {
      cartContainer.innerHTML = "<p>Your cart is empty.</p>";
      checkoutBtn.disabled = true;
      totalItemsEl.textContent = "0";
      totalPriceEl.textContent = "0.00";
      updateCartBubble(0);
      return;
    }

    checkoutBtn.disabled = false;

    let totalItems = 0;
    let totalPrice = 0;

    cart.forEach(item => {
      totalItems += item.quantity;
      totalPrice += item.price * item.quantity;

      const div = document.createElement("div");
      div.classList.add("cart-item");
      div.innerHTML = `
        ${item.image ? `<img src="${item.image}" class="cart-item-image">` : ""}
        <h3>${item.name}</h3>
        <p>Brand: ${item.brand || "N/A"}</p>
        <p>Category: ${item.category || "N/A"}</p>
        <p>Price: $${item.price}</p>
        <p>Quantity: <input type="number" value="${item.quantity}" min="1" data-id="${item.id}" class="qty-input"></p>
        <button class="remove-btn" data-id="${item.id}">Remove</button>
      `;
      cartContainer.appendChild(div);
    });

    totalItemsEl.textContent = totalItems;
    totalPriceEl.textContent = totalPrice.toFixed(2);
    updateCartBubble(totalItems);
  }

  // ---------------- CART ICON ----------------
  function updateCartBubble(count) {
    if (!cartCountSpan) return;
    cartCountSpan.textContent = count;
    cartCountSpan.style.display = count > 0 ? "inline-block" : "none";
  }

  // ---------------- DEBOUNCE ----------------
  function debounce(fn, delay) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), delay);
    };
  }

  const debouncedUpdateCart = debounce(async (id, quantity) => {
    try {
      const resp = await fetch("/api/cart/update/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        credentials: "include",
        body: JSON.stringify({ item_id: id, quantity }),
      });

      const data = await resp.json();
      cart = data.cart;
      renderCart();
      await fetchDiscountedTotal();

    } catch (err) {
      console.error("Cart update failed:", err);
    }
  }, 400);

  // ---------------- REMOVE ITEM ----------------
  async function removeFromCart(id) {
    try {
      const resp = await fetch(`/api/cart/remove/${id}/`, {
        method: "DELETE",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        credentials: "include",
      });

      const data = await resp.json();
      cart = data.cart;
      renderCart();
      await fetchDiscountedTotal();
    } catch (err) {
      console.error("Remove failed:", err);
    }
  }

  // ---------------- APPLY COUPON ----------------
  if (couponForm) {
    couponForm.addEventListener("submit", async e => {
      e.preventDefault();

      const formData = new FormData(couponForm);

      await fetch("/orders/apply-coupon/", {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      couponMessage.textContent = "Coupon applied!";
      setTimeout(fetchDiscountedTotal, 250);
    });
  }

  // ---------------- CART EVENTS ----------------
  cartContainer.addEventListener("input", e => {
    if (e.target.classList.contains("qty-input")) {
      const id = e.target.dataset.id;
      const qty = parseInt(e.target.value) || 1;
      debouncedUpdateCart(id, qty);
    }
  });

  cartContainer.addEventListener("click", e => {
    if (e.target.classList.contains("remove-btn")) {
      removeFromCart(e.target.dataset.id);
    }
  });

  // ---------------- PAYMENT POPUP ----------------
  function openPopup() {
    paymentPopup.classList.remove("hidden");
    paymentPopup.style.display = "flex";

    if (!cardElementMounted) {
      stripe = Stripe(checkoutBtn.dataset.stripeKey);
      const elements = stripe.elements();
      cardElement = elements.create("card");
      cardElement.mount("#card-element");
      cardElement.on("change", e => {
        cardErrors.textContent = e.error ? e.error.message : "";
      });
      cardElementMounted = true;
    }
  }

  function closePopup() {
    paymentPopup.classList.add("hidden");
    paymentPopup.style.display = "none";
    paymentForm.reset();
    cardErrors.textContent = "";
  }

  checkoutBtn.addEventListener("click", openPopup);
  closeBtn.addEventListener("click", closePopup);

  // ---------------- PAYMENT HANDLER ----------------
  paymentForm.addEventListener("submit", async e => {
    e.preventDefault();
    if (isProcessing) return;

    isProcessing = true;
    checkoutBtn.disabled = true;
    checkoutBtn.textContent = "Processing...";

    const address = addressInput ? addressInput.value.trim() : "";
    const email = emailInput ? emailInput.value.trim() : "";


    try {
      // 1️⃣ Create PaymentIntent OR detect free order
      const resp = await fetch("/orders/create-payment-intent/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        credentials: "include",
        body: JSON.stringify({ address, email, cart }),
      });

      const data = await resp.json();

      // 🔥 FREE ORDER (skip Stripe entirely)
      if (data.freeOrder) {
        const completeResp = await fetch("/orders/complete-order/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          credentials: "include",
          body: JSON.stringify({
            address,
            email,
            cart,
            paymentIntentId: "FREE_ORDER",
          }),
        });

        const completeData = await completeResp.json();
        if (completeData.success) {
          alert("Order placed successfully (free order)!");
          closePopup();
          cart = [];
          renderCart();
        }
        return;
      }

      // 2️⃣ Stripe payment
      const result = await stripe.confirmCardPayment(data.clientSecret, {
        payment_method: { card: cardElement },
      });

      if (result.error) {
        cardErrors.textContent = result.error.message;
        alert(result.error.message);
        return;
      }

      // 3️⃣ Complete Order
      const completeResp = await fetch("/orders/complete-order/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        credentials: "include",
        body: JSON.stringify({
          address,
          email,
          cart,
          paymentIntentId: result.paymentIntent.id,
        }),
      });

      const completeData = await completeResp.json();
      if (!completeData.success) {
        alert("Order failed.");
        return;
      }

      alert("Payment successful!");
      closePopup();
      cart = [];
      renderCart();

    } catch (err) {
      console.error("Payment error:", err);
      alert("Payment failed.");
    } finally {
      isProcessing = false;
      checkoutBtn.disabled = false;
      checkoutBtn.textContent = "Pay";
    }
  });

  // ---------------- INIT ----------------
  fetchCart();
});
