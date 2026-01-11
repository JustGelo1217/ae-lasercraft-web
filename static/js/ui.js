"use strict";

/* =====================
   DEFAULT SETTINGS
===================== */
const DEFAULT_SETTINGS = {
  theme: "dark",
  accentColor: "#3b82f6",

  compactMode: false,
  enableAnimations: true,

  confirmCheckout: true,
  requireCash: false,
  autoPrintReceipt: false,
  receiptTemplate: "compact",

  preventNegativeStock: true,
  lowStockLevel: 5,

  requireLaserSettings: true,
  showLaserSettingsToStaff: false,

  maintenanceMode: false
};


/* =====================
   SETTINGS STATE
===================== */
let userSettings = {};

/* =====================
   LOAD SETTINGS
===================== */
async function loadUserSettings() {
  try {
    const res = await fetch("/api/settings");
    const saved = res.ok ? await res.json() : {};
    userSettings = { ...DEFAULT_SETTINGS, ...saved };
  } catch {
    userSettings = { ...DEFAULT_SETTINGS };
  }

  applySettings(userSettings);
  syncSettingsUI();
  localStorage.setItem("userSettings", JSON.stringify(userSettings));
}

/* =====================
   SAVE SETTINGS
===================== */
async function saveUserSettings() {
  localStorage.setItem("userSettings", JSON.stringify(userSettings));

  await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(userSettings)
  });
}

/* =====================
   TOGGLE SETTING
===================== */
function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");

    sidebar.classList.toggle("closed");

    if (overlay) {
        overlay.classList.toggle("hidden");
    }
}


/* =====================
   TOGGLE SIDEBAR
===================== */
function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    sidebar.classList.toggle("closed");
}



/* =====================
   RESET SETTINGS
===================== */
function resetUISettings() {
  userSettings = { ...DEFAULT_SETTINGS };
  applySettings(userSettings);
  syncSettingsUI();
  saveUserSettings();
  showToast("Settings reset to defaults");
}

/* =====================
   APPLY SETTINGS
===================== */
function applySettings(settings) {

  /* compact mode */
  document.body.classList.toggle("compact", settings.compactMode === true);

  /* theme (use existing CSS system) */
  if (settings.theme === "light") {
    document.body.classList.add("light");
  } else {
    document.body.classList.remove("light");
  }

  /* accent color (use existing CSS variable) */
  document.documentElement.style.setProperty(
    "--accent",
    settings.accentColor || "#22c55e"
  );

  window.APP_SETTINGS = settings;
}




/* =====================
   SYNC SETTINGS UI
===================== */
function syncSettingsUI() {
  document.querySelectorAll("[data-setting]").forEach(el => {
    const key = el.dataset.setting;
    if (el.type === "checkbox") {
      el.checked = userSettings[key] === true;
    } else {
      el.value = userSettings[key] ?? "";
    }
  });

  document.querySelectorAll(".accent-choice").forEach(btn => {
  if (btn.getAttribute("onclick")?.includes(userSettings.accentColor)) {
    btn.classList.add("accent-ring");
  } else {
    btn.classList.remove("accent-ring");
  }
  });


}

/* =====================
   MAINTENANCE MODE
===================== */
function enforceFeatureFlags() {
  const isAdmin = document.body.dataset.isAdmin === "true";

  if (userSettings.maintenanceMode && !isAdmin) {
    document.body.innerHTML = `
      <div class="min-h-screen flex items-center justify-center text-center">
        <div>
          <h1 class="text-3xl font-bold text-red-500">Maintenance Mode</h1>
          <p class="mt-4 text-gray-400">System is temporarily unavailable.</p>
        </div>
      </div>
    `;
  }
}

/* =====================
   TOAST
===================== */
function showToast(msg) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 2500);
}

function setTheme(theme) {
  toggleSetting("theme", theme);
}

function setAccent(color, el = null) {
  toggleSetting("accentColor", color);

  document.querySelectorAll(".accent-choice").forEach(btn => {
    btn.classList.remove("accent-ring");
  });

  if (el) {
    el.classList.add("accent-ring");
  }
}



/* =====================
   INIT
===================== */
document.addEventListener("DOMContentLoaded", () => {
  loadUserSettings().then(enforceFeatureFlags);

  document.addEventListener("click", function(e) {
    const sidebar = document.getElementById("sidebar");
    const btn = document.getElementById("menu-btn");

    if (!sidebar.contains(e.target) && !btn.contains(e.target)) {
    sidebar.classList.add("closed");
    document.getElementById("overlay")?.classList.add("hidden");
    }

});

});

