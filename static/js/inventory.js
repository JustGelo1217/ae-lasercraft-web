"use strict";


document.addEventListener("DOMContentLoaded", () => {

/* ================= FEATURE FLAG ================= */
if (window.APP_SETTINGS?.enableInventory === false) {
  alertError("Inventory Disabled", "Inventory management is disabled");
  return;
}


/* ================= SWEETALERT HELPERS ================= */
function alertSuccess(title, text = "") {
  return Swal.fire({
    icon: "success",
    title,
    text,
    timer: 1800,
    showConfirmButton: false
  });
}

function alertError(title, text = "") {
  return Swal.fire({
    icon: "error",
    title,
    text
  });
}

/* ================= MODAL ================= */
const modal = document.getElementById("itemModal");
const form = document.getElementById("itemForm");

function openModal() {
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function closeModal() {
  modal.classList.add("hidden");
  modal.classList.remove("flex");
  form.reset();
  document.getElementById("itemId").value = "";
}

/* ================= ADD ITEM ================= */
document.getElementById("addItemBtn").addEventListener("click", () => {
  document.getElementById("modalTitle").innerText = "Add Item";
  openModal();
});

/* ================= EDIT ITEM ================= */
document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".edit-btn");
    if (!btn) return;

    const id = btn.dataset.id;

    const res = await fetch(`/api/product/${id}`);
    const item = await res.json();

    document.getElementById("modalTitle").innerText = "Edit Item";
    document.getElementById("itemId").value = item.id;
    document.getElementById("itemName").value = item.name;
    document.getElementById("itemMaterial").value = item.material_type || "";
    document.getElementById("itemCategory").value = item.category || "";
    document.getElementById("itemPrice").value = item.price;
    document.getElementById("itemStock").value = item.stock;

    openModal();
});


/* ================= SAVE ITEM ================= */
form.addEventListener("submit", async e => {
  e.preventDefault();

  const stock = Number(document.getElementById("itemStock").value);

  if (window.APP_SETTINGS?.preventNegativeStock && stock < 0) {
    alertError("Invalid Stock", "Negative stock is not allowed");
    return;
  }

  const payload = {
    id: document.getElementById("itemId").value,
    name: document.getElementById("itemName").value,
    material_type: document.getElementById("itemMaterial").value || null,
    category: document.getElementById("itemCategory").value,
    price: Number(document.getElementById("itemPrice").value),
    stock
  };

  const url = payload.id ? "/inventory/edit" : "/inventory/add";

  Swal.fire({ title: "Saving...", didOpen: () => Swal.showLoading() });

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const result = await res.json();

  if (result.status === "success") {
    await alertSuccess("Saved successfully");
    location.reload();
  } else {
    alertError("Save failed", result.message || "");
  }
});

  /* ================= DELETE ITEM ================= */
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".delete-btn");
    if (!btn) return;

    const id = btn.dataset.id;

    const confirm = await Swal.fire({
      title: "Delete this item?",
      text: "This cannot be undone.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#dc2626",
      confirmButtonText: "Yes, delete",
      cancelButtonText: "Cancel"
    });

    if (!confirm.isConfirmed) return;

    Swal.fire({ title: "Deleting...", didOpen: () => Swal.showLoading() });

    try {
      const res = await fetch(`/inventory/delete/${id}`, { method: "POST" });
      const data = await res.json();

      if (data.status === "deleted") {
        await alertSuccess("Item deleted");
        location.reload();
      } else {
        alertError("Delete failed", data.message || "Unknown error");
      }
    } catch (err) {
      console.error(err);
      alertError("Delete failed", "Server error");
    }
  });



 });

 /* ================= INVENTORY FILTER ================= */
function filterInventory() {
  const search = document.getElementById("inventorySearch").value.toLowerCase();
  const category = document.getElementById("categoryFilter").value.toLowerCase();
  const lowStockOnly = document.getElementById("lowStockFilter").checked;

  document.querySelectorAll(".inventory-row").forEach(row => {
    const name = row.dataset.name || "";
    const cat = row.dataset.category || "";
    const stock = parseInt(row.dataset.stock || "0", 10);

    const lowStockLevel = window.APP_SETTINGS?.lowStockLevel ?? 5;

    const visible =
      (name.includes(search) || cat.includes(search)) &&
      (!category || cat === category) &&
      (!lowStockOnly || stock <= lowStockLevel);

    row.style.display = visible ? "" : "none";

    if (stock <= lowStockLevel) {
      row.classList.add("bg-red-500/10");
    }
  });
}

function resetInventoryFilters() {
  document.getElementById("inventorySearch").value = "";
  document.getElementById("categoryFilter").value = "";
  document.getElementById("lowStockFilter").checked = false;
  filterInventory();
}
