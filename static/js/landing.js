const FB_PAGE = "https://www.messenger.com/t/925106990688741";     // ← change this
const EMAIL = "ae.lasercraft@email.com";             // ← change this

// ================= CATEGORY TOGGLE =================
function toggleCategory(id) {
  const el = document.getElementById(`cat-${id}`);
  if (!el) return;

  el.classList.toggle("expanded");
  el.classList.toggle("collapsed");

  // rotate arrow
  const btn = document.querySelector(`[data-category='${id}'] .toggle-icon`);
  if (btn) btn.classList.toggle("rotate-180");
}



// ================= FADE IN ON SCROLL =================
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add("show");
    }
  });
}, { threshold: 0.15 });

document.querySelectorAll(".fade-in").forEach(el => observer.observe(el));


function openInquiryModal(productName, designName) {
  const msg = `Hello! I'm interested in:

Product: ${productName}
Design: ${designName}

Please send me more details.`;

  const encoded = encodeURIComponent(msg);

  const fb = "https://m.me/925106990688741";
  const mail = `mailto:ae.lasercraft@email.com?subject=Product Inquiry&body=${encoded}`;

  Swal.fire({
    title: "Contact us",
    html: `
      <div class="space-y-3">
        <button id="messengerBtn"
           class="w-full bg-blue-600 text-white py-2 rounded">Messenger</button>

        <a href="${mail}"
           class="block bg-emerald-600 text-white py-2 rounded">Email</a>
      </div>
    `,
    showConfirmButton: false
  });

  // Messenger click handler
  setTimeout(() => {
    const btn = document.getElementById("messengerBtn");
    if (!btn) return;

    btn.onclick = async () => {
      try {
        await navigator.clipboard.writeText(msg);
      } catch {}

      window.open(fb, "_blank");

      Swal.fire({
        toast: true,
        position: "bottom",
        icon: "success",
        title: "Message copied! Paste it in Messenger",
        showConfirmButton: false,
        timer: 2500
      });
    };
  }, 50);
}


function closeInquiryModal() {
  const modal = document.getElementById("inquiryModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

function jumpToCategory(id) {
  const wrapper = document.getElementById(`cat-wrapper-${id}`);
  const section = document.getElementById(`cat-${id}`);

  if (!section || !wrapper) return;

  section.classList.add("expanded");
  section.classList.remove("collapsed");

  wrapper.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}


document.querySelectorAll(".category-toggle").forEach(btn => {
  btn.addEventListener("click", () => {
    const id = btn.dataset.category;
    toggleCategory(id);
  });
});

// ================= OPEN DESIGNS =================
async function openDesigns(productId, productName) {
  const modal = document.getElementById("designModal");
  const grid = document.getElementById("designGrid");
  const title = document.getElementById("designModalTitle");

  // SAFETY CHECK
  if (!modal || !grid || !title) {
    console.error("Design modal elements missing from page");
    return;
  }

  title.textContent = `Designs for ${productName}`;
  grid.innerHTML = `<p class="col-span-full text-slate-400">Loading designs...</p>`;

  modal.classList.remove("hidden");

  try {
    const res = await fetch(`/gallery/${productId}/designs`);
    const designs = await res.json();

    if (!designs.length) {
      grid.innerHTML = `<p class="col-span-full text-slate-400">No designs available.</p>`;
      return;
    }

    grid.innerHTML = "";

    designs.forEach(d => {
      const card = document.createElement("div");
      card.className =
        "cursor-pointer bg-slate-800 rounded-lg overflow-hidden hover:scale-105 transition";

      card.innerHTML = `
        <img src="${d.image}" class="w-full h-32 object-cover">
        <div class="p-2 text-sm text-center">${d.name}</div>
      `;

      card.onclick = () => openInquiryModal(productName, d.name);

      grid.appendChild(card);
    });

  } catch (err) {
    console.error(err);
    grid.innerHTML = `<p class="col-span-full text-red-400">Failed to load designs.</p>`;
  }
}


function closeDesignModal() {
  document.getElementById("designModal").classList.add("hidden");
}

async function loadFeaturedDesigns() {
  try {
    const res = await fetch("/api/featured-designs");
    const designs = await res.json();

    const grid = document.getElementById("featuredDesignsGrid");
    if (!grid) return;

    if (!designs.length) {
      grid.innerHTML = `
        <div class="col-span-full text-center text-slate-500">
          No featured designs yet.
        </div>
      `;
      return;
    }

    grid.innerHTML = designs.map(d => `
      <div class="group bg-slate-900 rounded-xl overflow-hidden shadow hover:scale-[1.03] transition cursor-pointer">

        <div class="relative">
          <img src="${d.image}" class="w-full h-40 object-cover">

          <div class="absolute top-2 left-2 bg-emerald-500 text-black text-xs font-bold px-2 py-1 rounded">
            FEATURED
          </div>

          <div class="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition"></div>

          <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
            <span class="bg-emerald-400 text-black px-4 py-2 rounded-lg text-sm font-semibold">
              View Design
            </span>
          </div>
        </div>

        <div class="p-3">
          <div class="font-semibold truncate">${d.name}</div>
          <div class="text-xs text-slate-400">${d.product}</div>
        </div>

      </div>
    `).join("");

  } catch (err) {
    console.error("Failed to load featured designs", err);
  }
}

function openDesignPreview(img, title) {
  document.getElementById("featuredPreviewImg").src = img;
  document.getElementById("featuredPreviewTitle").textContent = title;

  const modal = document.getElementById("featuredPreviewModal");
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function closeDesignPreview() {
  const modal = document.getElementById("featuredPreviewModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

/* ================= FEATURED CAROUSEL ================= */

let carouselIndex = 0;
let carouselTimer = null;

function initFeaturedCarousel() {
  const track = document.getElementById("featuredCarousel");
  const dotsContainer = document.getElementById("carouselDots");

  if (!track || track.children.length === 0) return;

  const slides = track.children;
  const total = slides.length;

  // Create dots
  dotsContainer.innerHTML = "";
  for (let i = 0; i < total; i++) {
    const dot = document.createElement("button");
    dot.className = "w-2.5 h-2.5 rounded-full bg-white/40";
    dot.onclick = () => goToSlide(i);
    dotsContainer.appendChild(dot);
  }

  updateCarousel();

  carouselTimer = setInterval(nextSlide, 4500);
}

function updateCarousel() {
  const track = document.getElementById("featuredCarousel");
  const dots = document.querySelectorAll("#carouselDots button");

  track.style.transform = `translateX(-${carouselIndex * 100}%)`;

  dots.forEach((d, i) => {
    d.className = i === carouselIndex
      ? "w-3 h-3 rounded-full bg-emerald-400"
      : "w-2.5 h-2.5 rounded-full bg-white/40";
  });
}

function nextSlide() {
  const track = document.getElementById("featuredCarousel");
  if (!track) return;

  carouselIndex = (carouselIndex + 1) % track.children.length;
  updateCarousel();
}

function goToSlide(index) {
  carouselIndex = index;
  updateCarousel();

  clearInterval(carouselTimer);
  carouselTimer = setInterval(nextSlide, 4500);
}


document.addEventListener("DOMContentLoaded", () => {
  loadFeaturedDesigns();
  initFeaturedCarousel();
  /* ================= PRODUCT SEARCH ================= */
  const searchInput = document.getElementById("productSearch");

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      const q = searchInput.value.toLowerCase().trim();

      document.querySelectorAll(".product-card").forEach(card => {
        const name = (card.dataset.name || "").toLowerCase();
        card.style.display = name.includes(q) ? "" : "none";
      });
    });
  }


  // ================= PRODUCT CLICK → OPEN DESIGNS =================
document.querySelectorAll(".product-card").forEach(card => {
  card.addEventListener("click", e => {
    e.stopPropagation();

    const id = card.dataset.id;
    const name = card.dataset.name;

    openDesigns(id, name);
  });
});


// ================= CATEGORY JUMP BUTTONS =================
document.querySelectorAll(".category-jump").forEach(btn => {
  btn.addEventListener("click", () => {
    const id = btn.dataset.category;
    jumpToCategory(id);
  });
});

});
