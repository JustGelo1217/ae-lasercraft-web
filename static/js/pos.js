"use strict";

let cart = [];


/* ===================== ELEMENTS ===================== */
const cartItems = document.getElementById("cartItems");
const cartTotal = document.getElementById("cartTotal");
const cashInput = document.getElementById("cashInput");
const changeAmount = document.getElementById("changeAmount");
const searchInput = document.getElementById("productSearch");

/* ===================== RECEIPT TEMPLATE ===================== */
const RECEIPT_TEMPLATES = {

  compact: (items, total, cash) => {
    const change = cash - total;
    const date = new Date().toLocaleString();

    return `
<div style="font-family: monospace; font-size: 12px; width: 280px">
  <div style="text-align:center">
    <strong style="font-size:16px;">AE LaserCraft</strong><br/>
    Custom Laser Engraving<br/>
    ------------------------------<br/>
    ${date}
  </div>

  <hr/>

  <table width="100%" style="border-collapse: collapse;">
    ${items.map(i => `
      <tr>
        <td colspan="2">${i.name}${i.source === "pricing" ? " *" : ""}</td>
      </tr>
      <tr>
        <td>${i.qty} × ₱${i.price.toFixed(2)}</td>
        <td style="text-align:right">₱${(i.qty * i.price).toFixed(2)}</td>
      </tr>
    `).join("")}
  </table>

  <hr/>

  <table width="100%">
    <tr><td>Total</td><td align="right">₱${total.toFixed(2)}</td></tr>
    <tr><td>Cash</td><td align="right">₱${cash.toFixed(2)}</td></tr>
    <tr><td>Change</td><td align="right">₱${change.toFixed(2)}</td></tr>
  </table>

  <hr/>

  <div style="text-align:center">
    Thank you for your purchase!<br/>
    FB / IG / TikTok: AE LaserCraft
  </div>
</div>
`;
  },

  detailed: (items, total, cash) => {
    const change = cash - total;
    const date = new Date().toLocaleString();
    const receiptNo = Math.floor(Math.random() * 1000000);

    return `
<div style="font-family: Arial, sans-serif; font-size: 13px; width: 380px; padding: 10px">

  <div style="text-align:center">
    <div style="font-size:20px; font-weight:bold;">AE LaserCraft</div>
    <div>Custom Laser Engraving & Crafts</div>
    <div style="font-size:11px; color:#666;">Philippines</div>
  </div>

  <hr/>

  <div style="font-size:11px">
    Receipt #: ${receiptNo}<br/>
    Date: ${date}
  </div>

  <table width="100%" style="margin-top:10px; border-collapse: collapse;">
    <thead>
      <tr style="border-bottom:1px solid #000">
        <th align="left">Item</th>
        <th align="right">Qty</th>
        <th align="right">Price</th>
        <th align="right">Total</th>
      </tr>
    </thead>
    <tbody>
      ${items.map(i => `
        <tr>
          <td>
            ${i.name}
            ${i.source === "pricing" ? `<span style="font-size:10px">(Custom)</span>` : ""}
          </td>
          <td align="right">${i.qty}</td>
          <td align="right">₱${i.price.toFixed(2)}</td>
          <td align="right">₱${(i.qty * i.price).toFixed(2)}</td>
        </tr>
      `).join("")}
    </tbody>
  </table>

  <hr/>

  <table width="100%">
    <tr><td>Subtotal</td><td align="right">₱${total.toFixed(2)}</td></tr>
    <tr><td>Cash</td><td align="right">₱${cash.toFixed(2)}</td></tr>
    <tr><td><strong>Change</strong></td><td align="right"><strong>₱${change.toFixed(2)}</strong></td></tr>
  </table>

  <hr/>

  <div style="text-align:center; font-size:12px">
    Thank you for supporting small business! ❤️<br/>
    Follow us: Facebook / Instagram / TikTok @AE LaserCraft
  </div>

</div>
`;
  }

};



/* ===================== FEATURE FLAG ===================== */
if (window.APP_SETTINGS?.enablePOS === false) {
  document.body.innerHTML = `
    <div class="min-h-screen flex items-center justify-center">
      <h1 class="text-xl text-red-400">POS is currently disabled</h1>
    </div>
  `;
  throw new Error("POS disabled by feature flag");
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

/* ===================== INIT ===================== */
document.addEventListener("DOMContentLoaded", async () => {
  const payload = localStorage.getItem("pos_pricing_item");

  if (payload) {
    const item = JSON.parse(payload);

    cart.push({
      id: item.id,
      name: item.name,
      price: item.unit_price,
      qty: item.quantity,
      stock: Infinity,
      source: item.source || "pos"
    });

    localStorage.removeItem("pos_pricing_item");
    renderCart();

    Swal.fire({
      icon: "success",
      title: "Item Added from Pricing",
      text: `${item.name} × ${item.quantity}`,
      timer: 1600,
      showConfirmButton: false
    });
  }

  await refreshStockFromServer();
});

/* ===================== PRODUCT BUTTONS ===================== */
document.querySelectorAll("[data-id]").forEach(btn => {
  btn.addEventListener("click", () => {
    addToCart(
      btn.dataset.id,
      btn.dataset.name,
      Number(btn.dataset.price),
      Number(btn.dataset.stock)
    );
  });
});

/* ===================== CART HELPERS ===================== */
function getCartTotal() {
  return cart.reduce((sum, item) => sum + item.price * item.qty, 0);
}

/* ===================== ADD TO CART ===================== */
function addToCart(id, name, price, stock) {
  if (stock <= 0) {
    alertError("Out of stock", `${name} is unavailable`);
    return;
  }

  const existing = cart.find(i => i.id === id);

  if (existing) {
    if (existing.qty >= stock) {
      Swal.fire("Stock limit reached", "", "warning");
      return;
    }
    existing.qty++;
  } else {
    cart.push({ id, name, price, qty: 1, stock });
  }

  renderCart();
}

/* ===================== RENDER CART ===================== */
function renderCart() {
  cartItems.innerHTML = "";
  let total = 0;

  cart.forEach((item, index) => {
    total += item.price * item.qty;

    cartItems.innerHTML += `
      <div class="flex justify-between items-center bg-gray-700 p-2 rounded">
        <div>
          <div class="font-semibold flex items-center gap-2">
            ${item.name}
            ${item.source === "pricing"
              ? `<span class="text-xs bg-blue-600 px-2 py-0.5 rounded">PRICING</span>`
              : ""}
          </div>
          <div class="text-sm text-gray-300">
            ₱${item.price.toFixed(2)} × ${item.qty}
          </div>
        </div>
        <div class="flex gap-2">
          <button onclick="changeQty(${index}, -1)" class="px-2 bg-gray-600 rounded">−</button>
          <button onclick="changeQty(${index}, 1)" class="px-2 bg-gray-600 rounded">+</button>
        </div>
      </div>
    `;
  });

  cartTotal.innerText = `₱${total.toFixed(2)}`;
  updateChange();
}

/* ===================== CHANGE QUANTITY ===================== */
function changeQty(index, delta) {
  const item = cart[index];
  item.qty += delta;

  if (item.qty <= 0) {
    cart.splice(index, 1);
  } else if (item.qty > item.stock) {
    item.qty = item.stock;
    Swal.fire("Stock limit reached", "", "warning");
  }

  renderCart();
}

/* ===================== CASH / CHANGE ===================== */
cashInput.addEventListener("input", updateChange);

function updateChange() {
  const cash = Number(cashInput.value || 0);
  const total = getCartTotal();
  changeAmount.innerText = cash >= total ? (cash - total).toFixed(2) : "0.00";
}

/* ===================== SEARCH ===================== */
searchInput.addEventListener("input", () => {
  const query = searchInput.value.toLowerCase();
  document.querySelectorAll(".product-btn").forEach(btn => {
    btn.style.display = btn.dataset.name.toLowerCase().includes(query)
      ? "block"
      : "none";
  });
});

/* ===================== CHECKOUT ===================== */
async function checkoutCart() {
  if (cart.length === 0) {
    Swal.fire("Cart is empty", "", "warning");
    return;
  }

  const total = getCartTotal();
  const cash = Number(cashInput.value);

  /* REQUIRE CASH */
  if (window.APP_SETTINGS?.requireCash && (isNaN(cash) || cash < total)) {
    Swal.fire("Cash Required", "Please enter sufficient cash", "error");
    return;
  }

  /* CONFIRM CHECKOUT (ONLY ONCE – FIXED) */
  if (window.APP_SETTINGS?.confirmCheckout) {
    const confirm = await Swal.fire({
      title: "Confirm Checkout",
      html: `
        <p>Total: ₱${total.toFixed(2)}</p>
        <p>Cash: ₱${cash.toFixed(2)}</p>
        <p>Change: ₱${(cash - total).toFixed(2)}</p>
      `,
      icon: "question",
      showCancelButton: true,
      confirmButtonText: "Checkout"
    });

    if (!confirm.isConfirmed) return;
  }

  Swal.fire({
    title: "Processing...",
    allowOutsideClick: false,
    didOpen: () => Swal.showLoading()
  });

  try {
    const res = await fetch("/sales/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cart })
    });

    const result = await res.json();

    if (result.status === "success") {
      buildReceipt(total, cash);

      if (window.APP_SETTINGS?.autoPrintReceipt) {
        printReceipt();
      }

      Swal.fire({
        icon: "success",
        title: "Checkout Complete",
        timer: 1200,
        showConfirmButton: false
      });

      setTimeout(() => location.reload(), 1200);
    } else {
      Swal.fire("Checkout Failed", result.error || "", "error");
    }
  } catch (err) {
    console.error(err);
    Swal.fire("Server Error", "Check backend logs", "error");
  }
}

/* ===================== STOCK REFRESH ===================== */
async function refreshStockFromServer() {
  try {
    const res = await fetch("/api/products/stock");
    const data = await res.json();

    data.forEach(p => {
      const btn = document.getElementById(`product-btn-${p.id}`);
      const label = document.getElementById(`stock-label-${p.id}`);
      if (!btn || !label) return;

      btn.dataset.stock = p.stock;
      label.innerText = `Stock: ${p.stock}`;

      if (p.stock <= 0) {
        btn.disabled = true;
        btn.classList.add("opacity-50", "cursor-not-allowed");
      }
    });
  } catch (err) {
    console.error("Stock refresh failed", err);
  }
}

/* ===================== RECEIPT ===================== */
function buildReceipt(total, cash) {
  const template =
    window.APP_SETTINGS?.receiptTemplate || "compact";

  const html = RECEIPT_TEMPLATES[template](
    cart,
    total,
    cash
  );

  const receipt = document.getElementById("receipt");
  receipt.innerHTML = html;
}


function printReceipt() {
  const receipt = document.getElementById("receipt");
  const win = window.open("", "", "width=300,height=600");
  win.document.write(receipt.outerHTML);
  win.document.close();
  win.print();
  win.close();
}

