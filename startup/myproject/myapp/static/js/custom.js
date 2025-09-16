(function () {
    "use strict";

    /** ================================
     * Tiny Slider Initialization
     * ================================ */
    const initTinySlider = () => {
        const sliderEls = document.querySelectorAll(".testimonial-slider");
        if (sliderEls.length > 0) {
            tns({
                container: ".testimonial-slider",
                items: 1,
                axis: "horizontal",
                controlsContainer: "#testimonial-nav",
                swipeAngle: false,
                speed: 700,
                nav: true,
                controls: true,
                autoplay: true,
                autoplayHoverPause: true,
                autoplayTimeout: 3500,
                autoplayButtonOutput: false,
            });
        }
    };

    /** ================================
     * Quantity Plus/Minus Buttons
     * ================================ */
    const initQuantityControls = () => {
        const quantityContainers = document.getElementsByClassName("quantity-container");

        function bindControls(container) {
            const quantityAmount = container.querySelector(".quantity-amount");
            const increaseBtn = container.querySelector(".increase");
            const decreaseBtn = container.querySelector(".decrease");

            increaseBtn.addEventListener("click", () => changeValue(quantityAmount, 1));
            decreaseBtn.addEventListener("click", () => changeValue(quantityAmount, -1));
        }

        function changeValue(input, delta) {
            let value = parseInt(input.value, 10);
            value = isNaN(value) ? 0 : value;
            input.value = Math.max(0, value + delta); // Prevent negative
        }

        Array.from(quantityContainers).forEach(bindControls);
    };

    // Initialize features
    initTinySlider();
    initQuantityControls();
})(); // End IIFE


/** ================================
 * Prize Claim Form Logic
 * ================================ */
document.addEventListener("DOMContentLoaded", () => {
    const shopId = 123; // Ideally dynamic from URL or backend
    const shopLogo = document.getElementById("shop-logo");
    const shopName = document.getElementById("shop-name");
    const form = document.getElementById("coupon-form");
    const resultSection = document.getElementById("result-section");
    const resultAlert = document.getElementById("result-alert");

    /**
     * Fetch wrapper with exponential backoff
     */
    const fetchWithBackoff = async (url, options = {}, retries = 3, delay = 1000) => {
        for (let attempt = 0; attempt < retries; attempt++) {
            try {
                const response = await fetch(url, options);
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return await response.json();
            } catch (error) {
                console.error(`Attempt ${attempt + 1} failed:`, error);
                if (attempt < retries - 1) {
                    await new Promise((res) => setTimeout(res, delay * Math.pow(2, attempt))); // Exponential backoff
                } else {
                    throw error; // Retries exhausted
                }
            }
        }
    };

    /** Load shop details */
    fetchWithBackoff(`/api/shop/${shopId}`)
        .then((data) => {
            shopLogo.src = data.logo_url || "https://placehold.co/40x40/E8E8E8/444?text=Logo";
            shopName.textContent = data.name || "Shop Name";
        })
        .catch((err) => {
            console.error("Shop API error:", err);
            shopName.textContent = "Shop Name (Error)";
        });

    /** Handle coupon form submission */
    form.addEventListener("submit", (event) => {
        event.preventDefault();

        if (!form.checkValidity()) {
            event.stopPropagation();
            form.classList.add("was-validated");
            return;
        }

        const couponCode = document.getElementById("couponCode").value.trim();
        const customerName = document.getElementById("customerName").value.trim();
        const customerContact = document.getElementById("customerContact").value.trim();

        fetchWithBackoff(`/api/check-coupon`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                shop_id: shopId,
                coupon_code: couponCode,
                name: customerName,
                contact: customerContact,
            }),
        })
            .then((data) => {
                resultSection.style.display = "block";

                if (data.winner) {
                    resultAlert.className = "alert alert-success fade show";
                    resultAlert.innerHTML = `🎉 <strong>Congratulations!</strong> You won: ${data.prize_name}`;
                } else {
                    resultAlert.className = "alert alert-danger fade show";
                    resultAlert.innerHTML = `<strong>Better Luck Next Time</strong>`;
                }

                // Redirect after 5 seconds
                setTimeout(() => {
                    window.location.href = `/shop/${shopId}/offers`;
                }, 5000);
            })
            .catch((err) => {
                console.error("Coupon check API error:", err);
                resultSection.style.display = "block";
                resultAlert.className = "alert alert-danger fade show";
                resultAlert.innerHTML = `<strong>An error occurred. Please try again later.</strong>`;
            });
    });
});


/** ================================
 * Prize Game (Box Animation + Modal)
 * ================================ */
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("prizeForm");
    const claimButton = document.getElementById("claimButton");
    const prizeBoxes = document.querySelectorAll(".prize-box");
    const modal = document.getElementById("prizeModal");
    const prizeResultDiv = document.getElementById("prizeResult");
    const closeButton = document.querySelector(".close-button");

    const prizeList = [
        { name: "A free coffee", image: "https://via.placeholder.com/250/0000FF/FFFFFF?text=Coffee" },
        { name: "10% off your next purchase", image: "https://via.placeholder.com/250/FF0000/FFFFFF?text=Discount" },
        { name: "A free product sample", image: "https://via.placeholder.com/250/FFFF00/000000?text=Sample" },
        { name: "Free shipping", image: "https://via.placeholder.com/250/008000/FFFFFF?text=Shipping" },
        { name: "A surprise gift", image: "https://via.placeholder.com/250/800080/FFFFFF?text=Gift" },
        { name: "A coupon for a friend", image: "https://via.placeholder.com/250/FFA500/000000?text=Coupon" },
    ];

    const runAnimation = () => {
        return new Promise((resolve) => {
            let count = 0;
            let currentBoxIndex = 0;

            const interval = setInterval(() => {
                prizeBoxes.forEach((box) => box.classList.remove("highlight"));
                prizeBoxes[currentBoxIndex].classList.add("highlight");

                currentBoxIndex = (currentBoxIndex + 1) % prizeBoxes.length;
                count++;

                if (count > 20) {
                    clearInterval(interval);
                    const winningIndex = Math.floor(Math.random() * prizeList.length);
                    resolve(winningIndex);
                }
            }, 100);
        });
    };

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        claimButton.disabled = true;
        const inputs = form.querySelectorAll("input");
        inputs.forEach((input) => (input.disabled = true));

        // Reset boxes
        prizeBoxes.forEach((box) => {
            box.classList.remove("highlight");
            box.textContent = "?";
        });

        const winningIndex = await runAnimation();

        // Highlight winning box
        prizeBoxes.forEach((box, index) => {
            box.classList.remove("highlight");
            if (index === winningIndex) {
                box.classList.add("highlight");
            }
        });

        const winningPrize = prizeList[winningIndex];
        prizeResultDiv.innerHTML = `
            <h2>🎉 Congratulations!</h2>
            <p>You won: <span class="prize-result-box">${winningPrize.name}</span></p>
            <img src="${winningPrize.image}" alt="${winningPrize.name}" class="prize-image">
        `;

        modal.style.display = "flex";

        claimButton.disabled = false;
        inputs.forEach((input) => (input.disabled = false));
    });

    // Modal close events
    closeButton.addEventListener("click", () => (modal.style.display = "none"));
    window.addEventListener("click", (e) => {
        if (e.target === modal) modal.style.display = "none";
    });
});
