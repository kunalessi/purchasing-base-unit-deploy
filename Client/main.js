document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const loginSection = document.getElementById("login-section");
    const mainContent = document.getElementById("main-content");
    const logoutButton = document.getElementById("logout-button");
    const loginButton = document.getElementById("login-button");
    const searchButton = document.getElementById("search-button");
    const saveButton = document.getElementById("save-button");
    const uploadButton = document.getElementById("upload-button");
    const themeToggle = document.getElementById("theme-toggle");
    const themeIcon = document.getElementById("theme-icon");
    const sunIcon = document.getElementById("sun-icon");
    const moonIcon = document.getElementById("moon-icon");
    const homeLink = document.getElementById("home-link");
    const aboutLink = document.getElementById("about-link");
    const aboutPopup = document.getElementById("about-popup");
    const closePopup = document.getElementById("close-popup");

    // Check Login State
    const token = localStorage.getItem("token");
    if (token) {
        loginSection.classList.add("hidden");
        mainContent.classList.remove("hidden");
        logoutButton.classList.remove("hidden");
    } else {
        loginSection.classList.remove("hidden");
        mainContent.classList.add("hidden");
        logoutButton.classList.add("hidden");
    }

    // Theme Toggle
    const applyTheme = () => {
        const theme = localStorage.getItem("theme") || "dark";
        if (theme === "dark") {
            document.body.classList.add("dark");
            sunIcon.classList.add("hidden");
            moonIcon.classList.remove("hidden");
        } else {
            document.body.classList.remove("dark");
            sunIcon.classList.remove("hidden");
            moonIcon.classList.add("hidden");
        }
    };
    applyTheme();

    themeToggle.addEventListener("click", () => {
        const isDark = document.body.classList.toggle("dark");
        localStorage.setItem("theme", isDark ? "dark" : "light");
        sunIcon.classList.toggle("hidden", isDark);
        moonIcon.classList.toggle("hidden", !isDark);
    });

    // Login
    loginButton.addEventListener("click", async () => {
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();
        if (!username || !password) {
            alert("Please enter both username and password.");
            return;
        }
        try {
            console.log("Sending login request with username:", username);
            // Line 97: Changed URL to relative path
            const response = await fetch("/token", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
            });
            console.log("Login response status:", response.status);
            if (!response.ok) {
                const errorText = await response.text();
                console.error("Login response error text:", errorText);
                throw new Error(`Login failed: ${errorText}`);
            }
            const data = await response.json();
            console.log("Login response data:", data);
            localStorage.setItem("token", data.access_token);
            loginSection.classList.add("hidden");
            mainContent.classList.remove("hidden");
            logoutButton.classList.remove("hidden");
        } catch (error) {
            console.error("Detailed login error:", {
                message: error.message,
                name: error.name,
                stack: error.stack
            });
            // Line 121: Updated error message to reflect production context
            alert(`Login failed: ${error.message}. Please ensure you are connected to the deployed application.`);
        }
    });

    // Logout
    logoutButton.addEventListener("click", () => {
        localStorage.removeItem("token");
        loginSection.classList.remove("hidden");
        mainContent.classList.add("hidden");
        logoutButton.classList.add("hidden");
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

    // Home Link
    homeLink.addEventListener("click", (e) => {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: "smooth" });
        if (token) {
            loginSection.classList.add("hidden");
            mainContent.classList.remove("hidden");
            logoutButton.classList.remove("hidden");
        } else {
            loginSection.classList.remove("hidden");
            mainContent.classList.add("hidden");
            logoutButton.classList.add("hidden");
        }
    });

    // About Popup
    const showPopup = (e) => {
        e.preventDefault();
        aboutPopup.classList.remove("hidden");
    };
    aboutLink.addEventListener("click", showPopup);
    aboutLink.addEventListener("touchstart", showPopup);

    const hidePopup = () => {
        aboutPopup.classList.add("hidden");
    };
    closePopup.addEventListener("click", hidePopup);
    closePopup.addEventListener("touchstart", hidePopup);

    aboutPopup.addEventListener("click", (e) => {
        if (e.target === aboutPopup) {
            hidePopup();
        }
    });

    // Download Datasheet
    async function downloadDatasheet(productId, datasheetPath, button) {
        try {
            const token = localStorage.getItem("token");
            console.log("Token being sent for datasheet download:", token);
            if (!token) {
                throw new Error("No token found. Please log in again.");
            }
            button.textContent = "Downloading...";
            button.disabled = true;
            // Line 193: Changed URL to relative path
            const response = await fetch(`/api/datasheet/${productId}`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(`Failed to download datasheet: ${text}`);
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            const fileName = datasheetPath ? datasheetPath.split(/[\\/]/).pop() : `datasheet_${productId}.pdf`;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Error downloading datasheet:", error);
            if (error.message.includes("401") || error.message.includes("No token found")) {
                alert("Session expired or not authenticated. Please log in again.");
                localStorage.removeItem("token");
                loginSection.classList.remove("hidden");
                mainContent.classList.add("hidden");
                logoutButton.classList.add("hidden");
                window.scrollTo({ top: 0, behavior: "smooth" });
            } else {
                alert(`Error downloading datasheet: ${error.message}`);
            }
        } finally {
            button.textContent = "Download Datasheet";
            button.disabled = false;
        }
    }

    // Search Products
    let currentPage = 1;
    const itemsPerPage = 5;
    let allProducts = [];

    searchButton.addEventListener("click", async () => {
        const requirements = document.getElementById("requirements-text").value.trim();
        if (!requirements) {
            alert("Please enter requirements to search.");
            return;
        }
        const searchText = document.getElementById("search-text");
        const spinner = document.getElementById("search-spinner");
        searchText.textContent = "Searching...";
        spinner.classList.remove("hidden");
        try {
            const token = localStorage.getItem("token");
            console.log("Sending semantic search request with token:", token);
            // Line 260: Changed URL to relative path
            const response = await fetch("/api/semantic_search", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ requirements })
            });
            console.log("Semantic search response status:", response.status);
            if (!response.ok) {
                const errorText = await response.text();
                console.error("Semantic search response error text:", errorText);
                if (response.status === 401) {
                    throw new Error("Session expired or not authenticated. Please log in again.");
                }
                throw new Error(`Search failed: ${errorText}`);
            }
            const products = await response.json();
            console.log("Search response:", products);
            if (!products.products || products.products.length === 0) {
                console.log("No products found in response.");
                displayProducts({ products: [] });
            } else {
                displayProducts(products);
            }
        } catch (error) {
            console.error("Detailed search error:", {
                message: error.message,
                name: error.name,
                stack: error.stack
            });
            // Line 287: Updated error message to reflect production context
            alert(`Error searching products: ${error.message}. Please ensure you are connected to the deployed application and that products are added to the database.`);
            if (error.message.includes("Session expired")) {
                localStorage.removeItem("token");
                loginSection.classList.remove("hidden");
                mainContent.classList.add("hidden");
                logoutButton.classList.add("hidden");
                window.scrollTo({ top: 0, behavior: "smooth" });
            }
        } finally {
            searchText.textContent = "Search";
            spinner.classList.add("hidden");
        }
    });

    // Save Product
    saveButton.addEventListener("click", async () => {
        const product = {
            company_name: document.getElementById("company-name").value.trim(),
            product_name: document.getElementById("product-name").value.trim(),
            product_type: document.getElementById("product-type").value.trim(),
            datasheet_path: document.getElementById("datasheet-path").value.trim() || "N/A",
            specs: document.getElementById("specs").value.trim()
        };
        if (!product.company_name || !product.product_name || !product.product_type || !product.specs) {
            alert("Please fill in all required fields (Company Name, Product Name, Product Type, Specifications).");
            return;
        }
        try {
            // Line 318: Changed URL to relative path
            const response = await fetch("/api/products", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`
                },
                body: JSON.stringify(product)
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(`Save failed: ${text}`);
            }
            await response.json();
            alert(`Product "${product.product_name}" saved successfully!`);
            document.getElementById("product-form").reset();
        } catch (error) {
            console.error("Error saving product:", error);
            // Line 335: Updated error message to reflect production context
            alert(`Error saving product: ${error.message}. Please ensure you are connected to the deployed application.`);
        }
    });

    // Upload Datasheet
    uploadButton.addEventListener("click", async () => {
        const fileInput = document.getElementById("datasheet-upload");
        const file = fileInput.files[0];
        if (!file) {
            alert("Please select a PDF file to upload.");
            return;
        }
        const formData = new FormData();
        formData.append("file", file);
        try {
            // Line 351: Changed URL to relative path
            const response = await fetch("/api/upload", {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${localStorage.getItem("token")}`
                },
                body: formData
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(`Upload failed: ${text}`);
            }
            await response.json();
            alert(`Datasheet "${file.name}" uploaded and processed successfully!`);
            fileInput.value = "";
            if (document.getElementById("requirements-text").value) {
                searchButton.click();
            }
        } catch (error) {
            console.error("Error uploading datasheet:", error);
            // Line 370: Updated error message to reflect production context
            alert(`Error uploading datasheet: ${error.message}. Please ensure you are connected to the deployed application.`);
        }
    });

    // Apply Filters
    function applyFilters(products) {
        const companyFilter = document.getElementById("filter-company").value.toLowerCase().trim();
        const typeFilter = document.getElementById("filter-type").value.toLowerCase().trim();
        const scoreFilter = parseFloat(document.getElementById("filter-score").value) || 0;
        return products.filter(product => {
            const matchesCompany = !companyFilter || (product.company || "").toLowerCase().includes(companyFilter);
            const matchesType = !typeFilter || (product.product_type || "").toLowerCase().includes(typeFilter);
            const matchesScore = !scoreFilter || (product.match_score || 0) >= scoreFilter;
            return matchesCompany && matchesType && matchesScore;
        });
    }

    // Display Products
    function displayProducts(products) {
        allProducts = applyFilters(products.products || products);
        console.log("Filtered products:", allProducts);
        const tbody = document.getElementById("products-table").getElementsByTagName("tbody")[0];
        tbody.innerHTML = "";
        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        const paginatedProducts = allProducts.slice(start, end);
        if (paginatedProducts.length === 0 && allProducts.length === 0) {
            const row = tbody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 8;
            cell.textContent = "No products found. Try adding a product or uploading a datasheet.";
            cell.className = "p-4 text-center text-gray-600 dark:text-gray-400";
        } else {
            paginatedProducts.forEach(product => {
                const row = tbody.insertRow();
                row.className = "hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200";
                row.insertCell().textContent = product.company || "N/A";
                row.insertCell().textContent = product.name || "N/A";
                row.insertCell().textContent = product.product_type || "N/A";
                row.insertCell().textContent = product.match_score ? `${product.match_score}%` : "N/A";
                row.insertCell().textContent = product.directory || "N/A";
                row.insertCell().textContent = product.datasheet_path || "N/A";
                row.insertCell().textContent = product.specs ? product.specs.substring(0, 100) + (product.specs.length > 100 ? "..." : "") : "N/A";
                const datasheetCell = row.insertCell();
                if (product.product_id && product.datasheet_path && product.datasheet_path !== "N/A") {
                    const button = document.createElement("button");
                    button.textContent = "Download Datasheet";
                    button.className = "text-coral-500 hover:underline transition-all duration-200";
                    button.addEventListener("click", () => downloadDatasheet(product.product_id, product.datasheet_path, button));
                    datasheetCell.appendChild(button);
                } else {
                    datasheetCell.textContent = "N/A";
                }
            });
        }
        updatePagination();
    }

    // Update Pagination
    function updatePagination() {
        const paginationDiv = document.getElementById("pagination");
        const totalPages = Math.ceil(allProducts.length / itemsPerPage);
        paginationDiv.innerHTML = "";
        for (let i = 1; i <= totalPages; i++) {
            const button = document.createElement("button");
            button.textContent = i;
            button.className = `px-4 py-2 rounded-lg ${i === currentPage ? 'bg-coral-500 text-white border-2 border-coral-600' : 'bg-gray-200 text-gray-700 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600'} hover:bg-coral-400 hover:text-white hover:font-semibold hover:scale-105 focus:ring-2 focus:ring-coral-300 active:bg-coral-600 transition-all duration-200`;
            button.addEventListener("click", () => {
                currentPage = i;
                displayProducts(allProducts);
            });
            paginationDiv.appendChild(button);
        }
    }

    // Filter Event Listeners
    document.getElementById("filter-company").addEventListener("input", () => {
        currentPage = 1;
        displayProducts(allProducts);
    });
    document.getElementById("filter-type").addEventListener("input", () => {
        currentPage = 1;
        displayProducts(allProducts);
    });
    document.getElementById("filter-score").addEventListener("input", () => {
        currentPage = 1;
        displayProducts(allProducts);
    });
});