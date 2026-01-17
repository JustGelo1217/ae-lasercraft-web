let currentGalleryId = null;

/* ================= CATEGORY SCROLL ================= */
function scrollToCategory(category) {
  const el = document.getElementById(`cat-${category}`);
  if (!el) return;

  el.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}

/* ================= COLLAPSE / EXPAND ================= */
function toggleCategory(category) {
  const section = document.getElementById(`section-${category}`);
  const icon = document.getElementById(`icon-${category}`);

  if (!section || !icon) return;

  const isOpen = section.style.maxHeight && section.style.maxHeight !== "0px";

  if (isOpen) {
    section.style.maxHeight = "0px";
    section.style.opacity = "0";
    icon.style.transform = "rotate(-90deg)";
  } else {
    section.style.maxHeight = section.scrollHeight + "px";
    section.style.opacity = "1";
    icon.style.transform = "rotate(0deg)";
  }
}

/* ================= DELETE GALLERY ================= */
async function deleteGallery(button) {
  const id = button.dataset.id;

  const confirm = await Swal.fire({
    title: "Delete this item?",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Delete"
  });

  if (!confirm.isConfirmed) return;

  const res = await fetch(`/gallery/delete/${id}`, { method: "POST" });
  const result = await res.json();

  if (result.status === "deleted") {
    Swal.fire("Deleted", "", "success").then(() => location.reload());
  } else {
    Swal.fire("Error", "Delete failed", "error");
  }
}

/* ================= ADD GALLERY ================= */
function openGalleryModal() {
  document.getElementById("galleryModal").classList.remove("hidden");
  document.getElementById("galleryModal").classList.add("flex");
}

function closeGalleryModal() {
  document.getElementById("galleryModal").classList.add("hidden");
  document.getElementById("galleryModal").classList.remove("flex");
}

document.getElementById("galleryForm")?.addEventListener("submit", async e => {
  e.preventDefault();

  const formData = new FormData(e.target);
  const res = await fetch("/gallery/add", {
    method: "POST",
    body: formData
  });

  const result = await res.json();

  if (result.status === "success") {
    Swal.fire("Added", "Gallery item added", "success")
      .then(() => location.reload());
  } else {
    Swal.fire("Error", result.message || "Upload failed", "error");
  }
});

function previewGalleryImage(event) {
  const img = document.getElementById("galleryPreview");
  const file = event.target.files[0];

  if (!file) {
    img.classList.add("hidden");
    return;
  }

  img.src = URL.createObjectURL(file);
  img.classList.remove("hidden");
}

/* ================= EDIT GALLERY ================= */
function openEditGallery(id, name, category, price, showPrice) {
  const modal = document.getElementById("editGalleryModal");
  modal.classList.remove("hidden");
  modal.classList.add("flex");

  const form = document.getElementById("editGalleryForm");
  form.id.value = id;
  form.name.value = name;
  form.category.value = category || "";
  form.price.value = price ?? "";
  form.show_price.checked = showPrice === 1;
}

function closeEditGallery() {
  document.getElementById("editGalleryModal").classList.add("hidden");
}

document.getElementById("editGalleryForm")?.addEventListener("submit", async e => {
  e.preventDefault();

  const form = e.target;
  const data = Object.fromEntries(new FormData(form));
  data.show_price = form.show_price.checked ? 1 : 0;

  const res = await fetch("/gallery/edit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  const result = await res.json();

  if (result.status === "success") {
    Swal.fire("Updated", "", "success").then(() => location.reload());
  } else {
    Swal.fire("Error", "Update failed", "error");
  }
});

/* ================= DESIGN COLLECTION ================= */
async function openDesignCollection(galleryId, title) {
  currentGalleryId = galleryId;

  const modal = document.getElementById("designCollectionModal");
  modal.classList.remove("hidden");
  modal.classList.add("flex");

  document.getElementById("designTitle").textContent =
    title + " – Designs";

  const addBtn = document.getElementById("addDesignBtn");
  if (addBtn) addBtn.classList.remove("hidden");

  const grid = document.getElementById("designGrid");
  grid.innerHTML = "";

  const res = await fetch(`/gallery/${galleryId}/designs`);
  const designs = await res.json();

  designs.forEach(d => {
  grid.innerHTML += `
    <div class="bg-gray-800 rounded overflow-hidden relative">

      <img src="${d.image}" class="w-full h-48 object-cover">

      <div class="p-3">
        <div class="font-semibold">${d.name}</div>

        ${
        d.laser_settings && document.body.dataset.isAdmin === "true"
            ? `
            <div class="text-xs text-gray-400 mt-2 space-y-1">
                <div><strong>Font:</strong> ${d.laser_settings.font || "—"}</div>
                <div><strong>Power:</strong> ${d.laser_settings.power}%</div>
                <div><strong>Laser Time:</strong> ${d.laser_settings.laser_time} min</div>

                ${
                d.laser_settings.speed !== null
                    ? `<div><strong>Speed:</strong> ${d.laser_settings.speed} mm/s</div>`
                    : ""
                }
                ${
                d.laser_settings.depth !== null
                    ? `<div><strong>Depth:</strong> ${d.laser_settings.depth}%</div>`
                    : ""
                }
                <div><strong>Passes:</strong> ${d.laser_settings.passes}</div>
            </div>

            <div class="flex gap-2 mt-3">
                <button
                class="edit-design-btn bg-blue-600 hover:bg-blue-500 text-xs px-2 py-1 rounded"
                data-design='${JSON.stringify(d)}'>
                Edit
                </button>

                <button
                class="delete-design-btn bg-red-600 hover:bg-red-500 text-xs px-2 py-1 rounded"
                data-id="${d.id}">
                Delete
                </button>
            </div>
            `
            : ""
        }

      </div>
    </div>
  `;
});
}

function closeDesignCollection() {
  document.getElementById("designCollectionModal").classList.add("hidden");
}

/* ================= ADD DESIGN ================= */
function closeAddDesignModal() {
  const modal = document.getElementById("addDesignModal");
  modal.classList.add("hidden");

  const preview = document.getElementById("designPreview");
  if (preview) preview.classList.add("hidden");

  document.getElementById("addDesignForm")?.reset();
}

function previewDesignImage(e) {
  const img = document.getElementById("designPreview");
  const file = e.target.files[0];

  if (!file) {
    img.classList.add("hidden");
    return;
  }

  img.src = URL.createObjectURL(file);
  img.classList.remove("hidden");
}

function closeEditDesignModal() {
  const modal = document.getElementById("editDesignModal");
  if (!modal) return;

  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

/* ================= DOM READY ================= */
document.addEventListener("DOMContentLoaded", () => {

  /* Sync collapse state */
  document.querySelectorAll(".gallery-section").forEach(section => {
    section.style.maxHeight = section.scrollHeight + "px";
    section.style.opacity = "1";
  });

  /* Edit gallery buttons */
  document.querySelectorAll(".edit-gallery-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      e.stopPropagation();
      openEditGallery(
        btn.dataset.id,
        btn.dataset.name,
        btn.dataset.category,
        btn.dataset.price ? parseFloat(btn.dataset.price) : null,
        parseInt(btn.dataset.showPrice)
      );
    });
  });

  /* Gallery card click */
  document.querySelectorAll(".gallery-item").forEach(item => {
    item.addEventListener("click", e => {
      if (e.target.closest("button")) return;
      openDesignCollection(item.dataset.id, item.dataset.name);
    });
  });

  /* Add design button */
  const addDesignBtn = document.getElementById("addDesignBtn");
  if (addDesignBtn) {
    addDesignBtn.addEventListener("click", () => {
      if (!currentGalleryId) return;

      document.getElementById("designGalleryId").value = currentGalleryId;
      document.getElementById("addDesignModal").classList.remove("hidden");
      document.getElementById("addDesignModal").classList.add("flex");
      
    });
  }

  /* Add design submit */
  document.getElementById("addDesignForm")?.addEventListener("submit", async e => {
    e.preventDefault();

    const form = e.target;
    const data = new FormData(form);

    const res = await fetch("/gallery/design/add", {
      method: "POST",
      body: data
    });

    const result = await res.json();

    if (result.status === "success") {
      Swal.fire("Added", "Design added", "success");
      closeAddDesignModal();
      openDesignCollection(
        currentGalleryId,
        document.getElementById("designTitle")
          .textContent.replace(" – Designs", "")
      );
    } else {
      Swal.fire("Error", result.message || "Upload failed", "error");
    }
  });

document.addEventListener("click", e => {
  const btn = e.target.closest(".edit-design-btn");
  if (!btn) return;

  const d = JSON.parse(btn.dataset.design);

  const modal = document.getElementById("editDesignModal");
  modal.classList.remove("hidden");
  modal.classList.add("flex");

  const form = document.getElementById("editDesignForm");
  form.id.value = d.id;
  form.name.value = d.name;
  form.font.value = d.laser_settings.font || "";
  form.power.value = d.laser_settings.power;
  form.speed.value = d.laser_settings.speed ?? "";
  form.depth.value = d.laser_settings.depth ?? "";
  form.passes.value = d.laser_settings.passes;
  form.laser_time.value = d.laser_settings.laser_time;
  document.getElementById("edit_is_featured").checked = d.is_featured === 1;

});


document.getElementById("editDesignForm")?.addEventListener("submit", async e => {
  e.preventDefault();

  const form = e.target;
  const data = new FormData(form);
  data.set("is_featured",
  document.getElementById("edit_is_featured").checked ? 1 : 0
  );


  const res = await fetch("/gallery/design/edit", {
    method: "POST",
    body: data
  });

  const result = await res.json();

  if (result.status === "success") {
    Swal.fire("Updated", "Design updated", "success");
    closeEditDesignModal();
    openDesignCollection(
      currentGalleryId,
      document.getElementById("designTitle")
        .textContent.replace(" – Designs", "")
    );
  } else {
    Swal.fire("Error", "Update failed", "error");
  }
});

document.addEventListener("click", async e => {
  const btn = e.target.closest(".delete-design-btn");
  if (!btn) return;

  e.stopPropagation();

  const id = btn.dataset.id;

  const confirm = await Swal.fire({
    title: "Delete this design?",
    text: "This cannot be undone.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Delete"
  });

  if (!confirm.isConfirmed) return;

  const res = await fetch(`/gallery/design/delete/${id}`, {
    method: "POST"
  });

  const result = await res.json();

  if (result.status === "deleted") {
    Swal.fire("Deleted", "", "success");

    // Refresh designs
    openDesignCollection(
      currentGalleryId,
      document.getElementById("designTitle")
        .textContent.replace(" – Designs", "")
    );
  } else {
    Swal.fire("Error", "Delete failed", "error");
  }
});


});
