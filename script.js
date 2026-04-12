let inventory = JSON.parse(localStorage.getItem("inventory")) || [];
let currentFilter = "all";

function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

function login() {
  showScreen("dashboard");
}

function saveData() {
  localStorage.setItem("inventory", JSON.stringify(inventory));
}

function addItem() {
  let item = {
    name: document.getElementById("name").value,
    date: document.getElementById("date").value,
    quantity: parseInt(document.getElementById("quantity").value),
    unit: document.getElementById("unit").value,
    category: document.getElementById("category").value,
    condition: document.getElementById("condition").value,
    status: document.getElementById("status").value,
    notes: document.getElementById("notes").value,
    lowStock: parseInt(document.getElementById("lowStock").value) || 5
  };

  inventory.push(item);
  saveData();
  renderList();
}

function setFilter(type) {
  currentFilter = type;

  document.getElementById("tab-all").classList.remove("active");
  document.getElementById("tab-low").classList.remove("active");
  document.getElementById("tab-" + type).classList.add("active");

  renderList();
}

function deleteItem(index) {
  if (confirm("Delete this item?")) {
    inventory.splice(index, 1);
    saveData();
    renderList();
  }
}

function changeQty(index, amount) {
  let item = inventory[index];

  item.quantity += amount;
  if (item.quantity < 0) item.quantity = 0;

  if (item.quantity === 0) {
    item.status = "Out";
  } else if (item.quantity <= item.lowStock) {
    item.status = "Low Stock";
  } else {
    item.status = "In Stock";
  }

  saveData();
  renderList();
}

function renderList() {
  let list = document.getElementById("inventory-list");
  let alertBox = document.getElementById("alert");
  let search = document.getElementById("search").value.toLowerCase();

  list.innerHTML = "";

  let lowItems = inventory.filter(item => item.quantity <= item.lowStock);

  if (lowItems.length > 0) {
    alertBox.innerHTML = `
      <div style="background:#ffcccc; padding:10px; border-radius:10px;">
        ⚠️ Low Stock: ${lowItems.map(i => i.name).join(", ")}
      </div>
    `;
  } else {
    alertBox.innerHTML = "";
  }

  inventory.forEach((item, index) => {
    if (!item.name.toLowerCase().includes(search)) return;
    if (currentFilter === "low" && item.quantity > item.lowStock) return;

    let div = document.createElement("div");
    div.className = "item";

    if (item.quantity <= item.lowStock) {
      div.classList.add("low");
    }

    div.innerHTML = `
      <strong>${item.name}</strong><br>
      <small>${item.category}</small><br>
      Qty: ${item.quantity} ${item.unit}<br>
      Status: ${item.status}<br>
      <small>Low at: ${item.lowStock} ${item.unit}</small><br>
      ${item.notes ? `<em>📝 ${item.notes}</em><br>` : ""}

      <div class="buttons">
        <button onclick="changeQty(${index}, 1)">＋</button>
        <button onclick="changeQty(${index}, -1)">－</button>
        <button onclick="deleteItem(${index})">🗑️</button>
      </div>
    `;

    list.appendChild(div);
  });
}

renderList();