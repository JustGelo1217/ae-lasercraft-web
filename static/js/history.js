let activeTab = "SALE";

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

/* ================= TAB SWITCH ================= */
function switchTab(type) {
  activeTab = type;

  document.querySelectorAll("tbody tr").forEach(row => {
    row.style.display =
      row.dataset.type === type ? "" : "none";
  });

  document.getElementById("tab-sales").className =
    type === "SALE"
      ? "px-4 py-2 rounded bg-blue-600"
      : "px-4 py-2 rounded bg-gray-700";

  document.getElementById("tab-inventory").className =
    type === "INVENTORY"
      ? "px-4 py-2 rounded bg-blue-600"
      : "px-4 py-2 rounded bg-gray-700";
}


/* ================= VOID SALE ================= */
async function voidSale(button) {
  const saleId = button.dataset.saleId;

  const confirm = await Swal.fire({
    title: "Void this sale?",
    input: "text",
    inputPlaceholder: "Reason required",
    showCancelButton: true,
    confirmButtonText: "Void Sale"
  });

  if (!confirm.isConfirmed || !confirm.value) return;

  const res = await fetch(`/sales/void/${saleId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason: confirm.value })
  });

  const result = await res.json();

  if (result.status === "success") {
    Swal.fire("Sale voided", "", "success");
    location.reload();
  } else {
    Swal.fire("Error", result.error || "Void failed", "error");
  }
}

function showDetailsFromButton(btn) {
  const data = {
    id: btn.dataset.id,
    time: btn.dataset.time,
    type: btn.dataset.type,
    event: btn.dataset.event,
    item: btn.dataset.item,
    qty: btn.dataset.qty,
    amount: btn.dataset.amount,
    user: btn.dataset.user,
    status: btn.dataset.status
  };

  Swal.fire({
    title: "Transaction Details",
    html: `
      <div class="text-left space-y-2">
        <div><b>Record ID:</b> ${data.id}</div>
        <div><b>Time:</b> ${data.time}</div>
        <div><b>Type:</b> ${data.type}</div>
        <div><b>Event:</b> ${data.event}</div>
        <div><b>Item:</b> ${data.item}</div>
        <div><b>Quantity:</b> ${data.qty}</div>
        <div><b>Amount:</b> ₱${data.amount}</div>
        <div><b>User:</b> ${data.user}</div>
        <div><b>Status:</b> ${data.status}</div>
      </div>
    `,
    width: 500,
    confirmButtonText: "Close"
  });
}


/* ================= INIT ================= */
document.addEventListener("DOMContentLoaded", () => {
  switchTab("SALE");
});
