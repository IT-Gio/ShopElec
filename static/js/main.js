// Fetch products from your API
let currentPageUrl = '/api/products/';

function loadProducts(url) {
    fetch(url)
      .then(res => res.json())
      .then(data => {
          const container = document.getElementById('products-container');
          container.innerHTML = '';
          
          data.results.forEach(product => {
              const div = document.createElement('div');
              div.classList.add('product');
              div.setAttribute('data-id', product.id);
              div.setAttribute('data-category', product.category || '');
              div.setAttribute('data-brand', product.brand || '');
              div.setAttribute('data-subCategory', product.subCategory || '');
              div.setAttribute('data-description', product.description || '');
              div.setAttribute('data-stock', product.stock);
              div.setAttribute('data-rating', product.average_rating ?? 0);
              div.innerHTML = `
                ${product.image ? `<img src="${product.image}" class="cardImage">` : ''}
                <div class="hr"></div>
                <h2 class="cardName">${product.name}</h2>
                <p class="cardPrice">${product.price} $</p>
                <div class="hr"></div>
                <p class="cardBrand">${product.brand}</p>
                <p class="cardCategory">${product.category || 'Uncategorized'}</p>
                <p class="cardRate">Rating: ${product.average_rating ?? "?"}/10</p>
                <p class="cardStock">${product.stock > 0 ? `In Stock: ${product.stock}` : '<span style="color:red;">Out of Stock</span>'}</p>
                <div class="cardButtonWrap">
                    <button class="cardButton">View More</button>
                    <button class="toCart" ${product.stock === 0 ? "disabled" : ""}>
                        <i class="fa-solid fa-cart-plus cartIcon"></i>
                    </button>
                </div>
              `;
              container.appendChild(div);
          });

          // Pagination buttons
          document.getElementById('prev-page').disabled = !data.previous;
          document.getElementById('next-page').disabled = !data.next;

          document.getElementById('prev-page').onclick = () => loadProducts(data.previous);
          document.getElementById('next-page').onclick = () => loadProducts(data.next);
      });
}

document.addEventListener('DOMContentLoaded', () => loadProducts(currentPageUrl));

// Mobile burger menu toggle
document.addEventListener("DOMContentLoaded", () => {
    const burger = document.getElementById("burger");
    const navLinks = document.getElementById("nav-links");
    burger.addEventListener("click", () => navLinks.classList.toggle("show"));
});

// Fetch categories
fetch('/api/categories/')
    .then(res => res.json())
    .then(data => {
        const sidebar = document.getElementById("sidebar");
        const categoryList = sidebar.querySelectorAll("ul")[1];
        categoryList.innerHTML = "";

        data.categories.forEach(cat => {
            const li = document.createElement("li");
            const btn = document.createElement("button");
            btn.textContent = cat;
            btn.dataset.category = cat;
            btn.addEventListener("click", () => filterByCategory(cat));
            li.appendChild(btn);
            categoryList.appendChild(li);
        });

        const mobileSelect = document.getElementById("category-select");
        mobileSelect.innerHTML = "<option value=''>All Categories</option>";
        data.categories.forEach(cat => {
            const option = document.createElement("option");
            option.value = cat;
            option.textContent = cat;
            mobileSelect.appendChild(option);
        });
        mobileSelect.addEventListener("change", e => filterByCategory(e.target.value));
    })
    .catch(err => console.error('Error fetching categories:', err));

// Filter products by category
function filterByCategory(category) {
    document.querySelectorAll("#products-container .product").forEach(prod => {
        prod.style.display = !category || prod.dataset.category === category ? "flex" : "none";
    });
}

// Sorting options (for dropdown)
const sortOptions = [
    { value: "price-asc", text: "Price: Low to High" },
    { value: "price-desc", text: "Price: High to Low" },
    { value: "rating", text: "Rating" },
    { value: "newest", text: "Newest" },
];
const sortSelect = document.getElementById("sort-select");
sortOptions.forEach(opt => {
    const option = document.createElement("option");
    option.value = opt.value;
    option.textContent = opt.text;
    sortSelect.appendChild(option);
});

// ---------------- CART LOGIC ----------------
let cart = JSON.parse(localStorage.getItem('cart')) || [];
const cartCountSpan = document.getElementById('cart-count');

function updateCartCount() {
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    if (count > 0) {
        cartCountSpan.style.display = "inline-block";
        cartCountSpan.textContent = count;
    } else {
        cartCountSpan.style.display = "none";
    }
}

// Add to cart with full product info
function addToCart(product) {
    let existing = cart.find(item => item.id == product.id);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({ ...product, quantity: 1 });
    }
    localStorage.setItem("cart", JSON.stringify(cart));
    updateCartCount();
}

// Attach Add to Cart event
document.addEventListener('click', e => {
    const btn = e.target.closest('.toCart');
    if (btn && !btn.disabled) {
        const productDiv = btn.closest('.product');
        const product = {
            id: productDiv.dataset.id,
            name: productDiv.querySelector(".cardName").textContent,
            price: parseFloat(productDiv.querySelector(".cardPrice").textContent),
            image: productDiv.querySelector(".cardImage")?.src || "",
            brand: productDiv.querySelector(".cardBrand").textContent,
            category: productDiv.dataset.category,
            subCategory: productDiv.dataset.subCategory,
            description: productDiv.dataset.description,
            stock: parseInt(productDiv.dataset.stock || 0),
            average_rating: parseFloat(productDiv.dataset.rating || 0)
        };
        addToCart(product);
    }
});

// Update cart on page load
document.addEventListener('DOMContentLoaded', updateCartCount);

// ---------------- VIEW MORE BUTTON ----------------
// Event delegation for dynamically created buttons
document.getElementById("products-container").addEventListener("click", (e) => {
    if (e.target && e.target.classList.contains("cardButton")) {
        const productDiv = e.target.closest('.product');
        const productId = productDiv.dataset.id;
        window.location.href = `/product/${productId}/`;
    }
});
