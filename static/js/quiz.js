const steps = [
  { key: "style", title: "Choose a design style", options: ["cute", "luxury", "vintage"] },

  { key: "mood", title: "Select the mood", options: ["romantic", "fun", "professional", "bold", "calm"] },

  {
    key: "category",
    title: "What will this product be used for?",
    options: ["birthday", "wedding", "giveaway", "anniversary", "business", "personal"]
  },

  {
    key: "font",
    title: "Choose a font style",
    options: ["script", "sans", "serif", "handwritten"],
    isFont: true
  },

  {
    key: "product",
    title: "Product type",
    options: [],
    isDynamic: true
  }
];


let currentStep = 0;
const answers = {};
let selectedValue = null;

let container, progressBar;

document.addEventListener("DOMContentLoaded", async () => {
  container = document.getElementById("quizContainer");
  progressBar = document.getElementById("progressBar");
  if (!container || !progressBar) return;

  await loadProducts();   // 👈 ADD THIS
  renderStep();
});


async function loadProducts() {
  const res = await fetch("/api/materials");
  const data = await res.json();

  const productStep = steps.find(s => s.key === "product");

  productStep.options = data.map(item => item.name.toLowerCase());
}


function renderStep() {
   const step = steps[currentStep];
   selectedValue = null;

  if (step.isDynamic && step.options.length === 0) {
    container.innerHTML = `<div class="text-center py-10">Loading products...</div>`;
    return;
  }
  const progress = (currentStep / steps.length) * 100;
  progressBar.style.width = progress + "%";

  let optionsHtml = "";

  if (step.isFont) {
    optionsHtml = `
      <div class="mb-4 p-4 border border-gray-700 rounded bg-gray-900 text-center">
        <div class="text-gray-400 text-sm mb-2">Preview</div>
        <div id="fontPreview" class="text-2xl">AE LaserCraft</div>
      </div>

      <div class="grid grid-cols-2 gap-3 mb-4">
        ${step.options.map(opt => `
          <button onclick="selectFont('${opt}', this)"
            class="option-btn border border-gray-700 rounded p-3 hover:border-emerald-500 transition capitalize">
            ${opt}
          </button>
        `).join("")}
      </div>
    `;
  } else {
    optionsHtml = `
      <div class="grid grid-cols-2 gap-3 mb-4">
        ${step.options.map(opt => `
          <button onclick="selectOption('${opt}', this)"
            class="option-btn border border-gray-700 rounded p-3 hover:border-emerald-500 transition capitalize">
            ${opt}
          </button>
        `).join("")}
      </div>
    `;
  }

  container.innerHTML = `
    <h2 class="text-lg font-semibold mb-4 text-center">${step.title}</h2>
    ${optionsHtml}

    <button id="nextBtn"
      onclick="nextStep()"
      disabled
      class="w-full bg-emerald-500 text-black font-semibold py-3 rounded-lg opacity-50 cursor-not-allowed">
      Next
    </button>
  `;
}

function clearSelections() {
  document.querySelectorAll(".option-btn").forEach(btn => {
    btn.classList.remove("border-emerald-500", "bg-emerald-500/10");
    btn.classList.add("border-gray-700");
  });
}

function enableNext() {
  const btn = document.getElementById("nextBtn");
  btn.disabled = false;
  btn.classList.remove("opacity-50", "cursor-not-allowed");
}

function selectOption(value, el) {
  clearSelections();
  selectedValue = value;
  el.classList.add("border-emerald-500", "bg-emerald-500/10");
  enableNext();
}

function selectFont(value, el) {
  clearSelections();
  selectedValue = value;
  el.classList.add("border-emerald-500", "bg-emerald-500/10");

  const preview = document.getElementById("fontPreview");
  if (preview) preview.className = "text-2xl " + fontClass(value);

  enableNext();
}

function fontClass(font) {
  switch (font) {
    case "script": return "font-script";
    case "sans": return "font-sans";
    case "serif": return "font-serif";
    case "handwritten": return "font-hand";
    default: return "";
  }
}

function nextStep() {
  if (!selectedValue) return;

  const stepKey = steps[currentStep].key;
  answers[stepKey] = selectedValue;

  currentStep++;

  if (currentStep < steps.length) {
    renderStep();
  } else {
    progressBar.style.width = "100%";
    submitQuiz();
  }
}

async function submitQuiz() {
  container.innerHTML = `
    <div class="text-center py-10">
      <div class="text-lg font-semibold mb-2">Finding your designs...</div>
      <div class="text-gray-400">Please wait</div>
    </div>
  `;

  const res = await fetch("/api/design-quiz/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(answers)
  });

  const result = await res.json();
  window.location = `/design-quiz/results/${result.session_id}`;
}
