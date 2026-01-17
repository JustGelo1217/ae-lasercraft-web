const materialSelect = document.getElementById("materialSelect");
const materialCost = document.getElementById("materialCost");
const recPrice = document.getElementById("recPrice");
const breakdown = document.getElementById("breakdown");

/* ---------- LOAD MATERIALS ---------- */

const MATERIALS = {};

/* ================= LOAD MATERIALS ================= */
async function loadMaterials() {
  const res = await fetch("/api/materials");
  const data = await res.json();
  console.table(data);

  data.forEach(m => {
    MATERIALS[m.id] = m;

    const opt = document.createElement("option");
    opt.value = m.id;
    opt.textContent = `${m.name} (₱${m.cost})`;
    materialSelect.appendChild(opt);
  });
}

/* ================= AUTO-FILL COST ================= */
materialSelect.addEventListener("change", () => {
  const mat = MATERIALS[materialSelect.value];
  materialCost.value = mat ? mat.cost : "";
  console.log("Material cost from API:", mat.cost);

});

loadMaterials();


/* ---------- CALCULATION ---------- */
function calculatePrice() {

  const material = Number(document.getElementById("materialCost")?.value || 0);
  const laserTime = Number(document.getElementById("laserTime")?.value || 0);
  const laserRate = Number(document.getElementById("laserRate")?.value || 0);
  const laborCost = Number(document.getElementById("laborCost")?.value || 0);
  const overhead = Number(document.getElementById("overhead")?.value || 0);
  const discount = Number(document.getElementById("discount")?.value || 0);
  const qty = Number(document.getElementById("quantity")?.value || 1);

  // Calculate laser cost
  const laserCost = laserTime * laserRate;

  // Base cost
  const baseCost =
    material +
    laserCost +
    laborCost +
    overhead;

  // Unit cost
  let totalCost = baseCost * qty;

  // Apply discount
  let finalPrice = totalCost - (totalCost * discount / 100);

  // Update UI
  recPrice.innerText = `₱${finalPrice.toLocaleString("en-PH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;


  breakdown.innerHTML = `
    <div>Material: ₱${material.toLocaleString("en-PH", {minimumFractionDigits:2})}</div>
    <div>Laser: ₱${laserCost.toFixed(2)}</div>
    <div>Labor: ₱${laborCost.toFixed(2)}</div>
    <div>Overhead: ₱${overhead.toFixed(2)}</div>
    <div>Quantity: ${qty}</div>
    <div>Discount: ${discount}%</div>
  `;
}

function usePriceInPOS() {
  const materialPrice = Number(document.getElementById("materialCost")?.value || 0);
  const laserTime = Number(document.getElementById("laserTime")?.value || 0);
  const laserRate = Number(document.getElementById("laserRate")?.value || 0);
  const laborCost = Number(document.getElementById("laborCost")?.value || 0);
  const overhead = Number(document.getElementById("overhead")?.value || 0);
  const discount = Number(document.getElementById("discount")?.value || 0);
  const qty = Number(document.getElementById("quantity")?.value || 1);
  const unitPrice = Number(
    recPrice.innerText.replace("₱", "").replace(/,/g, "")
  );

  // Calculate laser cost
  const laserCost = laserTime * laserRate;

  // Base cost
  const baseCost =
    materialPrice +
    laserCost +
    laborCost +
    overhead;

  
  const materialId = materialSelect.value;
  const material = MATERIALS[materialId];

  if (!material) {
    Swal.fire("Select a material first", "", "warning");
    return;
  }

  if (qty <= 0 || baseCost <= 0) {
    Swal.fire("Invalid quantity or price", "", "error");
    return;
  }

  const payload = {
    id: material.id,          // REAL PRODUCT ID
    name: material.name,     // REAL PRODUCT NAME
    unit_price: baseCost,
    price:unitPrice,
    quantity: qty,
    source: "pricing"
  };
  console.log(JSON.stringify(payload));
  localStorage.setItem("pos_pricing_item", JSON.stringify(payload));

  Swal.fire({
    icon: "success",
    title: "Sent to POS",
    text: `${material.name} × ${qty}`,
    timer: 1600,
    showConfirmButton: false
  });
}




window.calculatePrice = calculatePrice;

