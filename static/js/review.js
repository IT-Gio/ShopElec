// ---------------- reviews.js ----------------

// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", () => {
    const textarea = document.getElementById("review-comment");
    if (!textarea) return; // Exit if the textarea doesn't exist

    // === Character limit ===
    const maxChars = 300; // Match your Django model's max_length

    // Create and style a counter element
    const counter = document.createElement("p");
    counter.id = "char-counter";
    counter.textContent = `0 / ${maxChars}`;
    counter.style.fontSize = "0.9rem";
    counter.style.color = "#666";
    counter.style.textAlign = "right";
    counter.style.marginTop = "-25px";
    counter.style.marginRight = "10px";

    // Insert it right below the textarea
    textarea.parentNode.appendChild(counter);

    // Listen for typing
    textarea.addEventListener("input", () => {
        const len = textarea.value.length;

        // Prevent typing past the limit
        if (len > maxChars) {
            textarea.value = textarea.value.slice(0, maxChars);
        }

        // Update counter display
        counter.textContent = `${textarea.value.length} / ${maxChars}`;

        // Optional: color change when near the limit
        if (len > maxChars * 0.9) {
            counter.style.color = "#d33";
        } else {
            counter.style.color = "#666";
        }
    });
});

