"use strict";

let currentPage = 1;
let searchTimer = null;
const modal = document.getElementById("userModal");

function openAddUserModal() {
  document.getElementById("modalTitle").innerText = "Add User";
  document.getElementById("userId").value = "";
  document.getElementById("usernameInput").value = "";
  document.getElementById("fullnameInput").value = "";
  document.getElementById("passwordInput").value = "";
  document.getElementById("passwordSection").style.display = "block";
  document.getElementById("usernameInput").disabled = false;

  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function openEditUserModal(id, fullName, role) {
  document.getElementById("modalTitle").innerText = "Edit User";
  document.getElementById("userId").value = id;
  document.getElementById("fullnameInput").value = fullName;
  document.getElementById("roleInput").value = role;
  document.getElementById("passwordSection").style.display = "none";
  document.getElementById("usernameInput").disabled = true;

  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function closeUserModal() {
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

async function saveUser() {
  const id = document.getElementById("userId").value;
  const username = document.getElementById("usernameInput").value;
  const fullName = document.getElementById("fullnameInput").value;
  const role = document.getElementById("roleInput").value;
  const password = document.getElementById("passwordInput").value;

  let url, payload;

  if (id) {
    url = "/users/update";
    payload = { id, full_name: fullName, role };
  } else {
    if (!username || !password) {
      Swal.fire("Username and password required");
      return;
    }

    url = "/users/add";
    payload = { username, full_name: fullName, role, password };
  }

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  let result;

    try {
    result = await res.json();
    } catch (e) {
    const text = await res.text();
    console.error("Server returned non-JSON:", text);
    Swal.fire("Server error", "Check backend logs", "error");
    return;
    }


  if (result.status === "success") {
    Swal.fire("Saved!", "", "success").then(() => location.reload());
  } else {
    Swal.fire("Error", result.message || "Failed", "error");
  }
}

async function toggleUser(id) {
  const confirm = await Swal.fire({
    title: "Change user status?",
    icon: "warning",
    showCancelButton: true
  });

  if (!confirm.isConfirmed) return;

  const res = await fetch("/users/toggle-active", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id })
  });

  const result = await res.json();

  if (result.status === "success") {
    location.reload();
  } else {
    Swal.fire("Error", result.message, "error");
  }
}


async function resetPassword(id) {
  const { value: newPass } = await Swal.fire({
    title: "New password",
    input: "password",
    inputLabel: "Enter new password",
    showCancelButton: true
  });

  if (!newPass) return;

  const res = await fetch("/users/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, password: newPass })
  });

  const result = await res.json();

  if (result.status === "success") {
    Swal.fire("Password reset", "", "success");
  } else {
    Swal.fire("Error", "Failed", "error");
  }
}

 // Edit user
  document.querySelectorAll(".edit-user-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      const name = btn.dataset.name;
      const role = btn.dataset.role;

      openEditUserModal(id, name, role);
    });
  });

  // Reset password
  document.querySelectorAll(".reset-user-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      resetPassword(btn.dataset.id);
    });
  });

  // Enable / Disable
  document.querySelectorAll(".toggle-user-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      toggleUser(btn.dataset.id);
    });
  });



/* =====================
   LOAD USERS
===================== */
async function loadUsers(page = 1) {
  currentPage = page;

  const search = document.getElementById("searchInput").value;
  const role = document.getElementById("roleFilter").value;
  const status = document.getElementById("statusFilter").value;

  const res = await fetch(
    `/api/users?page=${page}&search=${encodeURIComponent(search)}&role=${role}&status=${status}`
  );

  const data = await res.json();

  renderUsers(data.users);
  renderPagination(data.page, data.pages);
}

/* =====================
   RENDER USERS
===================== */
function renderUsers(users) {
  const tbody = document.getElementById("usersTable");
  tbody.innerHTML = "";

  if (!users.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-gray-400 py-6">
          No users found
        </td>
      </tr>
    `;
    return;
  }

  users.forEach(u => {
    tbody.innerHTML += `
      <tr class="border-t border-slate-700 text-center">
        <td class="p-3">${u[1]}</td>
        <td class="p-3">${u[2] || ""}</td>
        <td class="p-3 capitalize">${u[3]}</td>
        <td class="p-3">
          ${u[4] === 1
            ? `<span class="bg-green-600 px-2 py-1 rounded text-xs">Active</span>`
            : `<span class="bg-gray-600 px-2 py-1 rounded text-xs">Disabled</span>`}
        </td>
        <td class="p-3 text-xs text-gray-400">${u[5] || "Never"}</td>
        <td class="p-3 text-xs text-gray-400">${u[6] || "Never"}</td>
        <td lass="p-3 text-center space-x-2">
          <button class="bg-slate-700 px-2 py-1 rounded"
            onclick="openEditUserModal(${u[0]}, '${escapeJS(u[2] || "")}', '${u[3]}')">
            Edit
          </button>

          <button class="bg-yellow-600 px-2 py-1 rounded"
            onclick="resetPassword(${u[0]})">
            Reset
          </button>

          <button class="bg-red-600 px-2 py-1 rounded"
            onclick="toggleUser(${u[0]})">
            ${u[4] === 1 ? "Disable" : "Enable"}
          </button>
        </td>
      </tr>
    `;
  });
}

/* =====================
   PAGINATION
===================== */
function renderPagination(page, pages) {
  const container = document.getElementById("pagination");
  container.innerHTML = "";

  if (pages <= 1) return;

  for (let i = 1; i <= pages; i++) {
    container.innerHTML += `
      <button onclick="loadUsers(${i})"
        class="px-3 py-1 rounded ${i === page ? "bg-blue-600" : "bg-slate-700"}">
        ${i}
      </button>
    `;
  }
}

/* =====================
   SAFETY ESCAPE
===================== */
function escapeJS(str) {
  return str.replace(/'/g, "\\'");
}

/* =====================
   AUTO SEARCH (DEBOUNCE)
===================== */
function setupLiveSearch() {
  const input = document.getElementById("searchInput");

  input.addEventListener("input", () => {
    clearTimeout(searchTimer);

    searchTimer = setTimeout(() => {
      loadUsers(1);
    }, 300); // wait 300ms after typing stops
  });

  document.getElementById("roleFilter").addEventListener("change", () => loadUsers(1));
  document.getElementById("statusFilter").addEventListener("change", () => loadUsers(1));
}

/* =====================
   INIT
===================== */
document.addEventListener("DOMContentLoaded", () => {
  setupLiveSearch();
  loadUsers();
});

