const API_URL = "http://127.0.0.1:8000"; 
// const USER_ID = 999; // Using the test user ID we created in the database

let inventory = [];
let currentFilter = "all";


function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

// Helper function to get the token for secure requests
function getAuthHeaders() {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}` // This validates the user on the backend
  };
}

async function login() {
  const email = document.getElementById("username").value; // Using email as username
  const password = document.getElementById("password").value;

  // FastAPI OAuth2 requires form data, not JSON
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  try {
    const response = await fetch(`${API_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData
    });

    if (!response.ok) {
      alert("Invalid email or password");
      return;
    }

    const data = await response.json();
    
    // Save the token locally
    localStorage.setItem("token", data.access_token);
    
    showScreen("dashboard");
    fetchInventory(); 
  } catch (error) {
    console.error("Login failed:", error);
  }
}

async function fetchInventory() {
  try {
    // Notice the route is now /ingredients/ without the ID attached!
    const response = await fetch(`${API_URL}/ingredients/`, {
      headers: getAuthHeaders()
    });
    
    if (response.status === 401) {
       alert("Your session expired. Please log in again.");
       showScreen("login-screen");
       return;
    }
    
    inventory = await response.json();
    renderList();
  } catch (error) {
    console.error("Failed to fetch inventory:", error);
  }
}

async function addItem() {
  const categoryMap = { "Vegetables": 1, "Meat": 2, "Dry Goods": 3, "Sauces": 4, "Drinks": 5 };
  const selectedCategory = document.getElementById("category").value;

  let item = {
    category_id: categoryMap[selectedCategory] || 1, 
    ingredient_name: document.getElementById("name").value,
    quantity: parseFloat(document.getElementById("quantity").value) || 0,
    unit_of_measurement: document.getElementById("unit").value,
    low_stock_threshold: parseFloat(document.getElementById("lowStock").value) || 5,
    is_active: true
  };

  try {
    await fetch(`${API_URL}/ingredients/`, {
      method: "POST",
      headers: getAuthHeaders(), // Secure header!
      body: JSON.stringify(item)
    });
    
    document.getElementById("name").value = "";
    document.getElementById("quantity").value = "";
    document.getElementById("lowStock").value = "";
    
    fetchInventory();
  } catch (error) {
    console.error("Failed to add item:", error);
  }
}

function setFilter(type) {
  currentFilter = type;
  document.getElementById("tab-all").classList.remove("active");
  document.getElementById("tab-low").classList.remove("active");
  document.getElementById("tab-" + type).classList.add("active");
  renderList();
}

async function deleteItem(id) {
  if (confirm("Delete this item?")) {
    try {
      await fetch(`${API_URL}/ingredients/${id}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });
      fetchInventory();
    } catch (error) {
      console.error("Failed to delete item:", error);
    }
  }
}

async function changeQty(id, currentQty, amount) {
  let newQty = currentQty + amount;
  if (newQty < 0) newQty = 0;

  try {
    await fetch(`${API_URL}/ingredients/${id}`, {
      method: "PATCH",
      headers: getAuthHeaders(), 
      body: JSON.stringify({ quantity: newQty }) 
    });
    fetchInventory();
  } catch (error) {
    console.error("Failed to update quantity:", error);
  }
}

function renderList() {
  let list = document.getElementById("inventory-list");
  let alertBox = document.getElementById("alert");
  let search = document.getElementById("search").value.toLowerCase();

  list.innerHTML = "";

  // Check low stock against the correct database property name
  let lowItems = inventory.filter(item => item.quantity <= item.low_stock_threshold);

  if (lowItems.length > 0) {
    alertBox.innerHTML = `
      <div style="background:#ffcccc; padding:10px; border-radius:10px; margin-bottom:15px;">
        ⚠️ Low Stock: ${lowItems.map(i => i.ingredient_name).join(", ")}
      </div>
    `;
  } else {
    alertBox.innerHTML = "";
  }

  inventory.forEach((item) => {
    // Use ingredient_name for search filtering
    if (!item.ingredient_name.toLowerCase().includes(search)) return;
    if (currentFilter === "low" && item.quantity > item.low_stock_threshold) return;

    let div = document.createElement("div");
    div.className = "item";

    if (item.quantity <= item.low_stock_threshold) {
      div.classList.add("low");
    }

    // Determine status text dynamically based on current quantity
    let statusText = "In Stock";
    if (item.quantity === 0) {
      statusText = "Out";
    } else if (item.quantity <= item.low_stock_threshold) {
      statusText = "Low Stock";
    }

    // Map Category ID back to text for the user interface
    const reverseCategoryMap = {
      1: "Vegetables",
      2: "Meat",
      3: "Dry Goods",
      4: "Sauces",
      5: "Drinks"
    };
    let categoryName = reverseCategoryMap[item.category_id] || "Unknown Category";

    // Bind the database's unique ingredient_id to the buttons
    div.innerHTML = `
      <strong>${item.ingredient_name}</strong><br>
      <small>${categoryName}</small><br>
      Qty: ${item.quantity} ${item.unit_of_measurement}<br>
      Status: ${statusText}<br>
      <small>Low at: ${item.low_stock_threshold} ${item.unit_of_measurement}</small><br>

      <div class="buttons">
        <button onclick="changeQty(${item.ingredient_id}, ${item.quantity}, 1)">＋</button>
        <button onclick="changeQty(${item.ingredient_id}, ${item.quantity}, -1)">－</button>
        <button onclick="deleteItem(${item.ingredient_id})">🗑️</button>
      </div>
    `;

    list.appendChild(div);
  });
}
